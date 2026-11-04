from django.db import models

from apps.queries.models import QueryTarget


class VerificationAttempt(models.Model):
    """One live contact attempt against a target (docs 06 §2)."""

    CHANNELS = [("call", "call"), ("whatsapp", "whatsapp"), ("sms", "sms"),
                ("inbox", "inbox"), ("human", "human")]

    target = models.ForeignKey(QueryTarget, on_delete=models.CASCADE, related_name="attempts")
    channel = models.CharField(max_length=16, choices=CHANNELS)
    provider_call_id = models.CharField(max_length=64, blank=True)
    template_id = models.CharField(max_length=64, blank=True)
    provider_events = models.JSONField(default=list, blank=True)   # raw webhook trail
    transcript = models.TextField(blank=True)
    asr_confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    nlu_schema = models.JSONField(null=True, blank=True)
    outcome = models.CharField(max_length=32, blank=True)          # canonical (docs 03 §2)
    reason_code = models.CharField(max_length=64, blank=True)
    recording_s3_key = models.CharField(max_length=256, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"attempt#{self.id} t#{self.target_id} {self.channel} → {self.outcome or '…'}"
