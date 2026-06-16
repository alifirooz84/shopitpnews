from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import OtpCode, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("اطلاعات بازار", {"fields": ("phone", "role", "is_phone_verified", "province", "city")}),
    )
    list_display = ("username", "phone", "role", "is_phone_verified", "is_staff")
    search_fields = ("username", "phone", "first_name", "last_name")


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "created_at", "expires_at", "used_at")
    search_fields = ("phone",)
