from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "status", "commission_percent", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order__buyer__phone", "order__listing__title", "provider_reference")
