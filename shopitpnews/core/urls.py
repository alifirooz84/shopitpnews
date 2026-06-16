from django.conf import settings
from django.conf.urls.static import static
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
    path("management/", include("backoffice.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
