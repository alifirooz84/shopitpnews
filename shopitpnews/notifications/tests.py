from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing
from notifications.models import MessageOutbox, Notification
from notifications.services import notify_user
from orders.models import Order
from payments.models import Payment


class NotificationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="notify-user", phone="09129990000")

    def test_notify_user_creates_notification_and_outbox(self):
        notify_user(self.user, "عنوان تست", "متن تست", queue_sms=True)
        self.assertTrue(Notification.objects.filter(recipient=self.user, title="عنوان تست").exists())
        self.assertTrue(MessageOutbox.objects.filter(recipient=self.user, channel=MessageOutbox.Channel.SMS).exists())
        self.assertTrue(MessageOutbox.objects.filter(recipient=self.user, channel=MessageOutbox.Channel.SYSTEM).exists())

    def test_notification_list_and_mark_read(self):
        notification = notify_user(self.user, "اعلان", "متن")
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:list"))
        self.assertContains(response, "اعلان")
        response = self.client.post(reverse("notifications:mark_read", args=[notification.pk]))
        self.assertRedirects(response, reverse("notifications:list"))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_order_creation_notifies_seller_and_buyer(self):
        seller = get_user_model().objects.create_user(username="notify-seller", phone="09129990001")
        buyer = get_user_model().objects.create_user(username="notify-buyer", phone="09129990002")
        listing = Listing.objects.create(
            seller=seller,
            title="آگهی اعلان",
            breed="آرین",
            quantity=10,
            price_per_chick=1000,
            province="تهران",
            city="ری",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(buyer)
        response = self.client.post(reverse("orders:create", args=[listing.pk]), {"quantity": 2})
        order = Order.objects.get()
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        self.assertTrue(Notification.objects.filter(recipient=seller, title__icontains="سفارش جدید").exists())
        self.assertTrue(Notification.objects.filter(recipient=buyer, title__icontains="سفارش شما").exists())

    def test_delivery_confirmation_creates_settlement_notification(self):
        seller = get_user_model().objects.create_user(username="notify-seller2", phone="09129990003")
        buyer = get_user_model().objects.create_user(username="notify-buyer2", phone="09129990004")
        listing = Listing.objects.create(
            seller=seller,
            title="آگهی تحویل اعلان",
            breed="راس ۳۰۸",
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
        response = self.client.post(reverse("orders:confirm_delivery", args=[order.pk]))
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        self.assertTrue(Notification.objects.filter(recipient=seller, title__icontains="وجه سفارش آزاد شد").exists())
