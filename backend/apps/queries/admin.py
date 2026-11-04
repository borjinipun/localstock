from django.contrib import admin

from .models import AvailabilityRecord, Query, QueryTarget, ReportWrongInfo


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ("id", "raw_text", "city", "status", "created_at")
    list_filter = ("city", "status")


@admin.register(QueryTarget)
class QueryTargetAdmin(admin.ModelAdmin):
    list_display = ("id", "query", "shop", "state", "outcome", "reason_code", "rank_final")
    list_filter = ("state",)


@admin.register(AvailabilityRecord)
class AvailabilityRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "query", "state", "evidence_kind", "freshness_at", "publish_state")
    list_filter = ("evidence_kind", "publish_state")


admin.site.register(ReportWrongInfo, list_display=("reason", "status", "created_at"))
