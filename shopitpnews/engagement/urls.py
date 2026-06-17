from django.urls import path

from . import views

app_name = "engagement"

urlpatterns = [
    path("favorites/", views.favorites, name="favorites"),
    path("listings/<int:listing_id>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("conversations/", views.conversations, name="conversations"),
    path("conversations/<int:pk>/", views.conversation_detail, name="conversation_detail"),
    path("conversations/<int:pk>/message/", views.add_message, name="add_message"),
    path("listings/<int:listing_id>/contact/", views.contact_seller, name="contact_seller"),
]
