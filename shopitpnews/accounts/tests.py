from django.test import TestCase
from django.urls import reverse

from .models import OtpCode


class OtpFlowTests(TestCase):
    def test_request_and_verify_otp(self):
        response = self.client.post(reverse("accounts:request_otp"), data={"phone": "09123456789"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OtpCode.objects.filter(phone="09123456789").exists())

        response = self.client.post(reverse("accounts:verify_otp"), data={"phone": "09123456789", "code": "123456"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
