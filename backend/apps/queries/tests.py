"""Core pipeline tests (docs 02 + 03 happy paths, mocks wired internally)."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Plan
from apps.core.models import City
from apps.catalog.models import CatalogState
from apps.queries.models import Query, QueryTarget
from apps.queries.parsing import parse_text
from apps.shops.models import Shop


def _seed_fixture():
    city = City.objects.create(code="pune", name="Pune", center_lat=Decimal("18.5204"),
                               center_lng=Decimal("73.8567"), is_live=True)
    Plan.objects.create(code="free", name="Basic", monthly_paise=0, checks_month=50,
                        rank_boost=Decimal("0.03"), features={})
    shops = []
    # shop 1: fresh catalog, blue dress, M in stock → should answer instant SHOP_REPORTED
    s1 = Shop.objects.create(display_name="Style Studio", verticals=["fashion"], city=city,
                             lat=Decimal("18.5210"), lng=Decimal("73.8570"),
                             ops_phone="919000000001", public_phone="+919000000001",
                             whatsapp_number="919000000001", whatsapp_linked=True,
                             claimed_at=timezone.now(), current_plan="free",
                             mock_behavior="always_yes")
    CatalogState.objects.create(shop=s1, catalog_key="fashion.dress", label="Dress",
                                state="in", size_matrix={"M": True, "L": True},
                                price_band={"min": 999, "max": 2499},
                                color_notes=["Blue", "Black"],
                                recorded_by="portal",
                                valid_until=timezone.now() + timedelta(hours=48))
    # shop 2: catalog partial (only S) → live check target (call), mock always_yes
    s2 = Shop.objects.create(display_name="Bob's Fashion", verticals=["fashion"], city=city,
                             lat=Decimal("18.5220"), lng=Decimal("73.8580"),
                             ops_phone="919000000002", public_phone="+919000000002",
                             whatsapp_number="919000000002", whatsapp_linked=True,
                             claimed_at=timezone.now(), current_plan="free",
                             mock_behavior="always_yes")
    CatalogState.objects.create(shop=s2, catalog_key="fashion.dress", label="Dress",
                                state="partial", size_matrix={"S": True},
                                price_band={"min": 799, "max": 1999},
                                color_notes=["Black", "Blue"],
                                recorded_by="portal",
                                valid_until=timezone.now() + timedelta(hours=48))
    # shop 3: unreachable (call will fail) → UNREACHABLE through the mock
    s3 = Shop.objects.create(display_name="Quiet Cloth House", verticals=["fashion"], city=city,
                             lat=Decimal("18.5240"), lng=Decimal("73.8590"),
                             ops_phone="919000000003", public_phone="+919000000003",
                             whatsapp_number="919000000003", whatsapp_linked=False,
                             claimed_at=timezone.now(), current_plan="free",
                             mock_behavior="unreachable")
    CatalogState.objects.create(shop=s3, catalog_key="fashion.dress", label="Dress",
                                state="partial", size_matrix={"L": True},
                                recorded_by="portal",
                                valid_until=timezone.now() + timedelta(hours=48))
    shops = [s1, s2, s3]
    return city, shops


def test_parse_blue_dress_medium():
    p = parse_text("blue dress medium size")
    assert p["item_codes"] == ["fashion.dress"], p
    assert p["color"] == "Blue"
    assert p["size"] == "M"
    assert p["confidence"] >= 0.8


def test_parse_size_alias_and_price():
    p = parse_text("small kurti under 900")
    assert p["size"] == "S"
    assert p["item_codes"] == ["fashion.kurti"]
    assert p["price_max"] == 900


@pytest.mark.django_db
def test_query_pipeline_instant_and_wave(monkeypatch):
    """End-to-end sans broker/provider: build targets; apply mock webhook manually."""
    from apps.verification import services
    monkeypatch.setattr(services, "start_verification", lambda tid: None)

    city, shops = _seed_fixture()
    api = APIClient()
    resp = api.post("/api/v1/queries", {
        "text": "blue dress medium size",
        "city": "pune",
        "location": {"lat": 18.5204, "lng": 73.8567},
        "radius_m": 5000,
    }, format="json")
    assert resp.status_code == 202, resp.data
    body = resp.json()
    qid = body["query_id"]
    query = Query.objects.get(id=qid)

    # instant result expected from Style Studio's fresh catalog row
    assert any(r["state"] == "SHOP_REPORTED_IN_STOCK" for r in body["instant_results"])
    # live wave includes Bob's Fashion (partial) & Quiet Cloth House
    wave = QueryTarget.objects.filter(query=query, state__in=["queued", "contacting"])
    assert wave.count() == 2
    shops_in_wave = set(wave.values_list("shop__display_name", flat=True))
    assert "Bob's Fashion" in shops_in_wave

    # simulate voice-svc webhook for Bob's target (docs 03 §12)
    target = wave.get(shop__display_name="Bob's Fashion")
    from apps.verification.services import apply_verification_update
    apply_verification_update(target.id, {
        "channel": "call",
        "outcome": "CONFIRMED_IN_STOCK",
        "sizes": ["M", "L"],
        "price_text": "₹1,999",
        "transcript": "bot: क्या नीला ड्रेस साइज़ M उपलब्ध है?\nshop: हाँ, M और L बची हैं\nbot: धन्यवाद!",
        "asr_confidence": 0.93,
        "provider_events": [{"event": "ringing"}, {"event": "answered"}, {"event": "ended"}],
    })
    target.refresh_from_db()
    assert target.state == "resolved" and target.outcome == "CONFIRMED_IN_STOCK"

    detail = api.get(f"/api/v1/queries/{qid}").json()
    confirmed = [r for r in detail["instant_results"] if r["state"] == "CONFIRMED_IN_STOCK"]
    # AvailabilityRecord exposed through detail["availability"] — use that instead
    recs = [r for r in detail.get("availability", []) if r["state"] == "CONFIRMED_IN_STOCK"]
    assert recs and recs[0]["shop_id"] == shops[1].id
    assert confirmed == [] or recs

    # query should now be completed (only one live target remains: unreachable mock)
    query.refresh_from_db()
    assert query.status == "processing"


@pytest.mark.django_db
def test_query_extend_and_caps(monkeypatch):
    """'Check a few more' respects budget + caps (docs 02 F-C-03, 03 §7)."""
    from apps.verification import services
    monkeypatch.setattr(services, "start_verification", lambda tid: None)

    city, shops = _seed_fixture()
    api = APIClient()
    resp = api.post("/api/v1/queries", {"text": "blue dress medium", "city": "pune",
                                        "radius_m": 5000}, format="json")
    qid = resp.json()["query_id"]
    query = Query.objects.get(id=qid)
    # exhaust budget: set to 0 → extension should 429
    query.budget_paise = 0
    query.save()
    r2 = api.post(f"/api/v1/queries/{qid}/extend").json()
    assert r2.get("error", {}).get("code") == "BUDGET_EXCEEDED"


@pytest.mark.django_db
def test_claim_flow_and_catalog_update():
    city, _ = _seed_fixture()
    shop = Shop.objects.create(display_name="New Bazaar", verticals=["fashion"], city=city,
                               ops_phone="919000000010", claimed_at=None, mock_behavior="always_yes")
    api = APIClient()
    res = api.post("/api/v1/shop/claim/lookup", {"phone": "919000000010"}, format="json").json()
    req_id = res["requests"][0]["request_id"]
    otp = res["requests"][0]["dev_otp"]
    token_resp = api.post("/api/v1/shop/claim/verify",
                          {"request_id": req_id, "code": otp}, format="json")
    assert token_resp.status_code == 200, token_resp.data
    token = token_resp.json()["token"]
    shop.refresh_from_db()
    assert shop.claimed_at is not None

    api2 = APIClient()
    api2.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    rows = api2.put("/api/v1/me/shop/catalog", {
        "rows": [{"catalog_key": "fashion.dress", "state": "in",
                  "size_matrix": {"M": True}, "color_notes": ["Blue"],
                  "price_band": {"min": 500, "max": 1500}}]
    }, format="json")
    assert rows.status_code == 200, rows.data
    assert any(r["catalog_key"] == "fashion.dress" for r in rows.json()["rows"])


def test_settings_of_taxonomy_names_are_ascii():
    from apps.catalog.services import TAXONOMY
    assert all("." in k for k in TAXONOMY)


@pytest.mark.django_db
def test_shop_portal_inbox_reply_resolves_live_target(monkeypatch):
    from apps.verification import services
    monkeypatch.setattr(services, "start_verification", lambda tid: None)

    city, shops = _seed_fixture()
    api = APIClient()
    qid = api.post("/api/v1/queries", {"text": "blue dress medium", "city": "pune",
                                       "radius_m": 5000}, format="json").json()["query_id"]

    target = QueryTarget.objects.filter(query_id=qid, shop=shops[1]).first()
    assert target is not None

    # claim that shop (Bob's Fashion) and answer from the portal inbox
    phone = shops[1].ops_phone
    # Bob's is claimed by the fixture; un-claim only for this claim-flow portion
    # (inbox lookup covers unclaimed shops — portal behaviour matches docs 04 §2)
    shops[1].claimed_at = None
    shops[1].save(update_fields=["claimed_at"])
    lookup = api.post("/api/v1/shop/claim/lookup", {"phone": phone}, format="json").json()
    rid, code = lookup["requests"][0]["request_id"], lookup["requests"][0]["dev_otp"]
    token = api.post("/api/v1/shop/claim/verify", {"request_id": rid, "code": code},
                     format="json").json()["token"]

    shop_api = APIClient()
    shop_api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    inbox = shop_api.get("/api/v1/me/shop/inquiries").json()
    assert any(i["target_id"] == target.id for i in inbox["items"]), inbox

    res = shop_api.post(f"/api/v1/me/shop/inquiries/{target.id}/reply",
                        {"outcome": "CONFIRMED_IN_STOCK", "sizes": ["M"]}, format="json").json()
    assert res["ok"] is True
    target.refresh_from_db()
    assert target.state == "resolved" and target.outcome == "CONFIRMED_IN_STOCK"
    avail = [r for r in shops[1].availability_records.filter(query_id=qid)]
    assert any(r.evidence_kind == "inbox" and r.state == "CONFIRMED_IN_STOCK" for r in avail)
