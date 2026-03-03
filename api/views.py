from collections import defaultdict

from django.db.models import Avg, Min, Max, Count
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Source, Detail
from .serializers import DetailSerializer, InterestUpdateSerializer
from .services import get_details, update_interest


# ─────────────────────────────────────────────────────────────
# Auth guard helper  (works correctly inside @api_view)
# ─────────────────────────────────────────────────────────────
def require_login(request):
    """
    Return a redirect to /login/ when the user is not authenticated,
    otherwise return None so the view proceeds normally.
    """
    if not request.user or not request.user.is_authenticated:
        return redirect(f"/login/?next={request.path}")
    return None


# ─────────────────────────────────────────────────────────────
# Auth views  (plain Django — intentionally NOT @api_view)
# ─────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect("/api/dashboard/")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get("next", "/api/dashboard/")
            return redirect(next_url)
        return render(request, "login.html", {"form": form, "error": "Invalid username or password."})

    return render(request, "login.html", {"form": AuthenticationForm()})


def logout_view(request):
    logout(request)
    return redirect("/login/")


# ─────────────────────────────────────────────────────────────
# App views  (all protected)
# ─────────────────────────────────────────────────────────────
@api_view(["GET"])
def home(request):
    guard = require_login(request)
    if guard:
        return guard
    return redirect("/api/dashboard/")


@api_view(["GET"])
def dashboard_view(request):
    guard = require_login(request)
    if guard:
        return guard
    return render(request, "dashboard.html")


@api_view(["GET"])
def market_place_names(request):
    """
    Returns a dict grouping spider names by their base marketplace name.
    e.g. {"wallapop": ["libros", "comics"], "vinted": ["libros"]}
    """
    guard = require_login(request)
    if guard:
        return guard

    groups = defaultdict(list)
    for name in Source.objects.all().values_list("spider_name", flat=True):
        base = next(iter(name.split("_")))
        groups[base].append(name.replace(base + "_", ""))

    return Response(groups)


@api_view(["GET"])
def price_range_of_books(request):
    """
    Returns {min_price, max_price} across the current filter set.
    Accepts all filters supported by get_details().
    """
    guard = require_login(request)
    if guard:
        return guard

    detail, _ = get_details(request=request)
    return Response({
        "min_price": detail.order_by("price").first().price,
        "max_price": detail.order_by("-price").first().price,
    })


@api_view(["GET"])
def conditions_of_books(request):
    """
    Returns a sorted list of distinct condition strings (+ 'All') across
    the current filter set.
    """
    guard = require_login(request)
    if guard:
        return guard

    detail, _ = get_details(request=request)
    conditions = list(detail.values_list("condition", flat=True).distinct())
    conditions.append("All")
    conditions.sort()
    return Response(conditions)


@api_view(["GET"])
def main_stats(request):
    """
    Returns aggregate stats for the current filter set:
        Total Books, Unique Sellers, Average Price,
        Rotation Rate, Hot Books, Sold Books
    """
    guard = require_login(request)
    if guard:
        return guard

    try:
        detail, _ = get_details(request=request)
        total = detail.count()
        return Response({
            "Total Books":    total,
            "Unique Sellers": detail.values_list("seller", flat=True).distinct().count(),
            "Average Price":  round((detail.aggregate(avg_price=Avg("price")).get("avg_price") or 0), 2),
            "Rotation Rate":  f"{round((detail.filter(availability=False).count() / (total or 1)) * 100, 2)} %",
            "Hot Books":      detail.filter(availability=True).count(),
            "Sold Books":     detail.filter(availability=False).count(),
        })
    except Exception:
        return Response({
            "Total Books": 0, "Unique Sellers": 0, "Average Price": 0,
            "Rotation Rate": "0 %", "Hot Books": 0, "Sold Books": 0,
        })


@api_view(["GET"])
def all_filtered_results(request):
    guard = require_login(request)
    if guard:
        return guard

    group_by = request.GET.get("group_by", "isbn")
    detail, _ = get_details(request=request)
    available_detail = detail.filter(availability=True)

    if group_by in ("seller", "isbn"):
        # Pre‑compute aggregates for available books
        available_agg = available_detail.values(group_by).annotate(
            avg_price=Avg("price"),
            min_price=Min("price"),
            max_price=Max("price"),
            available_count=Count("detail_id")
        )
        agg_dict = {item[group_by]: item for item in available_agg}

        # Pre‑compute sold counts per group
        sold_agg = detail.filter(availability=False).values(group_by).annotate(
            sold_count=Count("detail_id")
        )
        sold_dict = {item[group_by]: item["sold_count"] for item in sold_agg}

        # Group items
        grouped_data = defaultdict(list)
        for obj in available_detail:
            key = getattr(obj, group_by) or "unknown"
            grouped_data[key].append(obj)

        response = []
        for key, items in grouped_data.items():
            agg = agg_dict.get(key, {})
            total_available = agg.get("available_count", len(items))
            sold_count = sold_dict.get(key, 0)

            response.append({
                group_by.capitalize(): key,
                "Available Books": total_available,
                "Books Sold": sold_count,
                "Average Rotation (%)": f"{round((sold_count / (total_available or 1)) * 100, 2)}%",
                "Average Price": round(agg.get("avg_price") or 0, 2),
                "Minimum Price": round(agg.get("min_price") or 0, 2),
                "Maximum Price": round(agg.get("max_price") or 0, 2),
                "results": DetailSerializer(items, many=True).data,
            })

        return Response(response)

    return Response(DetailSerializer(detail, many=True).data)

# @api_view(["GET"])
# def all_filtered_results(request):
#     """
#     Returns results grouped by 'isbn' (default) or 'seller'.
#     Optimized to use aggregation for per‑group stats.
#     """
#     guard = require_login(request)
#     if guard:
#         return guard
#
#     group_by = request.GET.get("group_by", "isbn")
#     detail, _ = get_details(request=request)          # filtered queryset
#     available_detail = detail.filter(availability=True)
#
#     if group_by in ("seller", "isbn"):
#         # ----- 1. Pre‑compute aggregates for available books (single query) -----
#         available_agg = available_detail.values(group_by).annotate(
#             avg_price=Avg("price"),
#             min_price=Min("price"),
#             max_price=Max("price"),
#             available_count=Count("detail_id")
#         )
#         agg_dict = {item[group_by]: item for item in available_agg}
#
#         # ----- 2. Pre‑compute sold counts per group (single query) -----
#         sold_agg = detail.filter(availability=False).values(group_by).annotate(
#             sold_count=Count("detail_id")
#         )
#         sold_dict = {item[group_by]: item["sold_count"] for item in sold_agg}
#
#         # ----- 3. Group items (one loop, no extra queries) -----
#         grouped_data = defaultdict(list)
#         for obj in available_detail:
#             key = getattr(obj, group_by) or "unknown"
#             grouped_data[key].append(obj)
#
#         # ----- 4. Build response using pre‑computed aggregates -----
#         response = []
#         for key, items in grouped_data.items():
#             agg = agg_dict.get(key, {})
#             total_available = agg.get("available_count", len(items))   # fallback
#             sold_count = sold_dict.get(key, 0)
#
#             response.append({
#                 group_by.capitalize(): key,
#                 "Available Books": total_available,
#                 "Books Sold": sold_count,
#                 "Average Rotation (%)": f"{round((sold_count / (total_available or 1)) * 100, 2)}%",
#                 "Average Price": round(agg.get("avg_price") or 0, 2),
#                 "Minimum Price": round(agg.get("min_price") or 0, 2),
#                 "Maximum Price": round(agg.get("max_price") or 0, 2),
#                 "results": DetailSerializer(items, many=True).data,
#             })
#
#         return Response(response)
#
#     # Fallback – no grouping
#     return Response(DetailSerializer(detail, many=True).data)


# ─────────────────────────────────────────────────────────────
# Interest flag endpoint
# ─────────────────────────────────────────────────────────────
@api_view(["PATCH"])
def update_interest_view(request, detail_id: int):
    """
    PATCH /api/interest/<detail_id>/

    Body (JSON):
        { "interest": "interested" }        ← star activated
        { "interest": "not_interested" }    ← dislike / X clicked
        { "interest": "pending" }           ← reset to default

    Returns:
        200  { "detail_id": <int>, "interest": "<value>" }
        400  validation errors
        404  detail not found
    """
    guard = require_login(request)
    if guard:
        return guard

    serializer = InterestUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        detail = update_interest(
            detail_id=detail_id,
            interest_value=serializer.validated_data["interest"],
        )
    except Detail.DoesNotExist:
        return Response({"error": "Detail not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {"detail_id": detail.detail_id, "interest": detail.interest},
        status=status.HTTP_200_OK,
    )

@api_view(["PATCH"])
def update_contact_view(request, detail_id: int):
    """
    PATCH /api/contact/<detail_id>/
    Body: { "contact": true }  or  { "contact": false }
    """
    guard = require_login(request)
    if guard:
        return guard

    contact_value = request.data.get("contact")
    if contact_value is None or not isinstance(contact_value, bool):
        return Response(
            {"error": "contact must be a boolean."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        detail = Detail.objects.get(pk=detail_id)
        detail.contact = contact_value
        detail.save(update_fields=["contact"])
        return Response(
            {"detail_id": detail.detail_id, "contact": detail.contact},
            status=status.HTTP_200_OK
        )
    except Detail.DoesNotExist:
        return Response(
            {"error": "Detail not found."},
            status=status.HTTP_404_NOT_FOUND
        )