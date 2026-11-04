from django.db import models


class OpsTask(models.Model):
    """Internal queue rows (docs 02 F-O-*, docs 03 §11)."""

    KINDS = [("escalate", "escalate"), ("claim_review", "claim_review"),
             ("dispute", "dispute"), ("spot_audit", "spot_audit")]

    kind = models.CharField(max_length=16, choices=KINDS)
    ref_id = models.BigIntegerField(null=True)
    payload = models.JSONField(default=dict)
    priority = models.IntegerField(default=5)
    assigned_to = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(max_length=12, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kind}#ref{self.ref_id} {self.state}"
