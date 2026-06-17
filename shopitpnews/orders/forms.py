from django import forms

from .models import DisputeCase, DisputeMessage


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
