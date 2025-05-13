from django import forms

from reservations.models import Reservation, WorkDay
from services.models import Service
from users.models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["name", "services"]


class WorkDayForm(forms.ModelForm):
    class Meta:
        model = WorkDay
        fields = ["date", "employee", "start_time", "end_time"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "employee": forms.Select(attrs={"class": "form-control"}),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
        }


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
