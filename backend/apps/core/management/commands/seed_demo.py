"""Demo seed: cities, plans, shops with scripted behaviours, catalog (docs/09 Phase-0 betа).

Phones pool maps to scripted behaviours so the whole query flow can be
demonstrated end-to-end with the mock providers.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.billing.models import Plan
from apps.catalog.models import CatalogState
from apps.catalog.services import TAXONOMY
from apps.core.models import City
from apps.shops.models import ClaimRequest, ContactPolicy, Shop


class Command(BaseCommand):
    help = "Seed cities, plans, shops, catalog for the demo (safe to re-run)."

    def handle(self, *args, **options):
        random.seed(7)
        cities = {
            "pune": ("Pune", 18.5204, 73.8567),
            "mumbai": ("Mumbai", 19.0760, 72.8777),
        }
        for code, (name, lat, lng) in cities.items():
            City.objects.update_or_create(
                code=code, defaults={"name": name, "center_lat": lat, "center_lng": lng, "is_live": True})

        for code, name, paise, checks in [
            ("free", "Basic", 0, 50),
            ("grow", "Grow", 99900, 250),
            ("featured", "Featured", 249900, 1000),
            ("scale", "Scale", 499900, 5000),
        ]:
            Plan.objects.update_or_create(code=code, defaults={
                "name": name, "monthly_paise": paise, "checks_month": checks,
                "rank_boost": {"free": 0.03, "grow": 0.06, "featured": 0.09, "scale": 0.09}[code],
                "features": {} if code == "free" else {"accuracy_showcase": True},
            })

        behaviors = ["always_yes", "always_yes", "always_yes", "no_with_alternative",
                     "conditional", "wa_only_yes", "unreachable", "never_answer", "always_yes",
                     "always_yes", "wa_only_yes", "no_with_alternative"]
        plans_cycle = ["free", "grow", "featured", "free", "grow", "free"]
        now = timezone.now()
        valid_until = now + timedelta(hours=48)

        SHOP_PRESETS = [
            # Fashion Products & Tailoring Services
            {"name": "Style Studio & Fashion Boutique", "verticals": ["fashion"], "catalog": "fashion.dress"},
            {"name": "Royal Men's Apparel & Kurtas", "verticals": ["fashion"], "catalog": "fashion.kurti"},
            {"name": "Master Stitch Tailors & Alterations", "verticals": ["tailoring", "fashion"], "catalog": "service.tailor"},
            # Electronics & Repair Services
            {"name": "QuickFix Mobile & Laptop Repair", "verticals": ["mobile_repair", "electronics"], "catalog": "service.mobile_repair"},
            {"name": "Apex Electronics & Power Hub", "verticals": ["electronics"], "catalog": "electronics.powerbank"},
            {"name": "CyberTech Computer & Screen Care", "verticals": ["laptop_repair", "electronics"], "catalog": "service.laptop_repair"},
            # Home Services & Hardware
            {"name": "Metro Hardware & Plumbing Solutions", "verticals": ["plumbing", "hardware"], "catalog": "service.plumber"},
            {"name": "PowerLine Electricals & Wiring Hub", "verticals": ["electrician", "hardware"], "catalog": "service.electrician"},
            # Essentials & Pharmacy
            {"name": "Lifeline Chemist & Medical Store", "verticals": ["pharmacy"], "catalog": "pharmacy.medicine"},
            {"name": "Sparkle Dry Cleaners & Laundry", "verticals": ["laundry"], "catalog": "service.laundry"},
            {"name": "City Kirana & Daily Provisions", "verticals": ["groceries"], "catalog": "groceries.atta"},
            {"name": "Urban Edge Apparel (Unclaimed)", "verticals": ["fashion"], "catalog": "fashion.dress"},
        ]

        made = 0
        for i, preset in enumerate(SHOP_PRESETS):
            city = City.objects.get(code="pune" if i < 8 else "mumbai")
            lat = float(city.center_lat) + random.uniform(-0.015, 0.015)
            lng = float(city.center_lng) + random.uniform(-0.015, 0.015)
            phone_base = 919000000001 + i
            behavior = behaviors[i % len(behaviors)]
            is_unclaimed = (i == len(SHOP_PRESETS) - 1)  # last one unclaimed

            shop, _ = Shop.objects.update_or_create(
                ops_phone=str(phone_base),
                defaults={
                    "display_name": preset["name"],
                    "verticals": preset["verticals"],
                    "address_text": f"Shop {i + 1}, Main Market Road, {city.name}",
                    "city": city, "lat": lat, "lng": lng,
                    "public_phone": f"+91{9000000000 + i}",
                    "whatsapp_number": str(phone_base),
                    "whatsapp_linked": i % 5 != 0,
                    "claimed_at": None if is_unclaimed else now,
                    "current_plan": plans_cycle[i % len(plans_cycle)],
                    "accuracy_score": 0.90 + (i % 5) * 0.02,
                    "hours_text": "09:30–21:00",
                    "mock_behavior": behavior,
                    "source": "ops",
                })
            ContactPolicy.objects.get_or_create(shop=shop, defaults={
                "channels": ["whatsapp", "call"] if behavior.startswith("wa_only") else ["call", "whatsapp"],
                "language_pref": "hi"})

            cat_key = preset["catalog"]
            if cat_key in TAXONOMY:
                behavior_stale = shop.mock_behavior in ("unreachable", "never_answer")
                live_checked = shop.mock_behavior not in ("unreachable", "never_answer")
                CatalogState.objects.update_or_create(
                    shop=shop, catalog_key=cat_key, superseded_at__isnull=True,
                    defaults={
                        "label": TAXONOMY[cat_key]["label"],
                        "state": "partial" if live_checked else "in",
                        "size_matrix": {"S": True, "M": True, "L": i % 2 == 0, "XL": False},
                        "price_band": {"min": 350, "max": 1800},
                        "color_notes": ["Blue", "Black", "Maroon"] if "fashion" in preset["verticals"] else ["Standard"],
                        "recorded_by": "portal",
                        "valid_until": valid_until if live_checked else now - timedelta(hours=2),
                    })
            made += 1

        # One pending claim for the portal demo
        pending_shop = Shop.objects.filter(claimed_at__isnull=True).first()
        if pending_shop:
            ClaimRequest.objects.get_or_create(
                shop=pending_shop, applicant_phone=pending_shop.ops_phone,
                defaults={"otp_code": "42912"})

        self.stdout.write(self.style.SUCCESS(
            f"Seeded cities={len(cities)} plans=4 shops={made} (phones 919000000001 …)"))
