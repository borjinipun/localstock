from rest_framework import serializers

from apps.catalog.models import CatalogState
from apps.shops.models import ClaimRequest, ContactPolicy, Shop


class ContactPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPolicy
        fields = ["channels", "quiet_start", "quiet_end", "max_daily_checks", "opt_out", "language_pref"]


class ShopPublicSerializer(serializers.ModelSerializer):
    city_code = serializers.CharField(source="city.code", read_only=True)

    class Meta:
        model = Shop
        fields = [
            "id", "display_name", "verticals", "address_text", "city_code",
            "lat", "lng", "public_phone", "current_plan", "accuracy_score",
            "hours_text", "is_claimed",
        ]
        read_only_fields = fields


class CatalogRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogState
        fields = ["id", "catalog_key", "label", "state", "size_matrix", "price_band",
                  "color_notes", "recorded_by", "valid_until", "created_at"]
        read_only_fields = ["id", "recorded_by", "valid_until", "created_at"]


class InboxTargetSerializer(serializers.Serializer):
    """Inquiry as the shop sees it (spec 04 §4)."""

    target_id = serializers.IntegerField(source="id")
    query_id = serializers.IntegerField()
    raw_text = serializers.CharField(source="query.raw_text")
    parsed_intent = serializers.JSONField(source="query.parsed_intent")
    created_at = serializers.DateTimeField(source="query.created_at")
    state = serializers.CharField()


class ClaimLookupSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    shop_id = serializers.IntegerField()
    shop_name = serializers.CharField()
    # Dev convenience — in production this code is delivered via Call/WA/SMS only (docs 04 §2).
    dev_otp = serializers.CharField()


class ClaimVerifySerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    code = serializers.CharField()
