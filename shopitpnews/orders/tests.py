from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing
from payments.models import Payment

from .models import DisputeCase, DisputeMessage, Order, PurchaseOffer


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

    def test_dispute_creates_case_and_keeps_payment_held(self):
        self._create_order(quantity=1)
        order = Order.objects.get()
        response = self.client.post(
            reverse("orders:dispute", args=[order.pk]),
            {"reason": DisputeCase.Reason.QUALITY, "description": "کیفیت تحویل مغایرت دارد."},
        )
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DISPUTED)
        self.assertEqual(order.payment.status, Payment.Status.HELD)
        self.assertEqual(order.dispute_case.reason, DisputeCase.Reason.QUALITY)
        self.assertTrue(order.dispute_case.messages.filter(body__icontains="کیفیت").exists())

    def test_dispute_message_can_be_added_by_party(self):
        self._create_order(quantity=1)
        order = Order.objects.get()
        self.client.post(
            reverse("orders:dispute", args=[order.pk]),
            {"reason": DisputeCase.Reason.DELAY, "description": "تأخیر دارد."},
        )
        response = self.client.post(
            reverse("orders:add_dispute_message", args=[order.dispute_case.pk]),
            {"body": "توضیح تکمیلی"},
        )
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        self.assertTrue(DisputeMessage.objects.filter(dispute=order.dispute_case, body="توضیح تکمیلی").exists())

    def test_seller_can_view_order_detail(self):
        self._create_order(quantity=1)
        order = Order.objects.get()
        self.client.force_login(self.seller)
        response = self.client.get(reverse("orders:detail", args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "جزئیات سفارش")


class PurchaseOfferFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="offer-seller", phone="09121110001")
        self.buyer = user_model.objects.create_user(username="offer-buyer", phone="09121110002")
        self.listing = Listing.objects.create(
            seller=self.seller,
            title="آگهی پیشنهاد",
            breed="راس ۳۰۸",
            quantity=20,
            price_per_chick=20000,
            province="تهران",
            city="ری",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )

    def test_buyer_can_create_purchase_offer(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("orders:create_offer", args=[self.listing.pk]),
            {"quantity": 5, "proposed_unit_price": 18000, "message": "اگر موافقید سریع خرید می‌کنم."},
        )
        offer = PurchaseOffer.objects.get()
        self.assertRedirects(response, offer.get_absolute_url())
        self.assertEqual(offer.total_amount, 90000)
        self.assertEqual(offer.status, PurchaseOffer.Status.PENDING)

    def test_seller_accepts_offer_creates_order_and_payment(self):
        offer = PurchaseOffer.objects.create(
            buyer=self.buyer,
            listing=self.listing,
            quantity=4,
            proposed_unit_price=17000,
        )
        self.client.force_login(self.seller)
        response = self.client.post(reverse("orders:accept_offer", args=[offer.pk]), {"seller_note": "قبول"})
        order = Order.objects.get(order_type=Order.OrderType.OFFER)
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        offer.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(offer.status, PurchaseOffer.Status.ACCEPTED)
        self.assertEqual(offer.created_order, order)
        self.assertEqual(order.unit_price, 17000)
        self.assertEqual(order.total_amount, 68000)
        self.assertEqual(order.payment.status, Payment.Status.HELD)
        self.assertEqual(self.listing.quantity, 16)

    def test_seller_rejects_offer(self):
        offer = PurchaseOffer.objects.create(buyer=self.buyer, listing=self.listing, quantity=2, proposed_unit_price=15000)
        self.client.force_login(self.seller)
        response = self.client.post(reverse("orders:reject_offer", args=[offer.pk]), {"seller_note": "کم است"})
        self.assertRedirects(response, offer.get_absolute_url())
        offer.refresh_from_db()
        self.assertEqual(offer.status, PurchaseOffer.Status.REJECTED)
        self.assertEqual(offer.seller_note, "کم است")

    def test_buyer_can_cancel_pending_offer(self):
        offer = PurchaseOffer.objects.create(buyer=self.buyer, listing=self.listing, quantity=2, proposed_unit_price=15000)
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("orders:cancel_offer", args=[offer.pk]))
        self.assertRedirects(response, offer.get_absolute_url())
        offer.refresh_from_db()
        self.assertEqual(offer.status, PurchaseOffer.Status.CANCELLED)

    def test_offer_cannot_exceed_inventory(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("orders:create_offer", args=[self.listing.pk]),
            {"quantity": 99, "proposed_unit_price": 18000},
        )
        self.assertRedirects(response, self.listing.get_absolute_url())
        self.assertFalse(PurchaseOffer.objects.exists())
