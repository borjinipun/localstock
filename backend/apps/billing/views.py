from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.shops.auth import get_shop
from apps.shops.models import Shop

from .models import Payment, Plan, Subscription


@api_view(["GET"])
def plans_list(request):
    plans = Plan.objects.filter(archived_at__isnull=True)
    return Response({"items": [
        {"code": p.code, "name": p.name, "price_paise": p.monthly_paise,
         "checks_month": p.checks_month, "features": p.features} for p in plans
    ]})


@api_view(["GET", "POST"])
def subscription_endpoint(request):
    """GET current subscription; POST {plan_code} to change plan (docs 04 §6).
    PAYMENTS provider is mock at MVP; Razorpay path stubbed per docs 07 §4."""
    shop = get_shop(request)
    if not shop:
        return Response({"error": {"code": "FORBIDDEN_SCOPE", "message": "shop token required"}}, status=401)
    sub = getattr(shop, "subscription", None)

    if request.method == "GET":
        return Response({"plan": sub.plan_code if sub else "free", "status": sub.status if sub else None,
                         "period_end": sub.period_end if sub else None})

    plan = Plan.objects.filter(code=(request.data or {}).get("plan_code"),
                               archived_at__isnull=True).first()
    if not plan:
        return Response({"error": {"code": "VALIDATION_ERROR", "message": "unknown plan_code"}}, status=400)

    # mock razorpay
    if settings.PROVIDER_PAYMENTS == "mock":
        period_end = timezone.now() + timedelta(days=30)
        sub, created = Subscription.objects.update_or_create(
            shop=shop,
            defaults={"plan_code": plan.code, "status": "active", "period_end": period_end})
        Payment.objects.create(
            subscription=sub, amount_paise=plan.monthly_paise,
            gst_amount_paise=int(plan.monthly_paise * 0.18),
            provider="mock", status="captured", invoice_no=f"INV-{shop.id}-{int(timezone.now().timestamp())}",
        )
        Shop.objects.filter(id=shop.id).update(current_plan=plan.code)
        return Response({"ok": True, "plan": plan.code, "period_end": period_end})

    # real provider path reserved (docs 07 §4) — OQ-06/pricing needs founder's keys first.
    return Response({"error": {"code": "PROVIDER_DOWN", "message": "razorpay adapter not configured"}}, status=501)
