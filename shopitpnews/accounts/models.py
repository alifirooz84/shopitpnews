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
    is_activity_verified = models.BooleanField("تأیید فعالیت", default=False)
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


class VerificationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار بررسی"
        APPROVED = "approved", "تأیید شده"
        REJECTED = "rejected", "رد شده"

    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_requests")
    national_id = models.CharField("کد ملی/شناسه", max_length=20)
    business_name = models.CharField("نام فارم/واحد فعالیت", max_length=160)
    business_address = models.TextField("آدرس واحد فعالیت")
    document = models.FileField("مدرک هویتی/فعالیت", upload_to="verification-documents/")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_verification_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant} - {self.get_status_display()}"
