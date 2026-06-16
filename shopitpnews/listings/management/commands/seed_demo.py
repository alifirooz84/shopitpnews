from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from listings.models import Listing, MarketPrice


class Command(BaseCommand):
    help = "Seed Persian demo market data for the current frontend templates."

    def handle(self, *args, **options):
        user_model = get_user_model()
        seller, _ = user_model.objects.get_or_create(
            username="09120000000",
            defaults={
                "phone": "09120000000",
                "first_name": "علیرضا",
                "last_name": "کریمی",
                "role": "parent_farm",
                "is_phone_verified": True,
            },
        )

        MarketPrice.objects.all().delete()
        for idx, item in enumerate([
            ("جوجه یک‌روزه گوشتی", 21400, "up"),
            ("تخم‌مرغ نطفه‌دار", 9200, "down"),
            ("ذرت برزیل", 11300, "up"),
            ("کنجاله سویا", 24500, "flat"),
        ]):
            MarketPrice.objects.create(title=item[0], price=item[1], direction=item[2], display_order=idx)

        image = "https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?auto=format&fit=crop&w=900&q=80"
        demo_rows = [
            ("جوجه یک‌روزه گوشتی نژاد راس ۳۰۸", "راس ۳۰۸", 15000, 18500, "مازندران", "آمل", True, 35),
            ("جوجه یک‌روزه گوشتی نژاد آرین", "آرین", 5000, 18200, "مازندران", "بابل", True, 65),
            ("جوجه کاب ۵۰۰ آماده تحویل", "کاب ۵۰۰", 12000, 19100, "گلستان", "گرگان", False, 20),
            ("جوجه بومی اصلاح‌شده پیش‌خرید", "بومی اصلاح شده", 8000, 17600, "اصفهان", "نجف‌آباد", False, 10),
        ]
        Listing.objects.all().delete()
        for days, row in enumerate(demo_rows):
            title, breed, quantity, price, province, city, featured, reserved = row
            Listing.objects.create(
                seller=seller,
                title=title,
                description="تولید شده در فارم تایید شده، دارای گواهی سلامت و برنامه واکسیناسیون کامل.",
                sale_type=Listing.SaleType.IMMEDIATE if days < 2 else Listing.SaleType.FUTURE,
                breed=breed,
                quantity=quantity,
                price_per_chick=price,
                province=province,
                city=city,
                delivery_date=timezone.localdate() + timedelta(days=days),
                image_url=image,
                is_verified=True,
                is_featured=featured,
                reservation_percent=reserved,
                seller_name="مهندس علیرضا کریمی",
                seller_title="مدیر فروش فارم سپیدان",
                seller_transactions=1500 + days,
            )
        self.stdout.write(self.style.SUCCESS("Demo marketplace data seeded."))
