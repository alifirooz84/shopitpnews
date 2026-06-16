from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing
from payments.models import Payment

from .models import Order


class OrderFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="seller", phone="09120000001")
        self.buyer = user_model.objects.create_user(username="buyer", phone="09120000002")
        self.listing = Listing.objects.create(
            seller=self.seller,
            title="جوجه آرین",
            breed="آرین",
            quantity=10,
            price_per_chick=1000,
            province="گلستان",
            city="گرگان",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )

    def _create_order(self, quantity=3):
        self.client.force_login(self.buyer)
        return self.client.post(
            reverse("orders:create", args=[self.listing.pk]),
            {"quantity": quantity, "order_type": "instant"},
        )

    def test_create_order_creates_held_payment_and_reserves_inventory(self):
        response = self._create_order(quantity=3)
        order = Order.objects.get()
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        self.assertEqual(order.total_amount, 3000)
        self.assertEqual(Payment.objects.get(order=order).status, Payment.Status.HELD)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity, 7)

    def test_buyer_cannot_order_own_listing(self):
        self.client.force_login(self.seller)
        response = self.client.post(reverse("orders:create", args=[self.listing.pk]), {"quantity": 1})
        self.assertRedirects(response, self.listing.get_absolute_url())
        self.assertFalse(Order.objects.exists())

    def test_confirm_delivery_releases_payment(self):
        self._create_order(quantity=2)
        order = Order.objects.get()
        response = self.client.post(reverse("orders:confirm_delivery", args=[order.pk]))
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertEqual(order.payment.status, Payment.Status.RELEASED)

    def test_cancel_order_refunds_payment_and_restores_inventory(self):
        self._create_order(quantity=4)
        order = Order.objects.get()
        response = self.client.post(reverse("orders:cancel", args=[order.pk]))
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        order.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.listing.quantity, 10)

    def test_dispute_keeps_payment_held(self):
        self._create_order(quantity=1)
        order = Order.objects.get()
        response = self.client.post(reverse("orders:dispute", args=[order.pk]))
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DISPUTED)
        self.assertEqual(order.payment.status, Payment.Status.HELD)

    def test_seller_can_view_order_detail(self):
        self._create_order(quantity=1)
        order = Order.objects.get()
        self.client.force_login(self.seller)
        response = self.client.get(reverse("orders:detail", args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "جزئیات سفارش")
