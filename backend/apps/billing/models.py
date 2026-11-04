from django.db import models


class Plan(models.Model):
    code = models.SlugField(primary_key=True)
    name = models.CharField(max_length=32)
    monthly_paise = models.IntegerField()
    checks_month = models.IntegerField()
    rank_boost = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    features = models.JSONField(default=dict)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} ₹{self.monthly_paise / 100:.0f}"


class Subscription(models.Model):
    """Shop plan lifecycle docs 04 §6.2: active → past_due → suspended → cancelled.
    MVP: mock captures payments instantly; Razorpay behind env flag (OQ provider matrix)."""

    STATUSES = [("active", "active"), ("past_due", "past_due"),
                ("suspended", "suspended"), ("cancelled", "cancelled")]

    shop = models.OneToOneField("shops.Shop", on_delete=models.CASCADE, related_name="subscription")
    plan_code = models.CharField(max_length=24)
    status = models.CharField(max_length=10, choices=STATUSES, default="active")
    usage_checks = models.IntegerField(default=0)
    period_start = models.DateTimeField(auto_now_add=True)
    period_end = models.DateTimeField(null=True, blank=True)


class Payment(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="payments")
    amount_paise = models.IntegerField()
    gst_amount_paise = models.IntegerField(default=0)
    provider = models.CharField(max_length=16, default="razorpay")
    provider_ref = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=12, default="captured")
    invoice_no = models.CharField(max_length=32, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
