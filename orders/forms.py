from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    # Honeypot: real people never see or fill this field.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off", "aria-hidden": "true"}))
    agree = forms.BooleanField(label="Согласен с правилами магазина", required=True,
                               error_messages={"required": "Нужно согласиться с правилами."})

    class Meta:
        model = Order
        fields = ["name", "contact", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "contact": forms.TextInput(attrs={"placeholder": "@username или +7…"}),
            "comment": forms.Textarea(attrs={"rows": 2, "placeholder": "Город доставки, пожелания по посадке…"}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("spam")
        return ""
