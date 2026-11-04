from django.conf import settings
from django.db import models

from apps.core.models import TimeStamped


class Query(TimeStamped):
    """One user intent (e.g. "blue dress medium size") + its verification wave."""

    parsed_intent = models.JSONField(default=dict)      # item/color/size/brand/price/confidence
    raw_text = models.TextField()                        # as typed, verbatim
    user_phone = models.CharField(max_length=16, null=True, blank=True)  # null → guest
    city = models.ForeignKey("core.City", on_delete=models.PROTECT, related_name="queries")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_m = models.IntegerField(default=3000)
    share_name = models.BooleanField(default=False)      # buyer identity revealed to shops
    notify_via = models.JSONField(default=list, blank=True)     # ["whatsapp","sms"] per F-C-05
    budget_paise = models.IntegerField(default=settings.QUERY_BUDGET_PAISE)
    spot_check = models.BooleanField(default=False)     # even when catalog has 5+ instant hits
    status = models.CharField(max_length=12, default="processing")
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"q#{self.id} {self.raw_text[:40]}"


class QueryTarget(models.Model):
    """A shop included in a query's candidate set (docs 02 F-M-02)."""

    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name="targets")
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="query_hits")
    match_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    rank_final = models.IntegerField(null=True, blank=True)
    channel_used = models.CharField(max_length=16, default="call")
    state = models.CharField(max_length=16, default="queued")           # docs 03 §12
    outcome = models.CharField(max_length=32, null=True, blank=True)    # canonical (docs 03 §2)
    reason_code = models.CharField(max_length=64, null=True, blank=True)
    contact_decision = models.JSONField(default=dict, blank=True)       # logged channel logic
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"t#{self.id} q#{self.query_id} → shop#{self.shop_id}"

    @property
    def resolved(self):
        return self.state == "resolved"


class AvailabilityRecord(models.Model):
    """What the user-facing surface consumes — evidence-denormalized (docs 06 §2)."""

    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="availability_records")
    query = models.ForeignKey(Query, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="availability_records")
    item_intent = models.JSONField(null=True, blank=True)   # matched chips snapshot
    state = models.CharField(max_length=32)                 # canonical vocabulary
    sizes = models.JSONField(default=list, blank=True)
    colors = models.JSONField(default=list, blank=True)
    price_text = models.CharField(max_length=64, blank=True, default="")
    condition_text = models.CharField(max_length=128, blank=True, default="")
    evidence_kind = models.CharField(max_length=16)              # docs 03 §2
    transcript_snippet = models.TextField(blank=True)
    freshness_at = models.DateTimeField()                          # when the fact held true
    publish_state = models.CharField(max_length=12, default="hidden")  # hidden|published|expired
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-freshness_at"]

    def __str__(self):
        return f"av#{self.id} shop#{self.shop_id} {self.state}"


class ReportWrongInfo(models.Model):
    STATUS = [("open", "open"), ("resolved", "resolved"), ("rejected", "rejected")]

    availability_record = models.ForeignKey(AvailabilityRecord, on_delete=models.CASCADE,
                                            related_name="reports")
    reason = models.CharField(max_length=64)
    detail = models.TextField(blank=True)
    status = models.CharField(max_length=8, choices=STATUS, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
