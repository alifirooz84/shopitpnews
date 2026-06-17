from django.conf import settings
from django.db import models
from django.urls import reverse


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


class PurchaseOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پاسخ"
        ACCEPTED = "accepted", "پذیرفته شده"
        REJECTED = "rejected", "رد شده"
        CANCELLED = "cancelled", "لغو شده"

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchase_offers")
    listing = models.ForeignKey("listings.Listing", on_delete=models.PROTECT, related_name="purchase_offers")
    quantity = models.PositiveIntegerField()
    proposed_unit_price = models.PositiveIntegerField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="source_offer")
    seller_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"پیشنهاد #{self.pk} - {self.listing}"

    @property
    def total_amount(self):
        return self.quantity * self.proposed_unit_price

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    def get_absolute_url(self):
        return reverse("orders:offer_detail", kwargs={"pk": self.pk})


class DisputeCase(models.Model):
    class Reason(models.TextChoices):
        DELAY = "delay", "تأخیر در تحویل"
        QUALITY = "quality", "مغایرت کیفیت/سلامت"
        QUANTITY = "quantity", "مغایرت تعداد"
        CANCELLATION = "cancellation", "لغو یک‌طرفه"
        OTHER = "other", "سایر موارد"

    class Status(models.TextChoices):
        OPEN = "open", "در حال بررسی"
        RELEASED = "released", "مختومه با تسویه فروشنده"
        REFUNDED = "refunded", "مختومه با بازگشت وجه"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="dispute_case")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_disputes")
    reason = models.CharField(max_length=24, choices=Reason.choices, default=Reason.OTHER)
    description = models.TextField(blank=True)
    evidence = models.FileField(upload_to="dispute-evidence/", blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    resolution_note = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resolved_disputes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"اختلاف سفارش #{self.order_id}"


class DisputeMessage(models.Model):
    dispute = models.ForeignKey(DisputeCase, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="dispute_messages")
    body = models.TextField()
    attachment = models.FileField(upload_to="dispute-messages/", blank=True)
    is_staff_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"پیام اختلاف #{self.dispute_id}"
