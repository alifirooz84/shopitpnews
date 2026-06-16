from django.contrib import admin
from django.urls import include, path

from listings.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("listings/", include("listings.urls")),
    path("orders/", include("orders.urls")),
    path("payments/", include("payments.urls")),
]
