"""Intent parser v0.1 — deterministic rules per docs 02 F-C-02.
Production replaces this with the LLM classifier; same output schema kept."""
import re

from apps.catalog.services import COLORS, SIZE_ALIASES, SIZES, SYNONYMS

_TOKEN = re.compile(r"[\w'-]+", re.UNICODE)
_PRICE = re.compile(r"(?:₹|rs\.?|rupees?|under|below|less than|में)\s*(\d[\d,]{0,7})", re.IGNORECASE)


def parse_text(text: str) -> dict:
    data = (text or "").lower()
    tokens = _TOKEN.findall(data)

    item_codes, item_labels = [], []
    for tok in tokens + [" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)]:
        code = SYNONYMS.get(tok)
        if code and code not in item_codes:
            item_codes.append(code)
            item_labels.append(code.split(".", 1)[1].replace("_", " ").title())
    # Drop multi-word hit if its single-word parent also hit (t-shirt vs shirt confusion guard)
    if len(item_codes) > 1:
        item_codes = [c for c in item_codes if not any(c in o for o in item_codes if o != c)]

    size = None
    for tok in tokens:
        t = tok.strip()
        if t in SIZES:
            size = t.upper()
            break
        if t in SIZE_ALIASES:
            size = SIZE_ALIASES[t]
            break

    color = None
    for tok in tokens:
        if tok in COLORS:
            color = COLORS[tok]
            break

    price = None
    m = _PRICE.search(data)
    if m:
        price = int(m.group(1).replace(",", ""))
        if re.search(r"(above|over|more than|kam se kam)", data):
            price = None  # unsupported direction at MVP: ignored (chip stays editable in UI)

    confidence = 0.4 + 0.2 * bool(item_codes) + 0.2 * bool(color) + 0.2 * bool(size)
    return {
        "item_codes": item_codes,
        "item_labels": item_labels,
        "color": color,
        "size": size,
        "brand": None,          # TODO(spec 02 F-C-02): brand chips after LLM classifier
        "price_max": price,
        "confidence": round(min(confidence, 1.0), 2),
        "raw": text,
    }
