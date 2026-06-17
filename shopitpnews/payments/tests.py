from django.test import TestCase
from django.urls import reverse


class PaymentHealthTests(TestCase):
    def test_payment_health(self):
        response = self.client.get(reverse("payments:health"))
        self.assertEqual(response.status_code, 200)


from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing
from orders.models import Order
from payments.models import Payment, Settlement


class FinancialReportTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="finance-seller", phone="09126666666")
        self.buyer = user_model.objects.create_user(username="finance-buyer", phone="09127777777")
        self.listing = Listing.objects.create(
            seller=self.seller,
            title="آگهی مالی",
            breed="راس ۳۰۸",
            quantity=100,
            price_per_chick=1000,
            province="تهران",
            city="ری",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            listing=self.listing,
            order_type=Order.OrderType.INSTANT,
            status=Order.Status.DELIVERED,
            quantity=10,
            unit_price=1000,
            total_amount=10000,
        )
        self.payment = Payment.objects.create(order=self.order, amount=10000, status=Payment.Status.RELEASED)

    def test_payment_create_settlement_calculates_commission(self):
        settlement = self.payment.create_settlement()
        self.assertEqual(settlement.gross_amount, 10000)
        self.assertEqual(settlement.commission_amount, 300)
        self.assertEqual(settlement.net_amount, 9700)
        self.assertEqual(settlement.seller, self.seller)

    def test_financial_report_renders_for_buyer_and_seller(self):
        self.payment.create_settlement()
        self.client.force_login(self.seller)
        response = self.client.get(reverse("payments:financial_report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "دفتر تسویه فروش")
        self.assertContains(response, "9700")

        self.client.force_login(self.buyer)
        response = self.client.get(reverse("payments:financial_report"))
        self.assertContains(response, "پرداخت‌های خرید")
        self.assertContains(response, "10000")

    def test_financial_report_csv(self):
        self.payment.create_settlement()
        self.client.force_login(self.seller)
        response = self.client.get(reverse("payments:financial_report_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertContains(response, "settlement")

    def test_mark_settlement_paid(self):
        settlement = self.payment.create_settlement()
        settlement.mark_paid(notes="bank ref 123")
        settlement.refresh_from_db()
        self.assertEqual(settlement.status, Settlement.Status.PAID)
        self.assertEqual(settlement.notes, "bank ref 123")


class WalletTests(TestCase):
    def test_wallet_top_up_creates_transaction(self):
        user = get_user_model().objects.create_user(username="wallet-user", phone="09127770000")
        self.client.force_login(user)
        response = self.client.post(reverse("payments:top_up"), {"amount": 50000})
        self.assertRedirects(response, reverse("payments:wallet"))
        user.refresh_from_db()
        self.assertEqual(user.wallet.balance, 50000)
        self.assertEqual(user.wallet.transactions.count(), 1)

    def test_cancelled_order_refunds_to_wallet(self):
        seller = get_user_model().objects.create_user(username="wallet-seller", phone="09127770001")
        buyer = get_user_model().objects.create_user(username="wallet-buyer", phone="09127770002")
        listing = Listing.objects.create(
            seller=seller,
            title="آگهی کیف پول",
            breed="آرین",
            quantity=10,
            price_per_chick=1000,
            province="تهران",
            city="ری",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )
        order = Order.objects.create(
            buyer=buyer,
            listing=listing,
            order_type=Order.OrderType.INSTANT,
            status=Order.Status.PAID_HELD,
            quantity=2,
            unit_price=1000,
            total_amount=2000,
        )
        Payment.objects.create(order=order, amount=2000)
        self.client.force_login(buyer)
        response = self.client.post(reverse("orders:cancel", args=[order.pk]))
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        buyer.refresh_from_db()
        self.assertEqual(buyer.wallet.balance, 2000)
        self.assertTrue(buyer.wallet.transactions.filter(transaction_type="refund", amount=2000).exists())
