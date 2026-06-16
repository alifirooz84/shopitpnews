from django.conf import settings
from django.db import models
from django.urls import reverse


class Listing(models.Model):
    class SaleType(models.TextChoices):
        IMMEDIATE = "immediate", "فروش فوری"
        FUTURE = "future", "فروش آتی"

    class Status(models.TextChoices):
        ACTIVE = "active", "فعال"
        RESERVED = "reserved", "رزرو شده"
        SOLD = "sold", "فروخته شده"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    sale_type = models.CharField(max_length=16, choices=SaleType.choices, default=SaleType.IMMEDIATE)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    breed = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    price_per_chick = models.PositiveIntegerField()
    province = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    delivery_date = models.DateField()
    health_status = models.CharField(max_length=120, default="واکسینه شده")
    parent_flock_age = models.CharField(max_length=32, default="۳۷-۵۰")
    hatch_rate_percent = models.PositiveSmallIntegerField(default=84)
    egg_weight_grams = models.PositiveSmallIntegerField(default=62)
    vaccination_status = models.CharField(max_length=120, default="کامل")
    reservation_percent = models.PositiveSmallIntegerField(default=0)
    image_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    seller_name = models.CharField(max_length=120, blank=True)
    seller_title = models.CharField(max_length=120, blank=True)
    seller_rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    seller_transactions = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "delivery_date", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("listings:detail", kwargs={"pk": self.pk})


class MarketPrice(models.Model):
    class Direction(models.TextChoices):
        UP = "up", "افزایشی"
        DOWN = "down", "کاهشی"
        FLAT = "flat", "ثابت"

    title = models.CharField(max_length=80)
    price = models.PositiveIntegerField()
    unit = models.CharField(max_length=32, default="تومان")
    direction = models.CharField(max_length=8, choices=Direction.choices, default=Direction.FLAT)
    display_order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "title"]

    def __str__(self):
        return self.title
