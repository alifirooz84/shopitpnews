from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Payment(models.Model):
    class Status(models.TextChoices):
        HELD = "held", "نگهداری امن"
        RELEASED = "released", "تسویه شده"
        REFUNDED = "refunded", "بازگشت وجه"

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="payment")
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.HELD)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=settings.PLATFORM_COMMISSION_PERCENT)
    provider_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def commission_amount(self):
        return int(Decimal(self.amount) * self.commission_percent / Decimal("100"))

    @property
    def seller_amount(self):
        return self.amount - self.commission_amount

    def create_settlement(self):
        if self.status != self.Status.RELEASED:
            return None
        settlement, _ = Settlement.objects.get_or_create(
            payment=self,
            defaults={
                "seller": self.order.listing.seller,
                "gross_amount": self.amount,
                "commission_amount": self.commission_amount,
                "net_amount": self.seller_amount,
            },
        )
        return settlement

    def __str__(self):
        return f"{self.amount} - {self.get_status_display()}"


class Settlement(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار واریز"
        PAID = "paid", "واریز شده"

    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="settlement")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="settlements")
    gross_amount = models.PositiveIntegerField()
    commission_amount = models.PositiveIntegerField()
    net_amount = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_paid(self, notes=""):
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        if notes:
            self.notes = notes
        self.save(update_fields=["status", "paid_at", "notes"])

    def __str__(self):
        return f"{self.seller} - {self.net_amount}"
