from django.contrib import admin

from .models import Conversation, ConversationMessage, FavoriteListing


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
