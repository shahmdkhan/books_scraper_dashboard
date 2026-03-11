from django.urls import path

from .views import (
    market_place_names,
    conditions_of_books,
    main_stats,
    price_range_of_books,
    all_filtered_results,
    dashboard_view,
    update_interest_view,
    update_contact_view
)

urlpatterns = [
    path("market_place_names/",   market_place_names,   name="market_place_names"),
    path("price_range_of_books/", price_range_of_books, name="price_range_of_books"),
    path("conditions_of_books/",  conditions_of_books,  name="conditions_of_books"),
    path("main_stats/",           main_stats,           name="main_stats"),
    path("all_filtered_results/", all_filtered_results, name="all_filtered_results"),
    path("dashboard/",            dashboard_view,       name="dashboard_view"),
    path("interest/<int:detail_id>/", update_interest_view, name="update_interest"),
    path("contact/<int:detail_id>/", update_contact_view, name="update_contact"),
]