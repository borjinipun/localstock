from django.contrib import admin

from .models import ClaimRequest, ContactPolicy, Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("display_name", "city", "current_plan", "is_claimed", "verticals", "accuracy_score")
    list_filter = ("city", "current_plan", "source")
    search_fields = ("display_name", "public_phone", "ops_phone")


admin.site.register(ContactPolicy)
admin.site.register(ClaimRequest, list_display=("shop", "applicant_phone", "status", "otp_verified"))
