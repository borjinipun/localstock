import json
import time

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .matching import build_extra_targets
from .models import AvailabilityRecord, Query, ReportWrongInfo
from .parsing import parse_text
from .serializers import AvailabilityRecordSerializer, QueryCreatedSerializer, QueryDetailSerializer
from .tasks import match_and_execute_query


@api_view(["POST"])
def query_create(request):
    """POST /queries (docs 07 API-2)."""
    data = request.data or {}
    text = (data.get("text") or "").strip()
    if not text:
        return Response({"error": {"code": "VALIDATION_ERROR", "message": "text required"}}, status=400)

    from apps.core.models import City
    city_code = data.get("city") or "pune"
    city = City.objects.filter(code=city_code).first() or City.objects.filter(is_live=True).first()
    if not city:
        return Response({"error": {"code": "UNREACHABLE_CITY", "message": "No live city configured"}}, status=422)

    parsed = parse_text(text)
    notify_via = data.get("notify_via") if data.get("user_phone") else None
    q = Query.objects.create(
        raw_text=text, parsed_intent={**parsed, **(data.get("parsed") or {})},
        city=city,
        lat=data.get("location", {}).get("lat") or None,
        lng=data.get("location", {}).get("lng") or None,
        radius_m=data.get("radius_m") or 3000,
        share_name=bool(data.get("share_name")),
        user_phone=data.get("user_phone"),
        notify_via=notify_via or [],
        budget_paise=_cfg("QUERY_BUDGET_PAISE"),
        spot_check=bool(data.get("force_spot_check")),
    )
    match_and_execute_query.delay(q.id)

    result = _shape(q)
    return Response({**result}, status=202)


def _cfg(key):
    from django.conf import settings
    return getattr(settings, key)


def _shape(q: Query) -> dict:
    details = QueryDetailSerializer(q).data
    from .models import QueryTarget
    wave = QueryTarget.objects.filter(query=q, state__in=["queued", "contacting",
                                                          "awaiting_reply", "interviewed"]).count()
    instant = [r for r in details["availability"]
               if r["state"] == "SHOP_REPORTED_IN_STOCK"]
    return {
        "query_id": q.id,
        "status": q.status,
        "parsed": details["parsed_intent"],
        "instant_results": instant,
        "availability": details["availability"],
        "checked_wave": {"count": wave, "eta_seconds": 240},
        "stream_url": f"/api/v1/queries/{q.id}/events",
    }


@api_view(["GET"])
def query_detail(request, pk):
    try:
        q = Query.objects.filter(pk=pk).first()
    except Query.DoesNotExist:
        q = None
    if not q:
        return Response({"error": {"code": "NOT_FOUND", "message": "Query not found"}}, status=404)
    return Response(_shape(q))


# ------------------------- SSE (docs 07 API-4) -------------------------
# MVP implementation: a polling-based stream that emits new availability rows.
# Swap to channel/websocket push in Phase 2 if webhook fanout demands (docs 05 NFR-P3).

def query_events(request, pk):
    def stream():
        sent = set()
        deadline = time.time() + 420   # 7-min lifecycle guard
        first = True
        while time.time() < deadline:
            if first:
                from .models import QueryTarget
                targets = list(QueryTarget.objects.filter(query_id=pk).values(
                    "id", "shop_id", "state", "rank_final"))
                yield _sse("targets", {"targets": targets})
                first = False
            for rec in AvailabilityRecord.objects.filter(query_id=pk).select_related("shop"):
                if rec.id in sent:
                    continue
                sent.add(rec.id)
                yield _sse("result", AvailabilityRecordSerializer(rec).data)
            q = Query.objects.filter(pk=pk).first()
            if q and q.status in ("completed", "cancelled"):
                yield _sse("query.completed", {"query_id": pk, "status": q.status})
                break
            time.sleep(1.5)

    resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp


def _sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


# --------------- extend / cancel (docs 07 API-5) ---------------

@api_view(["POST"])
def query_extend(request, pk):
    q = Query.objects.filter(pk=pk).first()
    if not q:
        return Response({"error": {"code": "NOT_FOUND", "message": "Query not found"}}, status=404)
    if q.status != "processing":
        return Response({"error": {"code": "VALIDATION_ERROR", "message": "Query already finished"}}, status=400)
    new_ids = build_extra_targets(q, limit=_cfg("SPOT_CHECK_EXTRA"))
    if not new_ids:
        return Response({"error": {"code": "BUDGET_EXCEEDED", "message": "No budget for more checks"}},
                        status=429)
    from apps.verification.services import start_verification
    for tid in new_ids:
        start_verification(tid)
    return Response({"added_targets": new_ids})


@api_view(["POST"])
def query_cancel(request, pk):
    q = Query.objects.filter(pk=pk).first()
    if not q:
        return Response({"error": {"code": "NOT_FOUND", "message": "Query not found"}}, status=404)
    from django.utils import timezone
    q.status = "cancelled"
    q.completed_at = timezone.now()
    q.save(update_fields=["status", "completed_at"])
    q.targets.exclude(state="resolved").update(state="resolved", reason_code="cancelled")
    return Response({"ok": True, "status": "cancelled"})


@api_view(["POST"])
def availability_report(request, rid):
    rec = AvailabilityRecord.objects.filter(id=rid).first()
    if not rec:
        return Response({"error": {"code": "NOT_FOUND", "message": "Availability record not found"}}, status=404)
    ReportWrongInfo.objects.create(
        availability_record=rec,
        reason=(request.data or {}).get("reason", "unspecified"),
        detail=(request.data or {}).get("detail", ""),
    )
    return Response({"ok": True}, status=201)
