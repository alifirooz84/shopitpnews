from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Listing, MarketPrice


class ListingViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="seller", phone="09121111111")
        MarketPrice.objects.create(title="جوجه یک‌روزه", price=21000)
        self.listing = Listing.objects.create(
            seller=self.user,
            title="جوجه راس",
            breed="راس ۳۰۸",
            quantity=100,
            price_per_chick=20000,
            province="مازندران",
            city="آمل",
            delivery_date=timezone.localdate() + timedelta(days=1),
        )

    def test_dashboard_renders_market_data(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "جوجه بازار")
        self.assertContains(response, "جوجه راس")

    def test_listing_filter_by_province(self):
        response = self.client.get(reverse("listings:list"), {"province": "مازندران"})
        self.assertContains(response, self.listing.title)
