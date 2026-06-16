from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("listings/<int:listing_id>/create/", views.create_order, name="create"),
]
