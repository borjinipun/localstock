"""Canonical availability vocabulary + state machine values (spec 03 §2, §12)."""

OUTCOMES = [
    "CONFIRMED_IN_STOCK",
    "SHOP_REPORTED_IN_STOCK",
    "CONFIRMED_OUT_OF_STOCK",
    "ALTERNATIVE_OFFERED",
    "CONDITIONAL",
    "UNREACHABLE",
    "NO_ANSWER",
    "UNCERTAIN",
    "OPT_OUT_FLAGGED",
    "HUMAN_ESCALATED",
]

EVIDENCE_KINDS = ["catalog", "call", "whatsapp", "sms", "inbox", "human"]

TARGET_STATES = ["queued", "contacting", "awaiting_reply", "interviewed", "resolved"]

QUERY_STATES = ["processing", "completed", "cancelled"]
