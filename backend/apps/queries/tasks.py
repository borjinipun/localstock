from celery import shared_task
from django.utils import timezone

from .models import Query


@shared_task
def match_and_execute_query(query_id: int):
    """Full pipeline for one query (docs 01 §1 'like Uber'): 
    match → instant records → dispatch wave → finalize when settled."""
    from apps.queries import matching
    from apps.verification.services import start_verification

    query = Query.objects.select_related("city").filter(id=query_id).first()
    if not query or query.status != "processing":
        return
    result = matching.build_targets(query)
    for tid in result["wave"]:
        start_verification(tid)
    finalize_if_settled(query_id)
    return result


@shared_task
def finalize_if_settled(query_id: int):
    query = Query.objects.filter(id=query_id).first()
    if not query or query.status != "processing":
        return "skipped"
    pending = query.targets.exclude(state="resolved").exists()
    if not pending:
        query.status = "completed"
        query.completed_at = timezone.now()
        query.save(update_fields=["status", "completed_at"])
    return query.status


@shared_task
def staleness_sweep():
    """Hourly: mark expired availability records (`docs 05 §7` — staleness horizon)."""
    from django.utils import timezone
    from .models import AvailabilityRecord
    qs = AvailabilityRecord.objects.filter(
        publish_state="published", freshness_at__lt=timezone.now() - timezone.timedelta(
            hours=settings_fresh_hours()))
    for r in qs:
        r.publish_state = "expired"
        r.save(update_fields=["publish_state"])
    return qs.count()


def settings_fresh_hours():
    from django.conf import settings
    return settings.FRESH_CATALOG_HOURS
