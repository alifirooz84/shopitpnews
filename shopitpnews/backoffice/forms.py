from django import forms

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
