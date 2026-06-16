from django.urls import path

from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("prices/", views.market_prices, name="market_prices"),
    path("prices/<int:pk>/delete/", views.delete_market_price, name="delete_market_price"),
    path("users/", views.users, name="users"),
    path("users/<int:pk>/action/", views.user_action, name="user_action"),
    path("financial/", views.financial_reports, name="financial_reports"),
    path("financial.csv", views.financial_reports_csv, name="financial_reports_csv"),
    path("settlements/<int:pk>/paid/", views.mark_settlement_paid, name="mark_settlement_paid"),
    path("disputes/", views.disputes, name="disputes"),
    path("disputes/<int:pk>/", views.dispute_detail, name="dispute_detail"),
    path("disputes/<int:pk>/resolve/", views.resolve_dispute, name="resolve_dispute"),
]
