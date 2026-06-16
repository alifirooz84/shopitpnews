from django.test import TestCase
from django.urls import reverse


class PaymentHealthTests(TestCase):
    def test_payment_health(self):
        response = self.client.get(reverse("payments:health"))
        self.assertEqual(response.status_code, 200)
