from django.test import TestCase
from django.urls import reverse

from .models import OtpCode, User


class OtpFlowTests(TestCase):
    def test_request_and_verify_otp(self):
        response = self.client.post(reverse("accounts:request_otp"), data={"phone": "09123456789"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OtpCode.objects.filter(phone="09123456789").exists())

        response = self.client.post(reverse("accounts:verify_otp"), data={"phone": "09123456789", "code": "123456"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_profile_form_updates_user(self):
        user = User.objects.create_user(username="09120000003", phone="09120000003")
        self.client.force_login(user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "علی",
                "last_name": "رضایی",
                "role": User.Role.GROW_OUT,
                "province": "تهران",
                "city": "ورامین",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.GROW_OUT)
        self.assertEqual(user.city, "ورامین")


class SellerProfileTests(TestCase):
    def test_seller_profile_shows_active_listings(self):
        from datetime import timedelta
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from listings.models import Listing

        seller = get_user_model().objects.create_user(username="seller-profile", phone="09125555555")
        Listing.objects.create(
            seller=seller,
            title="آگهی پروفایل فروشنده",
            breed="آرین",
            quantity=100,
            price_per_chick=18000,
            province="مازندران",
            city="بابل",
            delivery_date=timezone.localdate() + timedelta(days=2),
        )
        response = self.client.get(reverse("accounts:seller_profile", args=[seller.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "آگهی پروفایل فروشنده")


class VerificationRequestTests(TestCase):
    def test_user_can_submit_verification_request(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        user = User.objects.create_user(username="verify-user", phone="09129991111")
        self.client.force_login(user)
        document = SimpleUploadedFile("doc.txt", b"document", content_type="text/plain")
        response = self.client.post(
            reverse("accounts:verification"),
            {
                "national_id": "1234567890",
                "business_name": "فارم تست",
                "business_address": "مازندران آمل",
                "document": document,
            },
        )
        self.assertRedirects(response, reverse("accounts:verification"))
        self.assertTrue(user.verification_requests.filter(business_name="فارم تست").exists())
