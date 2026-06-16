from django.conf import settings
from django.db import models


class Order(models.Model):
    class OrderType(models.TextChoices):
        INSTANT = "instant", "خرید آنی"
        PREORDER = "preorder", "پیش‌خرید"
        OFFER = "offer", "پیشنهاد قیمت"

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "در انتظار پرداخت"
        PAID_HELD = "paid_held", "پرداخت امن"
        DELIVERED = "delivered", "تحویل شده"
        DISPUTED = "disputed", "دارای اختلاف"
        CANCELLED = "cancelled", "لغو شده"

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    listing = models.ForeignKey("listings.Listing", on_delete=models.PROTECT, related_name="orders")
    order_type = models.CharField(max_length=16, choices=OrderType.choices)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PAID_HELD)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()
    total_amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_order_type_display()} - {self.listing}"

    @property
    def is_active_escrow(self):
        return self.status == self.Status.PAID_HELD

    @property
    def can_be_cancelled(self):
        return self.status in {self.Status.PENDING_PAYMENT, self.Status.PAID_HELD}

    @property
    def can_be_disputed(self):
        return self.status == self.Status.PAID_HELD

    @property
    def can_confirm_delivery(self):
        return self.status == self.Status.PAID_HELD
