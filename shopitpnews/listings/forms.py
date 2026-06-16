from django import forms
from django.utils import timezone

from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = (
            "title",
            "description",
            "sale_type",
            "breed",
            "quantity",
            "price_per_chick",
            "province",
            "city",
            "delivery_date",
            "health_status",
            "parent_flock_age",
            "hatch_rate_percent",
            "egg_weight_grams",
            "vaccination_status",
            "image_url",
        )
        labels = {
            "title": "عنوان آگهی",
            "description": "توضیحات",
            "sale_type": "نوع آگهی",
            "breed": "نژاد یا واریته",
            "quantity": "تعداد جوجه",
            "price_per_chick": "قیمت هر قطعه",
            "province": "استان",
            "city": "شهر",
            "delivery_date": "تاریخ تحویل",
            "health_status": "وضعیت بهداشتی",
            "parent_flock_age": "سن گله مادر",
            "hatch_rate_percent": "درصد جوجه دهی",
            "egg_weight_grams": "میانگین وزن تخم مرغ",
            "vaccination_status": "وضعیت واکسیناسیون",
            "image_url": "آدرس تصویر",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "delivery_date": forms.DateInput(attrs={"type": "date"}),
            "image_url": forms.URLInput(attrs={"placeholder": "اختیاری"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data["delivery_date"]
        if delivery_date < timezone.localdate():
            raise forms.ValidationError("تاریخ تحویل نمی‌تواند در گذشته باشد.")
        return delivery_date

    def clean_reservation_percent(self):
        value = self.cleaned_data.get("reservation_percent", 0)
        return min(max(value, 0), 100)
