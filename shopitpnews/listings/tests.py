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


class ListingManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="manager", phone="09123333333")
        self.other = get_user_model().objects.create_user(username="other", phone="09124444444")
        self.listing = Listing.objects.create(
            seller=self.user,
            title="آگهی قابل مدیریت",
            breed="راس ۳۰۸",
            quantity=500,
            price_per_chick=18000,
            province="تهران",
            city="ورامین",
            delivery_date=timezone.localdate() + timedelta(days=2),
        )

    def test_my_listings_shows_owned_listing(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("listings:mine"))
        self.assertContains(response, self.listing.title)

    def test_upload_image_on_listing_create(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_login(self.user)
        upload = SimpleUploadedFile("chicks.jpg", b"fake-image-content", content_type="image/jpeg")
        response = self.client.post(
            reverse("listings:create"),
            {
                "title": "آگهی تصویردار",
                "description": "تست آپلود تصویر",
                "sale_type": Listing.SaleType.IMMEDIATE,
                "breed": "آرین",
                "quantity": 100,
                "price_per_chick": 17000,
                "province": "تهران",
                "city": "ری",
                "delivery_date": timezone.localdate() + timedelta(days=3),
                "health_status": "واکسینه شده",
                "parent_flock_age": "۳۷-۵۰",
                "hatch_rate_percent": 82,
                "egg_weight_grams": 60,
                "vaccination_status": "کامل",
                "image": upload,
                "image_url": "",
            },
        )
        created = Listing.objects.get(title="آگهی تصویردار")
        self.assertRedirects(response, created.get_absolute_url())
        self.assertTrue(created.image.name.startswith("listing-images/"))

    def test_update_listing_requires_owner(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("listings:edit", args=[self.listing.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_update_listing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("listings:edit", args=[self.listing.pk]),
            {
                "title": "عنوان ویرایش شده",
                "description": "ویرایش",
                "sale_type": Listing.SaleType.FUTURE,
                "breed": self.listing.breed,
                "quantity": 400,
                "price_per_chick": 19000,
                "province": self.listing.province,
                "city": self.listing.city,
                "delivery_date": timezone.localdate() + timedelta(days=4),
                "health_status": "واکسینه شده",
                "parent_flock_age": "۳۷-۵۰",
                "hatch_rate_percent": 84,
                "egg_weight_grams": 62,
                "vaccination_status": "کامل",
                "image_url": "",
            },
        )
        self.listing.refresh_from_db()
        self.assertRedirects(response, self.listing.get_absolute_url())
        self.assertEqual(self.listing.title, "عنوان ویرایش شده")
        self.assertEqual(self.listing.quantity, 400)

    def test_delete_listing_soft_hides_it(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("listings:delete", args=[self.listing.pk]))
        self.assertRedirects(response, reverse("listings:mine"))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.INACTIVE)
