from django.contrib import admin

from .models import Conversation, ConversationMessage, FavoriteListing, Review


@admin.register(FavoriteListing)
class FavoriteListingAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "created_at")
    search_fields = ("user__phone", "user__username", "listing__title")


class ConversationMessageInline(admin.TabularInline):
    model = ConversationMessage
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("listing", "buyer", "seller", "updated_at")
    search_fields = ("listing__title", "buyer__phone", "seller__phone")
    inlines = [ConversationMessageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("seller", "reviewer", "order", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("seller__phone", "reviewer__phone", "comment")
