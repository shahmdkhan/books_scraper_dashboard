from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework.request import Request
from .models import Source, History, Detail

def get_details(request: Request):
    """
    Returns a (detail_qs, history_qs) tuple filtered by all active query params:
        domains      — comma-separated spider_name values
        min_price    — float
        max_price    — float
        condition    — comma-separated condition strings, or "All"
        days_old     — integer
        interest     — "pending" | "interested" | "not_interested"
        contact      — "true" | "false"
    """
    # Domain filter
    if domains := request.GET.get("domains", ""):
        query = Q()
        for domain in domains.split(","):
            query |= Q(spider_name=domain)
        ids = Source.objects.filter(query).values_list("spider_id", flat=True)
    else:
        ids = Source.objects.all().values_list("spider_id", flat=True)

    history = History.objects.filter(site_id__in=ids)
    detail  = Detail.objects.filter(history_id__in=history.values_list("history_id", flat=True))

    # Price filters
    if min_price := request.GET.get("min_price", None):
        detail = detail.filter(price__gte=float(min_price))
    if max_price := request.GET.get("max_price", None):
        detail = detail.filter(price__lte=float(max_price))

    # Condition filter
    if conditions := request.GET.get("condition", ""):
        if conditions != "All":
            query = Q()
            for condition in conditions.split(","):
                query |= Q(condition=condition)
            detail = detail.filter(query)

    # Days-old filter
    if (days_old_raw := request.GET.get("days_old")) is not None:
        days_old = int(days_old_raw)
        cutoff_date = timezone.now().date() - timedelta(days=days_old)
        if days_old == 1:
            detail = detail.filter(first_seen=cutoff_date + timedelta(days=1))
        else:
            detail = detail.filter(first_seen__gte=cutoff_date)

    # Interest filter
    # Interest filter
    if interest := request.GET.get("interest", ""):
        valid = {Detail.PENDING, Detail.INTERESTED, Detail.NOT_INTERESTED}
        if interest in valid:
            detail = detail.filter(interest=interest)

    # 👇 Move this outside – it's independent of the "interest" parameter
    if request.GET.get("exclude_not_interested") == "true":
        detail = detail.exclude(interest=Detail.NOT_INTERESTED)
    #    old one
    # if interest := request.GET.get("interest", ""):
    #     valid = {Detail.PENDING, Detail.INTERESTED, Detail.NOT_INTERESTED}
    #     if interest in valid:
    #         detail = detail.filter(interest=interest)


    # Contact filter
    if contact := request.GET.get("contact", ""):
        if contact.lower() == "true":
            detail = detail.filter(contact=True)
        elif contact.lower() == "false":
            detail = detail.filter(contact=False)

    return detail, history

def update_interest(detail_id: int, interest_value: str) -> Detail:
    detail = Detail.objects.get(pk=detail_id)
    detail.interest = interest_value
    detail.save(update_fields=["interest"])
    return detail

def update_contact(detail_id: int, contact_value: bool) -> Detail:
    detail = Detail.objects.get(pk=detail_id)
    detail.contact = contact_value
    detail.save(update_fields=["contact"])
    return detail
