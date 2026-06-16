from django.contrib import admin

from .models import Listing, MarketPrice


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "province", "city", "quantity", "price_per_chick", "status", "delivery_date")
    list_filter = ("status", "sale_type", "province", "breed", "is_verified", "is_featured")
    search_fields = ("title", "description", "breed", "province", "city")


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "unit", "direction", "display_order", "updated_at")
    list_editable = ("display_order",)
