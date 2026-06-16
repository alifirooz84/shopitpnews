from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing
from payments.models import Payment

from .models import Order


class OrderFlowTests(TestCase):
    def test_create_order_creates_held_payment(self):
        user_model = get_user_model()
        seller = user_model.objects.create_user(username="seller", phone="09120000001")
        buyer = user_model.objects.create_user(username="buyer", phone="09120000002")
        listing = Listing.objects.create(
            seller=seller,
            title="جوجه آرین",
            breed="آرین",
            quantity=10,
            price_per_chick=1000,
            province="گلستان",
            city="گرگان",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(buyer)
        response = self.client.post(reverse("orders:create", args=[listing.pk]), {"quantity": 3, "order_type": "instant"})
        self.assertRedirects(response, reverse("orders:list"))
        order = Order.objects.get()
        self.assertEqual(order.total_amount, 3000)
        self.assertEqual(Payment.objects.get(order=order).status, Payment.Status.HELD)
