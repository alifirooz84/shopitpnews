from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("profile/", views.profile, name="profile"),
    path("sellers/<int:pk>/", views.seller_profile, name="seller_profile"),
    path("api/otp/request/", views.request_otp, name="request_otp"),
    path("api/otp/verify/", views.verify_otp, name="verify_otp"),
    path("api/profile/", views.save_profile, name="save_profile"),
]
