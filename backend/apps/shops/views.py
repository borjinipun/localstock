import csv
import io
import random
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.catalog.services import TAXONOMY
from apps.catalog.models import CatalogState, TimeHelper
from apps.queries.models import AvailabilityRecord, QueryTarget
from apps.verification.services import apply_catalog_reply  # inbox-based resolution

from .auth import get_shop, issue_shop_token
from .models import ClaimRequest, ContactPolicy, Shop
from .serializers import (
    CatalogRowSerializer,
    ClaimLookupSerializer,
    ClaimVerifySerializer,
    ContactPolicySerializer,
    InboxTargetSerializer,
    ShopPublicSerializer,
)


# ------------------------- public (docs 07 API-6) -------------------------

@api_view(["GET"])
def shop_detail(request, pk):
    try:
        shop = Shop.objects.select_related("city", "contact_policy").get(pk=pk)
    except Shop.DoesNotExist:
        return Response({"error": {"code": "NOT_FOUND", "message": "Shop not found"}}, status=404)
    return Response(ShopPublicSerializer(shop).data)


@api_view(["GET"])
def shop_availability_history(request, pk):
    """Recent public availability trail (freshness-limited per docs 05 §7)."""
    recs = AvailabilityRecord.objects.filter(
        shop_id=pk, publish_state="published",
        item_intent__isnull=False,
    ).exclude(state="STALE")[:20]
    from apps.queries.serializers import AvailabilityRecordSerializer
    return Response({"items": AvailabilityRecordSerializer(recs, many=True).data})


# ------------------------- claim flow (docs 04 §2) -------------------------

@api_view(["POST"])
def claim_lookup(request):
    """POST /shop/claim/lookup {phone}. OTP is delivered by voice-svc/WA/SMS adapters;
    in mock/dev mode it is returned as dev_otp (docs 10 OQ note)."""
    phone = (request.data or {}).get("phone", "").strip()
    if not phone:
        return Response({"error": {"code": "VALIDATION_ERROR", "message": "phone required"}}, status=400)
    shops = Shop.objects.filter(ops_phone=phone, claimed_at__isnull=True)[:5]
    if not shops.exists():
        return Response({"error": {"code": "NOT_FOUND", "message": "No unclaimed shops for this phone"}}, status=404)
    out = []
    for shop in shops:
        cr = ClaimRequest.objects.create(
            shop=shop, applicant_phone=phone,
            otp_code=f"{random.randint(100000, 999999)}",
        )
        out.append(ClaimLookupSerializer({
            "request_id": cr.id, "shop_id": shop.id, "shop_name": shop.display_name,
            "dev_otp": cr.otp_code,
        }).data)
    return Response({"requests": out})


@api_view(["POST"])
def claim_verify(request):
    data = ClaimVerifySerializer(data=request.data)
    if not data.is_valid():
        return Response(data.errors, status=400)
    try:
        cr = ClaimRequest.objects.select_related("shop").get(id=data.validated_data["request_id"])
    except ClaimRequest.DoesNotExist:
        return Response({"error": {"code": "NOT_FOUND", "message": "Claim request not found"}}, status=404)
    if not cr.otp_verified:
        if cr.otp_code != data.validated_data["code"]:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Wrong OTP"}}, status=400)
        cr.otp_verified, cr.status = True, "approved"
        cr.save()
        shop = cr.shop
        shop.claimed_at = timezone.now()
        shop.source = "self_claim"
        shop.save(update_fields=["claimed_at", "source"])
        ContactPolicy.objects.get_or_create(shop=shop)
    return Response({"token": issue_shop_token(cr.shop_id), "shop_id": cr.shop_id,
                     "shop_name": cr.shop.display_name})


# ------------------------- bought-portal endpoints (scope shop:<id>) ----------

@api_view(["GET", "PUT"])
def me_shop(request):
    shop = get_shop(request)
    if not shop:
        return Response({"error": {"code": "FORBIDDEN_SCOPE", "message": "shop token required"}}, status=401)
    if request.method == "PUT":
        pol, _ = ContactPolicy.objects.get_or_create(shop=shop)
        poldata = ContactPolicySerializer(pol, data=request.data, partial=True)
        if poldata.is_valid():
            poldata.save()
        else:
            return Response(poldata.errors, status=400)
    return Response({
        "shop": ShopPublicSerializer(shop).data,
        "contact_policy": ContactPolicySerializer(shop.contact_policy).data,
    })


@api_view(["GET", "PUT"])
def shop_catalog(request):
    shop = get_shop(request)
    if not shop:
        return Response({"error": {"code": "FORBIDDEN_SCOPE", "message": "shop token required"}}, status=401)
    latest = CatalogState.objects.filter(shop=shop, superseded_at__isnull=True).order_by("catalog_key")
    if request.method == "PUT":
        payload = request.data.get("rows", [])
        for row in payload:
            key = row.get("catalog_key")
            if key not in TAXONOMY:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": f"Unknown catalog key {key}"}},
                                status=400)
            # Spec 06 §2.1: versioned rows — supersede previous rather than mutate.
            CatalogState.objects.filter(shop=shop, catalog_key=key, superseded_at__isnull=True)\
                .update(superseded_at=TimeHelper.now())
            CatalogState.objects.create(
                shop=shop, catalog_key=key, label=TAXONOMY[key]["label"],
                state=row.get("state", "in"),
                size_matrix=row.get("size_matrix") or {},
                price_band=row.get("price_band") or {},
                color_notes=row.get("color_notes") or [],
                recorded_by="portal",
                valid_until=TimeHelper.now() + timedelta(hours=48),
            )
    rows = CatalogRowSerializer(latest, many=True).data
    return Response({"taxonomy": TAXONOMY, "rows": rows})


@api_view(["POST"])
def shop_catalog_import(request):
    """POST /me/shop/catalog/import (multipart/CSV per docs 06 §5)."""
    shop = get_shop(request)
    if not shop:
        return Response({"error": {"code": "FORBIDDEN_SCOPE", "message": "shop token required"}}, status=401)
    raw = txt = None
    if "file" in request.FILES:
        txt = request.FILES["file"].read().decode("utf-8")
    else:
        txt = (request.data or {}).get("csv", "")
    errors, imported = [], 0
    reader = csv.DictReader(io.StringIO(txt or ""))
    for row in reader:
        key = (row.get("category_code") or "").strip()
        if key not in TAXONOMY:
            errors.append({"row": row, "reason": f"unknown taxonomy code {key}"})
            continue
        CatalogState.objects.filter(shop=shop, catalog_key=key, superseded_at__isnull=True)\
            .update(superseded_at=TimeHelper.now())
        sizes = [s.strip() for s in (row.get("sizes_available") or "").split(";") if s.strip()]
        CatalogState.objects.create(
            shop=shop, catalog_key=key, label=TAXONOMY[key]["label"],
            state=(row.get("state") or "in"),
            size_matrix={s: True for s in sizes},
            color_notes=[c.strip() for c in (row.get("colors") or "").split(";") if c.strip()],
            price_band={"min": _num(row.get("price_min")), "max": _num(row.get("price_max"))} if
            (row.get("price_min") or row.get("price_max")) else {},
            recorded_by="portal",
            valid_until=TimeHelper.now() + timedelta(hours=48),
        )
        imported += 1
    return Response({"imported": imported, "errors": errors})


def _num(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None


@api_view(["GET"])
def shop_inquiries(request):
    shop = get_shop(request)
    if not shop:
        return Response({"error": {"code": "FORBIDDEN_SCOPE", "message": "shop token required"}}, status=401)
    targets = QueryTarget.objects.filter(
        shop=shop,
        query__status="processing",
        state__in=["queued", "contacting", "awaiting_reply", "interviewed"],
    ).select_related("query").order_by("-query__created_at")[:50]
    return Response({"items": InboxTargetSerializer(targets, many=True).data})


@api_view(["POST"])
def shop_inquiry_reply(request, tid: int):
    shop = get_shop(request)
    if not shop:
        return Response({"error": {"code": "FORBIDDEN_SCOPE", "message": "shop token required"}}, status=401)
    target = QueryTarget.objects.filter(id=tid, shop=shop).first()
    if not target:
        return Response({"error": {"code": "NOT_FOUND", "message": "Inquiry not found"}}, status=404)
    outcome = (request.data or {}).get("outcome", "CONFIRMED_IN_STOCK")
    sizes = (request.data or {}).get("sizes") or []
    price_text = (request.data or {}).get("price_text", "")
    condition_text = (request.data or {}).get("condition_text", "")
    apply_catalog_reply(target.id, outcome=outcome, sizes=sizes,
                        price_text=price_text, condition_text=condition_text)
    return Response({"ok": True, "target_id": target.id, "state": target.state})
