from django.db import models

from apps.core.models import TimeStamped


class Shop(models.Model):
    """Directory + operational shop record (spec 06 §2).
    Most fields simplified from the spec for MVP (lat/lng floats instead of
    PostGIS — migration to GEOGRAPHY(Point) is flagged prod work)."""

    VERTICALS = [("fashion", "fashion"), ("electronics", "electronics"), ("groceries", "groceries")]
    SOURCES = [("ops", "ops"), ("place_seed", "place_seed"), ("self_claim", "self_claim")]

    # Mock-only: scripted answering behaviour simulated by voice-svc (see docs/09 Phase 0 spike note).
    BEHAVIORS = [
        ("always_yes", "always_yes"),
        ("no_with_alternative", "no_with_alternative"),
        ("conditional", "conditional"),
        ("wa_only_yes", "wa_only_yes"),
        ("unreachable", "unreachable"),
        ("never_answer", "never_answer"),
    ]

    display_name = models.CharField(max_length=128)
    verticals = models.JSONField(default=list)
    address_text = models.TextField(blank=True)
    city = models.ForeignKey("core.City", on_delete=models.PROTECT, related_name="shops")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    google_place_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    public_phone = models.CharField(max_length=16, blank=True)      # display number
    ops_phone = models.CharField(max_length=16, unique=True, null=True, blank=True)  # verified ops number
    whatsapp_number = models.CharField(max_length=16, blank=True)
    whatsapp_linked = models.BooleanField(default=False)
    source = models.CharField(max_length=16, choices=SOURCES, default="ops")
    claimed_at = models.DateTimeField(null=True, blank=True)
    current_plan = models.CharField(max_length=16, default="free")
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.9)
    hours_text = models.CharField(max_length=64, default="10:00–20:00", blank=True)
    mock_behavior = models.CharField(max_length=24, choices=BEHAVIORS, default="always_yes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

    @property
    def is_claimed(self):
        return self.claimed_at is not None


class ContactPolicy(models.Model):
    """Shop contact rules (spec 04 §5, 03 §7)."""

    CHANNELS_ALL = ["call", "whatsapp", "sms"]

    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name="contact_policy")
    channels = models.JSONField(default=list)   # ["call","whatsapp"] — normalized in get_or_create paths
    quiet_start = models.TimeField(null=True, blank=True)
    quiet_end = models.TimeField(null=True, blank=True)
    max_daily_checks = models.IntegerField(default=8)
    opt_out = models.BooleanField(default=False)
    language_pref = models.CharField(max_length=24, default="hi")


class ClaimRequest(models.Model):
    STATUS = [("pending", "pending"), ("approved", "approved"), ("rejected", "rejected")]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="claim_requests")
    applicant_phone = models.CharField(max_length=16)
    otp_code = models.CharField(max_length=6, blank=True)
    otp_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
