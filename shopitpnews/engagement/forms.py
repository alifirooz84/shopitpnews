from django import forms

from .models import ConversationMessage


class ConversationMessageForm(forms.ModelForm):
    class Meta:
        model = ConversationMessage
        fields = ("body", "attachment")
        labels = {"body": "متن پیام", "attachment": "پیوست"}
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4, "placeholder": "پیام خود را برای فروشنده یا خریدار بنویسید."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attachment"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border-gray-300 bg-white px-4 py-3 focus:border-[#0d631b] focus:ring-[#0d631b]",
            )
