"""Dialog flow designer + NLU snippets (docs 03 §4.2 script, §4.3 intents).

build_flows(behavior, channels, item_intent) → list[(delay_seconds, webhook_payload)]
Deterministic mock path; real providers replace `transcript` generation with
the streaming ASR pipeline but keep the same webhook contract (backend only).
"""
import asyncio
import os
import uuid

import httpx

DELAYS = {"whatsapp": 6, "call": 12, "sms": 9}

# intent wording per docs 03 §4.2 script skeleton
ASK_TEMPLATE = "नमस्ते! [App से] एक ऑटोमेटेड कॉल है — एक ग्राहक का सवाल। क्या {item}{color} साइज़ {size} उपलब्ध है?"
YES_TEMPLATE = "हाँ, {color} {size}{extra} बची हैं। {price}"
NO_TEMPLATE = "नहीं, नीले रंग की ड्रेस अभी नहीं है — {alternative} मिल जायेगा।"
COND_TEMPLATE = "आधे घंटे बाद आ जाओगे तो मिल जायेगा।"


def _item_desc(item_intent):
    color = item_intent.get("color") or "नीला"
    size = item_intent.get("size") or "M"
    label = (item_intent.get("item_labels") or ["ड्रेस"])[0]
    return color, size, label


def yes_payload(behavior, channel, item_intent, target_id, attempt_id):
    color, size, _ = _item_desc(item_intent)
    transcript = (
        "bot(automated disclosure): " + ASK_TEMPLATE.format(item="", color=color, size=size) + "\n"
        f"shop: {YES_TEMPLATE.format(color=color, size=size, extra=' और L भी', price='₹1,999 (MRP ₹2,499)')}\n"
        "bot: धन्यवाद! ग्राहक को बता दिया जायेगा।"
    )
    return {
        "target_id": target_id,
        "attempt_id": attempt_id,
        "channel": channel,
        "outcome": "CONFIRMED_IN_STOCK",
        "sizes": [size, "L"],
        "price_text": "₹1,999 (MRP ₹2,499)",
        "condition_text": "",
        "transcript": transcript,
        "asr_confidence": 0.93,
        "provider_events": [{"event": "ringing"}, {"event": "answered"},
                            {"event": "transcript.hey_reply"}, {"event": "ended", "reason": "completed"}],
        "recording_s3_key": f"mock-recordings/{target_id}-{uuid.uuid4().hex[:8]}.ogg",
    }


def alternative_payload(behavior, channel, item_intent, target_id, attempt_id):
    transcript = (
        "bot: " + ASK_TEMPLATE.format(item="", color="नीला", size="M") + "\n"
        "shop: नहीं, नीला नहीं है — काला और मरून मिल जायेगा\n"
        "bot: धन्यवाद!"
    )
    return {
        "target_id": target_id,
        "attempt_id": attempt_id,
        "channel": channel,
        "outcome": "ALTERNATIVE_OFFERED",
        "sizes": ["M", "L"],
        "price_text": "₹1,499",
        "condition_text": "Black & Maroon only",
        "transcript": transcript,
        "asr_confidence": 0.88,
        "provider_events": [{"event": "ringing"}, {"event": "answered"}, {"event": "ended"}],
        "recording_s3_key": "",
    }


def conditional_payload(behavior, channel, item_intent, target_id, attempt_id):
    return {
        "target_id": target_id,
        "attempt_id": attempt_id,
        "channel": channel,
        "outcome": "CONDITIONAL",
        "sizes": [],
        "price_text": "",
        "condition_text": "आधे घंटे बाद आ जाओगे तो मिल जायेगा (half hour)",
        "transcript": "bot: क्या ... मिलेगा?\nshop: हाँ पर आधे घंटे बाद।\nbot: धन्यवाद!",
        "asr_confidence": 0.9,
        "provider_events": [{"event": "ringing"}, {"event": "answered"}, {"event": "ended"}],
        "recording_s3_key": "",
    }


def unreachable_payload(behavior, channel, item_intent, target_id, attempt_id):
    events = [{"event": "ringing"}, {"event": "no_answer"}] if channel == "call" else \
             [{"event": "whatsapp.sent"}, {"event": "whatsapp.undelivered"}]
    return {
        "target_id": target_id,
        "attempt_id": attempt_id,
        "channel": channel,
        "outcome": "UNREACHABLE",
        "reason_code": "no_answer" if channel == "call" else "wa_undelivered",
        "transcript": "",
        "asr_confidence": None,
        "provider_events": events,
        "recording_s3_key": "",
    }


def build_flows(behavior: str, channels: list[str], item_intent: dict,
                target_id: int, attempt_id: int):
    """Deterministic sequence of webhook payloads per docs/03 decision table."""
    useables = [c for c in channels if c in DELAYS]
    if not useables:
        channels = ["call"]
        useables = ["call"]
    target_channel = None
    for behavior_pref in (
        "whatsapp" if behavior.startswith("wa_only") else None,
        None,
    ):
        target_channel = behavior_pref or useables[0]
        break

    if behavior == "wa_only_yes":
        if "whatsapp" in useables:
            return [(DELAYS["whatsapp"], yes_payload(behavior, "whatsapp", item_intent, target_id, attempt_id))]
        return [(max(DELAYS.values()), unreachable_payload("never_answer", "call", item_intent, target_id, attempt_id))]

    builder = {
        "always_yes": yes_payload,
        "no_with_alternative": alternative_payload,
        "conditional": lambda *a, **k: conditional_payload(*a, **k),
        "unreachable": unreachable_payload,
        "never_answer": unreachable_payload,
        "wa_only_yes": yes_payload,
    }.get(behavior, yes_payload)

    payload = builder(behavior, target_channel, item_intent, target_id, attempt_id)
    if behavior == "unreachable":
        payload["provider_events"] = [{"event": "ringing"}, {"event": "ringing"}, {"event": "no_answer"}]
    return [(DELAYS[target_channel], payload)]


async def _deliver(delay_seconds, payload, callback_url, token):
    await asyncio.sleep(max(0, delay_seconds))
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(callback_url, json=payload, headers={"X-Service-Token": token})
        except Exception as exc:  # pragma: no cover — logged & dropped (idempotent retries at back-end)
            print(f"[voice-svc] webhook delivery failed: {exc}")


def schedule_flows(flows, callback_url, token):
    for delay, payload in flows:
        asyncio.create_task(_deliver(delay, payload, callback_url, token))


def __main__scenario_row():
    assert os.environ.get("SERVICE_TOKEN", "dev-service-token") == "dev-service-token"
