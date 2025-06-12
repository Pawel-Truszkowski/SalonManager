from django import forms

from .models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "category", "description", "duration", "price"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Write duration time in minutes",
                }
            ),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
        }
