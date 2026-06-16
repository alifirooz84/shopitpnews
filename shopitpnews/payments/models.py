from decimal import Decimal

from django.conf import settings
from django.db import models


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

    def __str__(self):
        return f"{self.amount} - {self.get_status_display()}"
