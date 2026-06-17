from django.contrib import admin

from .models import Payment, Settlement, Wallet, WalletTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "status", "commission_percent", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order__buyer__phone", "order__listing__title", "provider_reference")


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("id", "seller", "gross_amount", "commission_amount", "net_amount", "status", "created_at", "paid_at")
    list_filter = ("status", "created_at", "paid_at")
    search_fields = ("seller__phone", "seller__username", "payment__order__listing__title")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__phone", "user__username")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "balance_after", "created_at")
    list_filter = ("transaction_type", "created_at")
    search_fields = ("wallet__user__phone", "description")
