from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "listing", "order_type", "status", "quantity", "total_amount", "created_at")
    list_filter = ("order_type", "status", "created_at")
    search_fields = ("buyer__phone", "buyer__username", "listing__title")
