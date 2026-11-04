"""Verification orchestrator (docs 03). MVP engine:
- channel decision table implemented deterministically, logged on target;
- dispatch to voice-svc (which owns telephony / WhatsApp / SMS adapters);
- applies webhook updates idempotently, writes AvailabilityRecords,
- escalates `UNCERTAIN` / callback requests into ops tasks.
"""
import os
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from apps.queries.models import AvailabilityRecord, QueryTarget
from apps.ops.models import OpsTask

from .models import VerificationAttempt

COST_PER_LIVE_CHECK_PAISE = 220


# ---------------------------------------------------------------- strategies

def _channels(shop) -> list[str]:
    policy = getattr(shop, "contact_policy", None)
    base = policy.channels if policy else ["call", "whatsapp"]
    if policy and policy.opt_out:
        return []
    if shop.whatsapp_linked is False:
        base = [c for c in base if c != "whatsapp"]
    return base or ["call"]


def decide_channel(target: QueryTarget) -> dict:
    shop = target.shop
    policy = getattr(shop, "contact_policy", None)
    channels = _channels(shop)
    choice = channels[0] if channels else None
    decision = {
        "policy_channels": policy.channels if policy else ["call", "whatsapp"],
        "quiet_hours": None if policy is None else (str(policy.quiet_start), str(policy.quiet_end)),
        "chosen": choice, "fallbacks": channels[1:2] if len(channels) > 1 else [],
        "opt_out": bool(policy.opt_out) if policy else False,
        "channels_order": channels,
    }
    target.contact_decision = {**(target.contact_decision or {}), **decision, "channels_order": channels}
    target.save(update_fields=["contact_decision"])
    return decision


# ---------------------------------------------------------------- dispatch

def start_verification(target_id: int) -> None:
    target = QueryTarget.objects.select_related("shop", "shop__contact_policy").get(id=target_id)
    decision = decide_channel(target)
    target.state = "contacting"
    target.save(update_fields=["state"])

    attempt = VerificationAttempt.objects.create(
        target=target, channel=decision["chosen"] or "call",
        reason_code="",
    )

    if not decision["chosen"]:
        _apply(target, attempt, outcome="OPT_OUT_FLAGGED", reason_code="shop_opt_out",
               evidence=None, transcript=None)
        return

    payload = {
        "target_id": target.id,
        "attempt_id": attempt.id,
        "shop": {
            "id": target.shop.id,
            "name": target.shop.display_name,
            "phone": target.shop.ops_phone,
            "language": target.shop.contact_policy.language_pref
            if getattr(target.shop, "contact_policy", None) else "hi",
            "mock_behavior": target.shop.mock_behavior,
        },
        "item_intent": target.query.parsed_intent,
        "languages": ["hi", "en"],
        "channels": decision["channels_order"] or ["call"],
        "callback_url": os.environ.get("API_INTERNAL_URL",
                                       "http://localhost:8000/api/internal/verification/update/"),
        "callback_token": settings.SERVICE_TOKEN,
    }
    try:
        resp = requests.post(f"{settings.VOICESVC_URL}/v1/calls", json=payload, timeout=5,
                             headers={"X-Service-Token": settings.SERVICE_TOKEN})
        if resp.status_code != 202:
            raise RuntimeError(resp.text)
        attempt.provider_call_id = (resp.json().get("call_id") or "")[:64]
        attempt.save(update_fields=["provider_call_id"])
    except Exception as exc:  # provider down → degrade honestly (NFR-R2)
        _apply(target, attempt, outcome="UNREACHABLE", reason_code="provider_down",
               transcript=str(exc), provider_events=[{"event": "dispatch_failed"}])


# ------------------------------------------------------- webhook application

def apply_verification_update(target_id: int, payload: dict) -> dict:
    """Idempotent application of a lifecycle webhook payload (docs 03 §12)."""
    target = QueryTarget.objects.select_related("shop", "query").get(id=target_id)
    if target.state == "resolved":
        return {"ok": True, "idempotent": True}

    channel = payload.get("channel") or "call"
    attempt = (VerificationAttempt.objects.filter(target=target, channel=channel)
               .order_by("-started_at").first()
               or VerificationAttempt.objects.create(target=target, channel=channel))

    attempt.outcome = payload.get("outcome") or attempt.outcome
    attempt.transcript = (payload.get("transcript") or "")[:4000]
    attempt.reason_code = payload.get("reason_code") or attempt.reason_code
    attempt.asr_confidence = payload.get("asr_confidence") or attempt.asr_confidence
    if payload.get("nlu_schema"):
        attempt.nlu_schema = payload["nlu_schema"]
    if payload.get("provider_events"):
        attempt.provider_events = payload["provider_events"]
    if payload.get("recording_s3_key"):
        attempt.recording_s3_key = payload["recording_s3_key"]
    attempt.ended_at = timezone.now()
    attempt.save()

    _apply(target, attempt,
           outcome=payload.get("outcome") or "UNCERTAIN",
           reason_code=payload.get("reason_code") or "",
           evidence=channel,
           transcript=None if payload.get("transcript") is None else attempt.transcript,
           sizes=payload.get("sizes") or [],
           price_text=payload.get("price_text") or "",
           condition_text=payload.get("condition_text") or "",
           nlu=attempt.nlu_schema)
    return {"ok": True, "idempotent": False}


def apply_catalog_reply(target_id: int, outcome: str, sizes=None, price_text="", condition_text=""):
    """Shop-portal / inbox answer path (docs 04 §4): counts as verified evidence."""
    from .models import VerificationAttempt as VA
    target = QueryTarget.objects.select_related("shop", "query").get(id=target_id)
    attempt = VA.objects.create(target=target, channel="inbox")
    _apply(target, attempt, outcome=outcome, reason_code="portal_reply", evidence="inbox",
           transcript="(shop replied via portal inbox)",
           sizes=sizes or [], price_text=price_text, condition_text=condition_text)


# ---------------------------------------------------------------- internal

def _apply(target, attempt, outcome, reason_code, evidence, transcript, sizes=None,
           price_text="", condition_text="", nlu=None, provider_events=None):
    target.state = "resolved"
    target.outcome = outcome
    target.reason_code = reason_code
    target.channel_used = attempt.channel
    target.save()
    attempt.outcome = outcome
    attempt.reason_code = reason_code
    if provider_events:
        attempt.provider_events = provider_events
    attempt.save(update_fields=["outcome", "reason_code", "provider_events"])

    evidence = evidence or "call"
    if evidence == "catalog":
        state, kind = "SHOP_REPORTED_IN_STOCK", "catalog"
    else:
        state = {"CONFIRMED_IN_STOCK": "CONFIRMED_IN_STOCK",
                 "SHOP_REPORTED_IN_STOCK": "SHOP_REPORTED_IN_STOCK",
                 "CONFIRMED_OUT_OF_STOCK": "CONFIRMED_OUT_OF_STOCK",
                 "ALTERNATIVE_OFFERED": "ALTERNATIVE_OFFERED",
                 "CONDITIONAL": "CONDITIONAL"}.get(outcome, outcome if outcome in
                                                  ("UNREACHABLE", "NO_ANSWER", "UNCERTAIN",
                                                   "OPT_OUT_FLAGGED") else "UNCERTAIN")
        kind = evidence if evidence in ("call", "whatsapp", "sms", "inbox", "human") else "call"

    snippet = None
    if transcript:
        cleaned = [l for l in transcript.strip().splitlines() if l]
        snippet = " | ".join(cleaned[-3:])[:240]

    AvailabilityRecord.objects.update_or_create(
        shop=target.shop, query=target.query, evidence_kind=kind,
        defaults={
            "item_intent": {"target_id": target.id},
            "state": state,
            "sizes": sizes or [],
            "colors": [],
            "price_text": price_text,
            "condition_text": condition_text,
            "transcript_snippet": snippet or "",
            "freshness_at": timezone.now(),
            "publish_state": "published",
        })

    if outcome in ("UNCERTAIN",) or (outcome == "CONDITIONAL" and not condition_text):
        OpsTask.objects.create(kind="escalate", ref_id=target.id,
                               payload={"attempt_id": attempt.id, "outcome": outcome})

    from apps.queries.tasks import finalize_if_settled
    finalize_if_settled(target.query_id)
