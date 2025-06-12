from django import forms
from phonenumber_field.formfields import SplitPhoneNumberField

from users.models import Employee
from utils.validators import not_in_the_past

from .models import Reservation, ReservationRequest, WorkDay


class SlotForm(forms.Form):
    selected_date = forms.DateField(validators=[not_in_the_past])
    staff_member = forms.ModelChoiceField(
        Employee.objects.all(),
        error_messages={"invalid_choice": "Staff member does not exist"},
    )
    service_id = forms.IntegerField(required=True)


class ReservationRequestForm(forms.ModelForm):
    class Meta:
        model = ReservationRequest
        fields = ("date", "start_time", "end_time", "service", "employee")
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "service": forms.Select(attrs={"class": "form-control"}),
            "employee": forms.Select(attrs={"class": "form-control"}),
        }


class ReservationForm(forms.ModelForm):
    phone = SplitPhoneNumberField(required=True, region="PL")

    class Meta:
        model = Reservation
        fields = ("phone", "additional_info")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].widget.attrs.update({"placeholder": "123456789"})
        self.fields["additional_info"].widget.attrs.update(
            {
                "rows": 2,
                "class": "form-control",
                "placeholder": "Would you like to tell somthing for us?",
            }
        )


class ClientDataForm(forms.Form):
    name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))


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
