from django.contrib import admin

from .models import VerificationAttempt


@admin.register(VerificationAttempt)
class VerificationAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "target", "channel", "outcome", "reason_code", "started_at", "ended_at")
    list_filter = ("channel", "outcome")
