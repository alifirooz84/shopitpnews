from django import forms

from .models import DisputeCase, DisputeMessage, PurchaseOffer


class PurchaseOfferForm(forms.ModelForm):
    class Meta:
        model = PurchaseOffer
        fields = ("quantity", "proposed_unit_price", "message")
        labels = {
            "quantity": "تعداد درخواستی",
            "proposed_unit_price": "قیمت پیشنهادی هر قطعه",
            "message": "پیام به فروشنده",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "شرایط پیشنهادی یا توضیح خود را بنویسید."}),
        }

    def __init__(self, *args, max_quantity=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_quantity is not None:
            self.fields["quantity"].widget.attrs["max"] = max_quantity
            self.fields["quantity"].help_text = f"حداکثر موجودی قابل پیشنهاد: {max_quantity} قطعه"
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("تعداد باید حداقل ۱ باشد.")
        max_attr = self.fields["quantity"].widget.attrs.get("max")
        if max_attr and quantity > int(max_attr):
            raise forms.ValidationError("تعداد پیشنهادی بیشتر از موجودی آگهی است.")
        return quantity

    def clean_proposed_unit_price(self):
        price = self.cleaned_data["proposed_unit_price"]
        if price < 1:
            raise forms.ValidationError("قیمت پیشنهادی معتبر نیست.")
        return price


class DisputeCaseForm(forms.ModelForm):
    class Meta:
        model = DisputeCase
        fields = ("reason", "description", "evidence")
        labels = {
            "reason": "دلیل اختلاف",
            "description": "شرح اختلاف",
            "evidence": "مدرک یا تصویر پیوست",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "جزئیات تأخیر، مغایرت کیفیت یا تعداد را بنویسید."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["evidence"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )


class DisputeMessageForm(forms.ModelForm):
    class Meta:
        model = DisputeMessage
        fields = ("body", "attachment")
        labels = {
            "body": "پیام",
            "attachment": "پیوست",
        }
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "پاسخ یا توضیح تکمیلی خود را وارد کنید."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attachment"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )
