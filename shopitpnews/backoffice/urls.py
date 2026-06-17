from django.urls import path

from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("prices/", views.market_prices, name="market_prices"),
    path("prices/<int:pk>/delete/", views.delete_market_price, name="delete_market_price"),
    path("users/", views.users, name="users"),
    path("verification/", views.verification_requests, name="verification_requests"),
    path("verification/<int:pk>/", views.verification_detail, name="verification_detail"),
    path("verification/<int:pk>/review/", views.review_verification, name="review_verification"),
    path("users/<int:pk>/action/", views.user_action, name="user_action"),
    path("newsletters/", views.newsletters, name="newsletters"),
    path("financial/", views.financial_reports, name="financial_reports"),
    path("financial.csv", views.financial_reports_csv, name="financial_reports_csv"),
    path("settlements/<int:pk>/paid/", views.mark_settlement_paid, name="mark_settlement_paid"),
    path("disputes/", views.disputes, name="disputes"),
    path("disputes/<int:pk>/", views.dispute_detail, name="dispute_detail"),
    path("disputes/<int:pk>/message/", views.add_dispute_message, name="add_dispute_message"),
    path("disputes/<int:pk>/resolve/", views.resolve_dispute, name="resolve_dispute"),
]
