"""Taxonomy v0.2 — Products & Local Services (docs 02 §E, spec expanded).
Covers Fashion, Electronics, Groceries, Pharmacy, Hardware, and Local Services."""

TAXONOMY = {
    # ---------------- Fashion Products ----------------
    "fashion.dress": {
        "label": "Dress", "vertical": "fashion", "type": "product",
        "synonyms": ["dress", "frock", "frocks", "gown", "one piece", "ड्रेस", "गाउन"],
    },
    "fashion.kurti": {
        "label": "Kurta / Kurti", "vertical": "fashion", "type": "product",
        "synonyms": ["kurta", "kurti", "kurtas", "कुर्ता", "कुर्ती", "suit"],
    },
    "fashion.shirt": {
        "label": "Shirt", "vertical": "fashion", "type": "product",
        "synonyms": ["shirt", "shirts", "formal shirt", "casual shirt", "शर्ट"],
    },
    "fashion.tshirt": {
        "label": "T-shirt", "vertical": "fashion", "type": "product",
        "synonyms": ["tshirt", "t-shirt", "tee", "टीशर्ट"],
    },
    "fashion.jeans": {
        "label": "Jeans / Denim", "vertical": "fashion", "type": "product",
        "synonyms": ["jeans", "denim", "trousers", "pants", "जींस"],
    },
    "fashion.saree": {
        "label": "Saree / Sari", "vertical": "fashion", "type": "product",
        "synonyms": ["saree", "sari", "साड़ी", "सारी"],
    },
    "fashion.shoes": {
        "label": "Footwear / Shoes", "vertical": "fashion", "type": "product",
        "synonyms": ["shoes", "sneakers", "sandals", "slippers", "chappal", "जूते", "सैंडल"],
    },

    # ---------------- Electronics Products ----------------
    "electronics.powerbank": {
        "label": "Powerbank", "vertical": "electronics", "type": "product",
        "synonyms": ["powerbank", "power bank", "पावरबैंक", "portable charger"],
    },
    "electronics.headphones": {
        "label": "Headphones / Earphones", "vertical": "electronics", "type": "product",
        "synonyms": ["headphones", "earphones", "headset", "earbuds", "airpods", "बुडवाइस", "हेडफोन"],
    },
    "electronics.phone": {
        "label": "Smartphone / Mobile", "vertical": "electronics", "type": "product",
        "synonyms": ["phone", "smartphone", "mobile", "iphone", "android", "मोबाइल", "फोन"],
    },
    "electronics.charger": {
        "label": "Phone Charger / Cable", "vertical": "electronics", "type": "product",
        "synonyms": ["charger", "type c cable", "charging cable", "adapter", "चार्जर", "केबल"],
    },
    "electronics.screenguard": {
        "label": "Screen Guard / Cover", "vertical": "electronics", "type": "product",
        "synonyms": ["screen guard", "tempered glass", "back cover", "phone case", "स्क्रीन गार्ड"],
    },

    # ---------------- Groceries & Essentials ----------------
    "groceries.atta": {
        "label": "Atta / Flour", "vertical": "groceries", "type": "product",
        "synonyms": ["atta", "flour", "gehu", "आटा"],
    },
    "groceries.milk": {
        "label": "Milk / Dairy", "vertical": "groceries", "type": "product",
        "synonyms": ["milk", "paneer", "curd", "dahi", "दूध", "पनीर"],
    },

    # ---------------- Pharmacy & Medical ----------------
    "pharmacy.medicine": {
        "label": "Medicines / Pharmacy", "vertical": "pharmacy", "type": "product",
        "synonyms": ["medicine", "medicines", "tablets", "syrup", "paracetamol", "painkiller", "दवा", "दवाई"],
    },
    "pharmacy.thermometer": {
        "label": "Thermometer / Medical Supplies", "vertical": "pharmacy", "type": "product",
        "synonyms": ["thermometer", "oximeter", "bandaid", "bandage", "sanitizer", "थर्मामीटर"],
    },

    # ---------------- Hardware & Electrical ----------------
    "hardware.tools": {
        "label": "Hardware / Tools", "vertical": "hardware", "type": "product",
        "synonyms": ["tools", "hammer", "drill", "screws", "pliers", "हथौड़ा", "हार्डवेयर"],
    },
    "hardware.electrical": {
        "label": "Bulbs / Electrical Fittings", "vertical": "hardware", "type": "product",
        "synonyms": ["bulb", "led bulb", "tube light", "wire", "switch", "बल्ब", "बिजली"],
    },

    # ---------------- Local Services ----------------
    "service.tailor": {
        "label": "Tailoring & Alteration", "vertical": "tailoring", "type": "service",
        "synonyms": [
            "tailor", "tailoring", "alteration", "pant fitting", "blouse stitching",
            "suit stitching", "dress fitting", "pant alteration", "darzi", "सिलाई", "दर्जी", "फिटिंग"
        ],
    },
    "service.mobile_repair": {
        "label": "Mobile Repair & Screen Replacement", "vertical": "mobile_repair", "type": "service",
        "synonyms": [
            "mobile repair", "screen repair", "screen replacement", "phone repair", "battery replacement",
            "charging port repair", "iphone repair", "glass repair", "डिस्प्ले रिपेयर", "मोबाइल रिपेयर"
        ],
    },
    "service.laptop_repair": {
        "label": "Laptop & Computer Servicing", "vertical": "laptop_repair", "type": "service",
        "synonyms": [
            "laptop repair", "laptop service", "computer repair", "laptop screen", "keyboard repair",
            "laptop format", "लैपटॉप रिपेयर", "कंप्यूटर रिपेयर"
        ],
    },
    "service.plumber": {
        "label": "Plumbing Service", "vertical": "plumbing", "type": "service",
        "synonyms": [
            "plumber", "plumbing", "pipe leak", "water leakage", "tap repair", "tap replacement",
            "water tank repair", "flush repair", "प्लंबर", "नल रिपेयर"
        ],
    },
    "service.electrician": {
        "label": "Electrician Service", "vertical": "electrician", "type": "service",
        "synonyms": [
            "electrician", "electrical repair", "fan repair", "short circuit", "switch repair",
            "wiring repair", "इलेक्ट्रीशियन", "पंखा रिपेयर"
        ],
    },
    "service.laundry": {
        "label": "Dry Cleaning & Laundry", "vertical": "laundry", "type": "service",
        "synonyms": [
            "dry cleaning", "laundry", "steam press", "ironing", "shoe cleaning", "clothes wash",
            "ड्राई क्लीनिंग", "लॉन्ड्री", "इस्त्री"
        ],
    },
    "service.appliance_repair": {
        "label": "AC & Appliance Repair", "vertical": "appliance_repair", "type": "service",
        "synonyms": [
            "ac service", "ac repair", "refrigerator repair", "washing machine repair", "fridge repair",
            "microwave repair", "एसी सर्विस", "फ्रिज रिपेयर"
        ],
    },
    "service.vehicle_repair": {
        "label": "Bike & Vehicle Servicing", "vertical": "vehicle_repair", "type": "service",
        "synonyms": [
            "bike service", "puncture repair", "car wash", "tyre puncture", "bike repair",
            "oil change", "पंचर", "बाइक सर्विस"
        ],
    },
    "service.salon": {
        "label": "Haircut & Grooming Service", "vertical": "salon", "type": "service",
        "synonyms": [
            "haircut", "salon", "parlour", "beard trim", "facial", "shave", "बाल काटना", "सैलून"
        ],
    },
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
