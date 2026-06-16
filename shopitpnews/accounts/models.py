from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        PARENT_FARM = "parent_farm", "مزرعه مرغ مادر"
        GROW_OUT = "grow_out", "واحد پرورش"
        BROKER = "broker", "واسطه و کارگزار"

    phone = models.CharField("شماره موبایل", max_length=15, unique=True, null=True, blank=True)
    role = models.CharField("نوع فعالیت", max_length=32, choices=Role.choices, blank=True)
    is_phone_verified = models.BooleanField("تایید موبایل", default=False)
    province = models.CharField("استان", max_length=64, blank=True)
    city = models.CharField("شهر", max_length=64, blank=True)

    def __str__(self):
        return self.get_full_name() or self.phone or self.username


class OtpCode(models.Model):
    phone = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def issue(cls, phone):
        cls.objects.filter(phone=phone, used_at__isnull=True).update(used_at=timezone.now())
        return cls.objects.create(
            phone=phone,
            code=settings.DEV_OTP_CODE,
            expires_at=timezone.now() + timedelta(seconds=settings.OTP_CODE_TTL_SECONDS),
        )

    def verify(self, code):
        if self.used_at or self.expires_at < timezone.now():
            return False
        if self.code != code:
            return False
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
        return True
