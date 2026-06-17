from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "اطلاع‌رسانی"
        SUCCESS = "success", "موفق"
        WARNING = "warning", "هشدار"
        ERROR = "error", "خطا"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=160)
    body = models.TextField()
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INFO)
    link_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def __str__(self):
        return self.title


class MessageOutbox(models.Model):
    class Channel(models.TextChoices):
        SYSTEM = "system", "اعلان داخل سایت"
        SMS = "sms", "پیامک"
        NEWSLETTER = "newsletter", "خبرنامه"

    class Status(models.TextChoices):
        QUEUED = "queued", "در صف ارسال"
        SENT = "sent", "ارسال شده"
        FAILED = "failed", "ناموفق"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="message_outbox")
    recipient_phone = models.CharField(max_length=15, blank=True)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    subject = models.CharField(max_length=160)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    provider_reference = models.CharField(max_length=120, blank=True)
    provider_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_sent(self, provider_reference="", provider_response=""):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.provider_reference = provider_reference
        self.provider_response = provider_response
        self.save(update_fields=["status", "sent_at", "provider_reference", "provider_response"])

    def __str__(self):
        return f"{self.get_channel_display()} - {self.subject}"
