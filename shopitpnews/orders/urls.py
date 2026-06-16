from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("<int:pk>/confirm-delivery/", views.confirm_delivery, name="confirm_delivery"),
    path("<int:pk>/cancel/", views.cancel_order, name="cancel"),
    path("<int:pk>/dispute/", views.report_dispute, name="dispute"),
    path("listings/<int:listing_id>/create/", views.create_order, name="create"),
]
