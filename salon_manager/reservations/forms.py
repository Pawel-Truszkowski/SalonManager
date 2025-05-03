from django import forms
from django.utils.translation import gettext as _
from phonenumber_field.formfields import SplitPhoneNumberField

from services.models import Service
from users.models import Employee
from utils.validators import not_in_the_past

from .models import Reservation, ReservationRequest


class CustomerInfoForm(forms.Form):
    name = forms.CharField(max_length=100, disabled=True, required=False)
    email = forms.EmailField(required=False, disabled=True)
    phone = forms.CharField(max_length=15, disabled=True, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["name"].initial = (
                self.user.get_full_name() or self.user.username
            )
            self.fields["email"].initial = self.user.email
            self.fields["phone"].initial = self.user.phone_number

            for field in self.fields:
                self.fields[field].widget.attrs["readonly"] = True


class ReservationSelectionForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={"class": "form-control", "id": "id_service"}),
    )

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={"class": "form-control", "id": "id_employee"}),
    )

    reservation_date = forms.DateField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_reservation_date",
                "autocomplete": "off",
            }
        )
    )

    start_time = forms.CharField(
        widget=forms.Select(attrs={"class": "form-control", "id": "id_start_time"}),
    )


class ConfirmationForm(forms.Form):
    notes = forms.CharField(
        label="Add special notes (optional)",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        required=False,
    )


###################### NEW #########################
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


class ReservationForm(forms.ModelForm):
    phone = SplitPhoneNumberField()

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
        max_length=50, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
