"""Candidate generation, ranking and wave selection (spec 02 module M, 04 §6.4)."""
import math
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.catalog.models import CatalogState
from apps.catalog.services import TAXONOMY
from apps.queries.discovery import discover_or_seed_nearby_candidates, haversine_km
from apps.queries.models import AvailabilityRecord, QueryTarget

WEIGHTS = {"match": 0.34, "proximity": 0.25, "freshness": 0.16, "accuracy": 0.15, "plan": 0.10}
PLAN_BOOST = {"free": 0.03, "grow": 0.06, "featured": 0.09, "scale": 0.09}
COST_PER_LIVE_CHECK_PAISE = 220  # approximate from docs 03 §13 (validation task in 08 §5)


def now():
    return timezone.now()


def _fresh_rows(query):
    earliest = now() - timedelta(hours=settings.FRESH_CATALOG_HOURS)
    rows = (
        CatalogState.objects
        .select_related("shop", "shop__city")
        .filter(superseded_at__isnull=True, created_at__gte=earliest,
                state__in=["in", "partial"],
                shop__city=query.city, shop__claimed_at__isnull=False,
        )
        .order_by("-created_at")[:400]
    )
    verticals_intent = {TAXONOMY[c]["vertical"] for c in (query.parsed_intent or {}).get("item_codes", []) if c in TAXONOMY}
    if verticals_intent:
        rows = [r for r in rows if r.shop.verticals and set(r.shop.verticals) & verticals_intent]
    return list(rows)


def _match_factor(catalog, intent):
    f = 0.5
    color, size, price_max = intent.get("color"), intent.get("size"), intent.get("price_max")
    if color:
        colors = [c.lower() for c in (catalog.color_notes or [])]
        f += 0.2 if color.lower() in colors else -0.05
    if size:
        sm = catalog.size_matrix or {}
        if sm:
            f += 0.2 if sm.get(size) else -0.15
    if price_max and catalog.price_band.get("max"):
        f += 0.1 if float(catalog.price_band["max"]) <= price_max else -0.1
    return max(0.05, f)


def _score(catalog, match_factor, distance_km, radius_m, shop):
    proximity = max(0.0, 1.0 - distance_km * 1000 / max(radius_m, 1))
    age_h = (now() - catalog.created_at).total_seconds() / 3600
    freshness = max(0.0, 1.0 - age_h / settings.FRESH_CATALOG_HOURS)
    accuracy = float(shop.accuracy_score or 0)
    plan = PLAN_BOOST.get(shop.current_plan, 0.03)
    return round(WEIGHTS["match"] * match_factor + WEIGHTS["proximity"] * proximity
                 + WEIGHTS["freshness"] * freshness + WEIGHTS["accuracy"] * accuracy
                 + WEIGHTS["plan"] * plan, 4)


def _within_radius(query, shop, center) -> float | None:
    """Returns distance km if shop is inside query radius, else None."""
    if not (shop.lat and shop.lng):
        return None
    d = haversine_km(*center, float(shop.lat), float(shop.lng))
    return d if d * 1000 <= query.radius_m else None


def _instant_record(query, intent, row):
    rec = AvailabilityRecord.objects.create(
        shop=row.shop, query=query,
        item_intent={"item_codes": intent.get("item_codes"), "color": intent.get("color"),
                     "size": intent.get("size")},
        state="SHOP_REPORTED_IN_STOCK",
        sizes=[s for s, ok in (row.size_matrix or {}).items() if ok][:10] or [],
        colors=row.color_notes or [],
        price_text=(f"₹{row.price_band['min']}–{row.price_band['max']}"
                    if row.price_band.get("min") is not None else ""),
        evidence_kind="catalog",
        transcript_snippet=f"Shop catalog: {row.label} in stock",
        freshness_at=row.created_at,
        publish_state="published",
    )
    return rec


def _live_target(query, intent, row, center):
    shop = row.shop
    d = _within_radius(query, shop, center) if (shop.lat and shop.lng) else 0.0
    if d is None:
        return None
    mf = _match_factor(row, intent)
    t = QueryTarget.objects.create(
        query=query, shop=shop, match_score=_score(row, mf, d or 0, query.radius_m, shop),
        contact_decision={"catalog_state": row.state, "size_matrix": row.size_matrix,
                          "distance_km": round(d, 3) if d is not None else None},
    )
    return t


def build_targets(query) -> dict:
    """Creates QueryTarget rows + instant records per docs 02 F-M-01/02.
    Combines instant catalog hits with nearby candidate discovery for Products and Services."""
    intent = query.parsed_intent or {}
    center = (float(query.lat), float(query.lng)) if query.lat and query.lng else (
        float(query.city.center_lat), float(query.city.center_lng))
    rows = _fresh_rows(query)

    instant_ids, kept_targets = [], []
    seen_shop_ids: set[int] = set()
    for row in rows:
        shop = row.shop
        if shop.id in seen_shop_ids:
            continue
        if (shop.lat and shop.lng) and _within_radius(query, shop, center) is None:
            continue
        size = intent.get("size")
        state_ok = row.state == "in" and (not size or (row.size_matrix or {}).get(size, True))
        if state_ok:
            rec = _instant_record(query, intent, row)
            instant_ids.append(rec.id)
        else:
            t = _live_target(query, intent, row, center)
            if t is not None:
                kept_targets.append(t)
        seen_shop_ids.add(shop.id)

    # Nearby place discovery engine for candidates with contact numbers (Products & Services)
    # Only discover/seed if we have fewer than 2 candidates from catalog/DB
    nearby_candidates = discover_or_seed_nearby_candidates(
        center_lat=center[0],
        center_lng=center[1],
        radius_m=query.radius_m,
        intent=intent,
        city=query.city,
        min_count=2 if (len(instant_ids) + len(kept_targets)) >= 2 else 3,
    )
    for cand in nearby_candidates:
        cand_shop = cand["shop"]
        if cand_shop.id in seen_shop_ids:
            continue
        # Unclaimed shops in demo are ignored unless opted or placed
        if cand_shop.claimed_at is None and cand_shop.source != "place_seed":
            continue

        dist_km = cand["distance_km"]
        proximity = max(0.0, 1.0 - (dist_km * 1000 / max(query.radius_m, 1)))
        cap_score = cand["capability_score"]
        accuracy = float(cand_shop.accuracy_score or Decimal("0.90"))
        plan = PLAN_BOOST.get(cand_shop.current_plan, 0.03)
        score = round(
            WEIGHTS["match"] * cap_score
            + WEIGHTS["proximity"] * proximity
            + WEIGHTS["freshness"] * 0.8
            + WEIGHTS["accuracy"] * accuracy
            + WEIGHTS["plan"] * plan,
            4,
        )

        t = QueryTarget.objects.create(
            query=query,
            shop=cand_shop,
            match_score=score,
            contact_decision={
                "distance_km": dist_km,
                "capability_score": cap_score,
                "contact_number": cand["contact_number"],
                "source": cand_shop.source,
                "channels": getattr(cand_shop, "contact_policy", None).channels if getattr(cand_shop, "contact_policy", None) else ["call"],
            },
        )
        kept_targets.append(t)
        seen_shop_ids.add(cand_shop.id)

    if len(instant_ids) >= 5 and not query.spot_check:
        return {"instant": instant_ids, "wave": [], "held_for_spot_check": True}

    kept_targets.sort(key=lambda t: -float(t.match_score))
    budget_left_paise = max(0, query.budget_paise)
    wave = []
    for t in kept_targets:
        if len(wave) >= settings.MAX_TARGETS_PER_WAVE:
            t.state, t.outcome, t.reason_code = "resolved", "UNREACHABLE", "wave_cap"
            t.save()
            continue
        if budget_left_paise < COST_PER_LIVE_CHECK_PAISE:
            t.state, t.outcome, t.reason_code = "resolved", "UNREACHABLE", "budget_exceeded"
            t.save()
            continue
        t.rank_final = len(wave) + 1
        t.save(update_fields=["rank_final"])
        wave.append(t.id)
        budget_left_paise -= COST_PER_LIVE_CHECK_PAISE

    return {"instant": instant_ids, "wave": wave, "held_for_spot_check": False}


def build_extra_targets(query, limit: int | None = None) -> list[int]:
    """'Check a few more' (F-C-03): next-ranked targets not yet attempted."""
    limit = limit or settings.SPOT_CHECK_EXTRA
    existing_shop_ids = set(QueryTarget.objects.filter(query=query).values_list("shop_id", flat=True))
    used_budget = (QueryTarget.objects.filter(query=query)
                   .exclude(state__in=["queued"]).count()) * COST_PER_LIVE_CHECK_PAISE
    if used_budget >= query.budget_paise:
        return []
    intent = query.parsed_intent or {}
    center = (float(query.lat), float(query.lng)) if query.lat and query.lng else (
        float(query.city.center_lat), float(query.city.center_lng))
    created = []
    for row in _fresh_rows(query):
        if len(created) >= limit or (query.budget_paise - used_budget) < COST_PER_LIVE_CHECK_PAISE * (len(created) + 1):
            break
        if row.shop.id in existing_shop_ids or row.shop.is_claimed is False:
            continue
        t = _live_target(query, intent, row, center)
        if t is not None:
            created.append(t.id)
    return created

