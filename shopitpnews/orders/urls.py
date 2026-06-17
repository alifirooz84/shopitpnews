from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("offers/", views.offer_list, name="offer_list"),
    path("offers/<int:pk>/", views.offer_detail, name="offer_detail"),
    path("offers/<int:pk>/accept/", views.accept_offer, name="accept_offer"),
    path("offers/<int:pk>/reject/", views.reject_offer, name="reject_offer"),
    path("offers/<int:pk>/cancel/", views.cancel_offer, name="cancel_offer"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("<int:pk>/confirm-delivery/", views.confirm_delivery, name="confirm_delivery"),
    path("<int:pk>/cancel/", views.cancel_order, name="cancel"),
    path("<int:pk>/dispute/", views.report_dispute, name="dispute"),
    path("disputes/<int:pk>/message/", views.add_dispute_message, name="add_dispute_message"),
    path("listings/<int:listing_id>/create/", views.create_order, name="create"),
    path("listings/<int:listing_id>/offers/create/", views.create_offer, name="create_offer"),
]
