from django import forms

from .models import User, VerificationRequest


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "role", "province", "city")
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "role": "نوع فعالیت",
            "province": "استان",
            "city": "شهر",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "مثلا علیرضا"}),
            "last_name": forms.TextInput(attrs={"placeholder": "مثلا کریمی"}),
            "province": forms.TextInput(attrs={"placeholder": "مثلا مازندران"}),
            "city": forms.TextInput(attrs={"placeholder": "مثلا آمل"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )


class VerificationRequestForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ("national_id", "business_name", "business_address", "document")
        labels = {
            "national_id": "کد ملی یا شناسه واحد",
            "business_name": "نام فارم/واحد فعالیت",
            "business_address": "آدرس واحد فعالیت",
            "document": "تصویر مدرک هویتی یا فعالیت",
        }
        widgets = {
            "business_address": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )
