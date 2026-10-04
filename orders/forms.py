from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    # Honeypot: real people never see or fill this field.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off", "aria-hidden": "true"}))

    class Meta:
        model = Order
        fields = ["size", "name", "contact", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "contact": forms.TextInput(attrs={"placeholder": "@username или +7…"}),
            "comment": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, sizes=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sizes:
            self.fields["size"] = forms.ChoiceField(
                label="Размер", choices=[("", "Выберите размер")] + [(s, s) for s in sizes])
        else:
            del self.fields["size"]

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("spam")
        return ""
