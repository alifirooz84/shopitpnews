from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("", views.listing_list, name="list"),
    path("<int:pk>/", views.listing_detail, name="detail"),
]
