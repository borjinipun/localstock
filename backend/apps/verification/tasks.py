from celery import shared_task


@shared_task
def recompute_accuracy():
    """Rolling 30-day accuracy per shop (docs 03 §10). MVP approximation:
    correct-confirmation share from availability records closed vs reports."""

    from apps.ops.models import OpsTask
    from apps.queries.models import ReportWrongInfo
    from apps.shops.models import Shop

    offending = {}
    for report in ReportWrongInfo.objects.filter(status="open").select_related("availability_record__shop"):
        shop = report.availability_record.shop
        offending[shop.id] = offending.get(shop.id, 0) + 1
    for shop in Shop.objects.all():
        base = float(shop.accuracy_score)
        laps = offending.get(shop.id, 0)
        adjusted = max(0.5, base - 0.02 * laps) if laps else base
        if adjusted != shop.accuracy_score:
            shop.accuracy_score = adjusted
            shop.save(update_fields=["accuracy_score"])
        if laps >= 2:
            OpsTask.objects.get_or_create(kind="dispute", ref_id=shop.id,
                                          payload={"reason": "accuracy_below_threshold",
                                                   "laps": laps})
    return {"shops_reviewed": Shop.objects.count()}
