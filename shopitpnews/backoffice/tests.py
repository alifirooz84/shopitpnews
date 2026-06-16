from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing, MarketPrice
from orders.models import Order
from payments.models import Payment


class BackofficeTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(username="admin", phone="09120001000", is_staff=True)
        self.buyer = user_model.objects.create_user(username="buyer2", phone="09120001001")
        self.seller = user_model.objects.create_user(username="seller2", phone="09120001002")
        self.listing = Listing.objects.create(
            seller=self.seller,
            title="جوجه اختلافی",
            breed="راس ۳۰۸",
            quantity=5,
            price_per_chick=1000,
            province="مازندران",
            city="آمل",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            listing=self.listing,
            order_type=Order.OrderType.INSTANT,
            status=Order.Status.DISPUTED,
            quantity=2,
            unit_price=1000,
            total_amount=2000,
        )
        self.payment = Payment.objects.create(order=self.order, amount=2000)

    def test_backoffice_requires_staff(self):
        response = self.client.get(reverse("backoffice:overview"))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_manage_market_prices(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("backoffice:market_prices"),
            {"title": "جوجه یک‌روزه", "price": 21000, "unit": "تومان", "direction": "up", "display_order": 1},
        )
        self.assertRedirects(response, reverse("backoffice:market_prices"))
        self.assertTrue(MarketPrice.objects.filter(title="جوجه یک‌روزه", price=21000).exists())

    def test_staff_can_verify_user(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("backoffice:user_action", args=[self.buyer.pk]), {"action": "verify"})
        self.assertRedirects(response, reverse("backoffice:users"))
        self.buyer.refresh_from_db()
        self.assertTrue(self.buyer.is_phone_verified)

    def test_staff_can_release_disputed_payment(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("backoffice:resolve_dispute", args=[self.order.pk]), {"resolution": "release"})
        self.assertRedirects(response, reverse("backoffice:disputes"))
        self.order.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DELIVERED)
        self.assertEqual(self.payment.status, Payment.Status.RELEASED)

    def test_staff_can_refund_disputed_payment_and_restore_inventory(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("backoffice:resolve_dispute", args=[self.order.pk]), {"resolution": "refund"})
        self.assertRedirects(response, reverse("backoffice:disputes"))
        self.order.refresh_from_db()
        self.payment.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.listing.quantity, 7)
