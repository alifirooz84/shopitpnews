from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("reports/", views.financial_report, name="financial_report"),
    path("reports.csv", views.financial_report_csv, name="financial_report_csv"),
]
