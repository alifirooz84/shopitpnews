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
