"""Shop-facing auth (MVP): signed bearer token, simplest possible per docs 07 §1.
Real deployments should move to short-lived JWT + refresh (docs ADR open default)."""

from django.core.signing import BadSignature, dumps, loads

from apps.shops.models import Shop

SALT = "shop-token"
MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def issue_shop_token(shop_id: int, role: str = "owner") -> str:
    return dumps({"shop_id": shop_id, "role": role}, salt=SALT)


def resolve(request):
    """Returns (shop, payload) or (None, None)."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, None
    try:
        data = loads(header[7:], salt=SALT, max_age=MAX_AGE)
    except BadSignature:
        return None, None
    shop = Shop.objects.filter(id=data.get("shop_id")).select_related("contact_policy").first()
    return shop, data


def get_shop(request):
    shop, _ = resolve(request)
    return shop
