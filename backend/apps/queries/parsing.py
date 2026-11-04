"""Intent parser v0.2 — deterministic & multi-domain rules for Products and Local Services.
Extracts items, services, action verbs, color, size, price, and target verticals."""
import re

from apps.catalog.services import COLORS, SIZE_ALIASES, SIZES, SYNONYMS, TAXONOMY

_TOKEN = re.compile(r"[\w'-]+", re.UNICODE)
_PRICE = re.compile(r"(?:₹|rs\.?|rupees?|under|below|less than|में|तक)\s*(\d[\d,]{0,7})", re.IGNORECASE)

SERVICE_VERBS = {
    "repair": "repair", "fixing": "repair", "fix": "repair", "replace": "repair", "replacement": "repair",
    "stitching": "stitching", "stitch": "stitching", "alteration": "alteration", "alter": "alteration",
    "fitting": "alteration", "clean": "cleaning", "cleaning": "cleaning", "wash": "cleaning",
    "service": "service", "servicing": "service", "install": "installation", "fitting": "installation",
    "रिपेयर": "repair", "सिलाई": "stitching", "सर्विस": "service",
}


def parse_text(text: str) -> dict:
    data = (text or "").lower()
    tokens = _TOKEN.findall(data)

    item_codes, item_labels = [], []
    matched_verticals = set()
    intent_type = "product"

    # Search up to 3-gram sequences for accurate service & compound product matching
    candidates = []
    # 3-word phrases
    for i in range(len(tokens) - 2):
        candidates.append(" ".join(tokens[i:i + 3]))
    # 2-word phrases
    for i in range(len(tokens) - 1):
        candidates.append(" ".join(tokens[i:i + 2]))
    # 1-word tokens
    candidates.extend(tokens)

    for cand in candidates:
        code = SYNONYMS.get(cand)
        if code and code not in item_codes:
            item_codes.append(code)
            node = TAXONOMY.get(code, {})
            label = node.get("label") or code.split(".", 1)[1].replace("_", " ").title()
            item_labels.append(label)
            if node.get("vertical"):
                matched_verticals.add(node["vertical"])
            if node.get("type") == "service":
                intent_type = "service"

    # If any service was matched and also products, or action verb present
    service_verb = None
    for tok in tokens:
        if tok in SERVICE_VERBS:
            service_verb = SERVICE_VERBS[tok]
            break

    # If service verb like 'repair' or 'stitching' is present, categorize as service
    if service_verb and intent_type == "product":
        intent_type = "service"
        # If user searched "phone repair" but phone was matched as electronics.phone
        if "electronics.phone" in item_codes and "service.mobile_repair" not in item_codes:
            item_codes.append("service.mobile_repair")
            item_labels.append(TAXONOMY["service.mobile_repair"]["label"])
            matched_verticals.add("mobile_repair")
        elif ("fashion.dress" in item_codes or "fashion.kurti" in item_codes or "fashion.shirt" in item_codes) and "service.tailor" not in item_codes:
            item_codes.append("service.tailor")
            item_labels.append(TAXONOMY["service.tailor"]["label"])
            matched_verticals.add("tailoring")

    # Drop single-word hit if a more specific multi-word hit covers it
    if len(item_codes) > 1:
        filtered = []
        for c in item_codes:
            # If both a generic product and a specific service are present, keep both or specialize
            filtered.append(c)
        item_codes = filtered

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
        if re.search(r"(above|over|more than|kam se kam|ज्यादा)", data):
            price = None

    confidence = 0.4 + 0.2 * bool(item_codes) + 0.2 * bool(color or service_verb) + 0.2 * bool(size or price)
    return {
        "item_codes": item_codes,
        "item_labels": item_labels,
        "intent_type": intent_type,
        "service_verb": service_verb,
        "target_verticals": list(matched_verticals),
        "color": color,
        "size": size,
        "brand": None,
        "price_max": price,
        "confidence": round(min(confidence, 1.0), 2),
        "raw": text,
    }
