from rest_framework import serializers

from .models import AvailabilityRecord, Query, QueryTarget


class ShopLiteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    distance_km = serializers.SerializerMethodField()
    public_phone = serializers.CharField()
    hours_text = serializers.CharField()
    current_plan = serializers.CharField()

    def get_distance_km(self, obj):
        ctx = self.context or {}
        tgt = ctx.get("target_distances", {}).get(obj.id)
        return tgt


class AvailabilityRecordSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.display_name", read_only=True)
    shop_phone = serializers.CharField(source="shop.public_phone", read_only=True)
    shop_hours = serializers.CharField(source="shop.hours_text", read_only=True)

    class Meta:
        model = AvailabilityRecord
        fields = ["id", "shop_id", "shop_name", "shop_phone", "shop_hours", "query_id",
                  "state", "sizes", "colors", "price_text", "condition_text",
                  "evidence_kind", "transcript_snippet", "freshness_at", "publish_state"]


class QueryTargetLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryTarget
        fields = ["id", "shop_id", "state", "outcome", "reason_code", "rank_final"]


class QueryDetailSerializer(serializers.ModelSerializer):
    parsed = serializers.SerializerMethodField()
    availability = AvailabilityRecordSerializer(source="availability_records", many=True, read_only=True)
    targets = QueryTargetLiteSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = ["id", "raw_text", "parsed_intent", "status", "radius_m",
                  "share_name", "spot_check", "completed_at", "parsed", "availability", "targets"]

    def get_parsed(self, obj):
        return obj.parsed_intent


class QueryCreatedSerializer(serializers.Serializer):
    """Response shape of docs 07 API-2."""
    query_id = serializers.IntegerField()
    status = serializers.CharField()
    instant_results = AvailabilityRecordSerializer(many=True)
    checked_wave = serializers.DictField()
    stream_url = serializers.CharField()
