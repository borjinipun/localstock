from django.db import models

from apps.core.models import TimeStamped


class CatalogState(TimeStamped):
    """Versioned shop catalog row (spec 06 §2). Latest valid row per
    (shop, catalog_key): superseded_at IS NULL AND valid_until > now()."""

    STATE_CHOICES = [("in", "in stock"), ("partial", "partial"), ("out", "out of stock")]
    RECORDED_BY = [
        ("portal", "portal"),
        ("whatsapp", "whatsapp"),
        ("ops", "ops"),
        ("photo_assist", "photo_assist"),
    ]

    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="catalog")
    catalog_key = models.CharField(max_length=64, db_index=True)
    label = models.CharField(max_length=128, blank=True)  # display snapshot
    state = models.CharField(max_length=8, choices=STATE_CHOICES)
    size_matrix = models.JSONField(default=dict, blank=True)   # {"M": true, "XL": false}
    price_band = models.JSONField(default=dict, blank=True)    # {"min": 999, "max": 2499}
    color_notes = models.JSONField(default=list, blank=True)   # ["Blue", "Black"]
    item_level = models.TextField(blank=True)                  # L2 (future)
    recorded_by = models.CharField(max_length=16, choices=RECORDED_BY, default="portal")
    valid_until = models.DateTimeField()
    superseded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["shop", "catalog_key", "valid_until"],
                name="idx_cat_latest",
                condition=models.Q(superseded_at__isnull=True),
            )
        ]

    @classmethod
    def latest_valid(cls, shop, key):
        return (
            cls.objects.filter(shop=shop, catalog_key=key, superseded_at__isnull=True, valid_until__gt=TimeHelper.now())
            .order_by("-valid_until")
            .first()
        )


class TimeHelper:
    """Tiny helper to avoid importing django.utils in two places."""

    @staticmethod
    def now():
        from django.utils import timezone

        return timezone.now()
