from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class City(models.Model):
    """Seed city. Center used for the web-app default map location (spec 01 §4)."""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=64)
    center_lat = models.DecimalField(max_digits=9, decimal_places=6)
    center_lng = models.DecimalField(max_digits=9, decimal_places=6)
    is_live = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Consent(models.Model):
    """Buyer consent artefacts (dpdp, spec 05 §4 / 02 F-C-08)."""

    SCOPES = [("notify", "notify"), ("share_name", "share_name")]
    phone = models.CharField(max_length=16, null=True, blank=True)
    scope = models.CharField(max_length=24, choices=SCOPES)
    artefact = models.TextField()  # exact consent copy shown
    given_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
