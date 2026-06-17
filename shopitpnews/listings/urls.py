from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("", views.listing_list, name="list"),
    path("mine/", views.my_listings, name="mine"),
    path("new/", views.listing_create, name="create"),
    path("<int:pk>/", views.listing_detail, name="detail"),
    path("<int:pk>/edit/", views.listing_update, name="edit"),
    path("<int:pk>/delete/", views.listing_delete, name="delete"),
]
