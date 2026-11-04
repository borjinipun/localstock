"""Taxonomy v0.1 — fashion first, electronics second (spec 02 §E, OQ-05).
Groceries stub included for Phase-2 but not seeded at MVP."""

TAXONOMY = {
    # Fashion
    "fashion.dress": {"label": "Dress", "vertical": "fashion",
                      "synonyms": ["dress", "frock", "frocks", "gown", "one piece", "ड्रेस", "गाउन"]},
    "fashion.kurti": {"label": "Kurta / Kurti", "vertical": "fashion",
                      "synonyms": ["kurta", "kurti", "kurtas", "कुर्ता", "कुर्ती"]},
    "fashion.shirt": {"label": "Shirt", "vertical": "fashion",
                      "synonyms": ["shirt", "shirts", "formal shirt", "शर्ट"]},
    "fashion.tshirt": {"label": "T-shirt", "vertical": "fashion",
                       "synonyms": ["tshirt", "t-shirt", "tee", "टीशर्ट"]},
    "fashion.saree": {"label": "Saree / Sari", "vertical": "fashion",
                      "synonyms": ["saree", "sari", "साड़ी", "सारी"]},
    # Electronics
    "electronics.powerbank": {"label": "Powerbank", "vertical": "electronics",
                              "synonyms": ["powerbank", "power bank", "पावरबैंक"]},
    "electronics.headphones": {"label": "Headphones", "vertical": "electronics",
                               "synonyms": ["headphones", "earphones", "headset", "बुडवाइस"]},
    "electronics.phone": {"label": "Smartphone", "vertical": "electronics",
                          "synonyms": ["phone", "smartphone", "mobile", "मोबाइल"]},
    # Groceries (stub, not launched)
    "groceries.atta": {"label": "Atta / Flour", "vertical": "groceries",
                       "synonyms": ["atta", "flour", "gehu", "आटा"]},
}

SYNONYMS = {}
for code, node in TAXONOMY.items():
    key = node["label"].lower()
    SYNONYMS[key] = code
    for syn in node["synonyms"]:
        SYNONYMS[syn.lower()] = code

# Size vocabulary (spec 02 §E)
SIZES = {"xs", "s", "m", "l", "xl", "xxl"}

SIZE_ALIASES = {
    "small": "S", "medium": "M", "large": "L",
    "chota": "S", "bada": "L", "मीडियम": "M", "मध्यम": "M",
}

# Canonical 24-swatch-equivalent core colours (docs 02 §E). Values are display names;
# keys include Hinglish/Hindi variants used by shopkeepers and buyers alike.
COLORS = {
    "blue": "Blue", "neela": "Blue", "neeli": "Blue", "नीला": "Blue", "नीली": "Blue",
    "black": "Black", "kaala": "Black", "kala": "Black", "काला": "Black",
    "red": "Red", "laal": "Red", "लाल": "Red",
    "green": "Green", "hara": "Green", "हरा": "Green",
    "white": "White", "safed": "White", "सफ़ेद": "White",
    "pink": "Pink", "gulabi": "Pink", "गुलाबी": "Pink",
    "yellow": "Yellow", "peela": "Yellow", "पीला": "Yellow",
    "maroon": "Maroon", "brown": "Brown", "grey": "Grey", "gray": "Grey",
    "orange": "Orange", "purple": "Purple", "beige": "Beige", "navy": "Navy",
}
