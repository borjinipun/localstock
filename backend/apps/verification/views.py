import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import apply_verification_update


@csrf_exempt
@require_POST
def verification_update(request):
    """POST /api/internal/verification/update/ — transport from voice-svc (docs 07 §5).
    Auth: X-Service-Token must equal settings.SERVICE_TOKEN (dev NFR-S4 note: shared
    secret is MVP placeholder; swap to mTLS/VPC in prod)."""
    if request.headers.get("X-Service-Token") != settings.SERVICE_TOKEN:
        return JsonResponse({"error": {"code": "FORBIDDEN_SCOPE", "message": "bad service token"}}, status=401)
    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        return JsonResponse({"error": {"code": "VALIDATION_ERROR", "message": "invalid json"}}, status=400)
    target_id = payload.get("target_id")
    if not target_id:
        return JsonResponse({"error": {"code": "VALIDATION_ERROR", "message": "target_id required"}}, status=400)
    result = apply_verification_update(int(target_id), payload)
    return JsonResponse(result)
