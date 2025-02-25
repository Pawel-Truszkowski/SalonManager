from django import forms

from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["service", "employee", "reservation_date", "start_time"]
        widgets = {
            "reservation_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }
