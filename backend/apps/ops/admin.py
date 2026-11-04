from django.contrib import admin

from .models import OpsTask


@admin.register(OpsTask)
class OpsTaskAdmin(admin.ModelAdmin):
    list_display = ("kind", "ref_id", "priority", "assigned_to", "state", "created_at")
    list_filter = ("kind", "state")
