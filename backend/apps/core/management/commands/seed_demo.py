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

        made = 0
        for i in range(12):
            city = City.objects.get(code="pune" if i < 9 else "mumbai")
            lat = float(city.center_lat) + random.uniform(-0.02, 0.02)
            lng = float(city.center_lng) + random.uniform(-0.02, 0.02)
            phone_base = 919000000001 + i
            behavior = behaviors[i % len(behaviors)]
            shop, _ = Shop.objects.update_or_create(
                ops_phone=str(phone_base),
                defaults={
                    "display_name": f"Demo Store {i + 1}",
                    "verticals": ["fashion"] if i % 3 else ["electronics"],
                    "address_text": f"Shop {i + 1}, Market Road, {city.name}",
                    "city": city, "lat": lat, "lng": lng,
                    "public_phone": f"+91{9000000000 + i}",
                    "whatsapp_number": str(phone_base),
                    "whatsapp_linked": i % 5 != 0,   # no-WA shops exercise SMS/call fallback
                    "claimed_at": now if i % 4 != 3 else None,  # a few unclaimed (display only)
                    "current_plan": plans_cycle[i % len(plans_cycle)],
                    "accuracy_score": 0.9 + (i % 5) * 0.02,
                    "hours_text": "10:00–20:00",
                    "mock_behavior": behavior,
                    "source": "ops",
                })
            ContactPolicy.objects.get_or_create(shop=shop, defaults={
                "channels": ["whatsapp", "call"] if behavior.startswith("wa_only") else ["call", "whatsapp"],
                "language_pref": "hi"})
            # catalog — choose state so the buyer-side flow demos each behaviour:
            #   live-checked: always_yes / no_with_alternative / wa_only_yes / conditional
            #   stale (excluded from fresh matching): unreachable / never_answer
            keys = ["fashion.dress", "fashion.kurti"] if shop.verticals == ["fashion"] else ["electronics.powerbank"]
            for key in keys:
                behavior_stale = shop.mock_behavior in ("unreachable", "never_answer")
                live_checked = shop.mock_behavior not in ("unreachable", "never_answer")
                CatalogState.objects.update_or_create(
                    shop=shop, catalog_key=key, superseded_at__isnull=True,
                    defaults={
                        "label": TAXONOMY[key]["label"],
                        "state": "partial" if live_checked else "in",
                        "size_matrix": {"S": True, "M": True, "L": i % 2 == 0, "XL": False},
                        "price_band": {"min": 499, "max": 2499},
                        "color_notes": ["Blue", "Black", "Maroon"] if key == "fashion.dress" else ["White"],
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
