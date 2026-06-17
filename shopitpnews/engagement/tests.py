from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from engagement.models import Conversation, ConversationMessage, FavoriteListing
from listings.models import Listing
from notifications.models import Notification


class EngagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="eng-seller", phone="09123000001")
        self.buyer = user_model.objects.create_user(username="eng-buyer", phone="09123000002")
        self.listing = Listing.objects.create(
            seller=self.seller,
            title="آگهی تعامل",
            breed="آرین",
            quantity=100,
            price_per_chick=1000,
            province="تهران",
            city="ری",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )

    def test_toggle_favorite_adds_and_removes_listing(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("engagement:toggle_favorite", args=[self.listing.pk]))
        self.assertRedirects(response, self.listing.get_absolute_url())
        self.assertTrue(FavoriteListing.objects.filter(user=self.buyer, listing=self.listing).exists())
        self.client.post(reverse("engagement:toggle_favorite", args=[self.listing.pk]))
        self.assertFalse(FavoriteListing.objects.filter(user=self.buyer, listing=self.listing).exists())

    def test_favorites_page_lists_saved_listing(self):
        FavoriteListing.objects.create(user=self.buyer, listing=self.listing)
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("engagement:favorites"))
        self.assertContains(response, self.listing.title)

    def test_contact_seller_creates_conversation_and_notification(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("engagement:contact_seller", args=[self.listing.pk]), {"body": "سلام قیمت نهایی؟"})
        conversation = Conversation.objects.get(buyer=self.buyer, seller=self.seller, listing=self.listing)
        self.assertRedirects(response, conversation.get_absolute_url())
        self.assertTrue(conversation.messages.filter(body="سلام قیمت نهایی؟").exists())
        self.assertTrue(Notification.objects.filter(recipient=self.seller, title__icontains="پیام جدید").exists())

    def test_seller_cannot_contact_self(self):
        self.client.force_login(self.seller)
        response = self.client.post(reverse("engagement:contact_seller", args=[self.listing.pk]))
        self.assertRedirects(response, self.listing.get_absolute_url())
        self.assertFalse(Conversation.objects.exists())

    def test_conversation_message_can_be_added_by_participant(self):
        conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        self.client.force_login(self.seller)
        response = self.client.post(reverse("engagement:add_message", args=[conversation.pk]), {"body": "قیمت همین است."})
        self.assertRedirects(response, conversation.get_absolute_url())
        self.assertTrue(ConversationMessage.objects.filter(conversation=conversation, sender=self.seller, body="قیمت همین است.").exists())
        self.assertTrue(Notification.objects.filter(recipient=self.buyer, title__icontains="پیام جدید").exists())

    def test_non_participant_cannot_view_conversation(self):
        other = get_user_model().objects.create_user(username="eng-other", phone="09123000003")
        conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        self.client.force_login(other)
        response = self.client.get(reverse("engagement:conversation_detail", args=[conversation.pk]))
        self.assertEqual(response.status_code, 404)
