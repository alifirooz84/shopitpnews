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

    def test_create_listing_requires_login(self):
        response = self.client.get(reverse("listings:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_create_listing_assigns_current_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("listings:create"),
            {
                "title": "جوجه کاب آماده تحویل",
                "description": "گله سالم با واکسیناسیون کامل",
                "sale_type": Listing.SaleType.IMMEDIATE,
                "breed": "کاب ۵۰۰",
                "quantity": 2000,
                "price_per_chick": 19000,
                "province": "گلستان",
                "city": "گرگان",
                "delivery_date": timezone.localdate() + timedelta(days=2),
                "health_status": "واکسینه شده",
                "parent_flock_age": "۳۷-۵۰",
                "hatch_rate_percent": 83,
                "egg_weight_grams": 61,
                "vaccination_status": "کامل",
                "image_url": "",
            },
        )
        created = Listing.objects.get(title="جوجه کاب آماده تحویل")
        self.assertRedirects(response, created.get_absolute_url())
        self.assertEqual(created.seller, self.user)
