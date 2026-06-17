from django import forms
from django.db import models

from listings.models import MarketPrice


class MarketPriceForm(forms.ModelForm):
    class Meta:
        model = MarketPrice
        fields = ("title", "price", "unit", "direction", "display_order")
        labels = {
            "title": "عنوان شاخص",
            "price": "قیمت",
            "unit": "واحد",
            "direction": "روند",
            "display_order": "ترتیب نمایش",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )


class NewsletterForm(forms.Form):
    class Target(models.TextChoices):
        ALL = "all", "همه کاربران فعال"
        VERIFIED = "verified", "کاربران تأیید شده"
        SELLERS = "sellers", "فروشندگان دارای آگهی"
        BUYERS = "buyers", "خریداران دارای سفارش"

    title = forms.CharField(label="عنوان", max_length=160)
    body = forms.CharField(label="متن پیام", widget=forms.Textarea(attrs={"rows": 5}))
    target = forms.ChoiceField(label="گروه مخاطب", choices=Target.choices)
    queue_sms = forms.BooleanField(label="ثبت پیامک در صف ارسال", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )
