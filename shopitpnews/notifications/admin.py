from django.contrib import admin

from .models import MessageOutbox, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "level", "is_read", "created_at")
    list_filter = ("level", "is_read", "created_at")
    search_fields = ("recipient__phone", "recipient__username", "title", "body")


@admin.register(MessageOutbox)
class MessageOutboxAdmin(admin.ModelAdmin):
    list_display = ("channel", "recipient", "recipient_phone", "subject", "status", "created_at", "sent_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("recipient__phone", "recipient_phone", "subject", "body")
