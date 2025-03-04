import datetime

from django import forms
from django.forms import ModelForm
from phonenumber_field.modelfields import PhoneNumberField
from services.models import Service
from users.models import Employee

from .models import Reservation, WorkDay


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["service", "reservation_date", "start_time", "employee"]
        widgets = {
            "reservation_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }


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


class ServiceSelectionForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class EmployeeSelectionForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        service = kwargs.pop("service", None)
        super().__init__(*args, **kwargs)
        if service:
            self.fields["employee"].queryset = Employee.objects.filter(services=service)


class DateSelectionForm(forms.Form):
    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)

        today = datetime.date.today()
        self.fields["reservation_date"].widget.attrs["min"] = today.strftime("%Y-%m-%d")

    def clean_reservation_date(self):
        date = self.cleaned_data["reservation_date"]
        today = datetime.date.today()

        if date < today:
            raise forms.ValidationError("Nie możesz wwybrać daty z przeszłości.")

        if self.employee:
            workday = WorkDay.objects.filter(employee=self.employee, date=date).first()
            if not workday:
                raise forms.ValidationError("Wybrany pracownik nie pracuje w tym dniu.")

        return date


class TimeSelectionForm(forms.Form):
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop("employee", None)
        self.date = kwargs.pop("date", None)
        self.service = kwargs.pop("service", None)
        super().__init__(*args, **kwargs)

    def clean_start_time(self):
        time = self.cleaned_data["start_time"]

        workday = WorkDay.objects.filter(employee=self.employee, date=self.date).first()
        if workday:
            if not (workday.start_time <= time <= workday.end_time):
                raise forms.ValidationError("Wybrany czas jest poza godzinami pracy.")

        start_datetime = datetime.datetime.combine(self.date, time)
        duration = datetime.timedelta(minutes=self.service.duration)
        end_datetime = start_datetime + duration
        end_time = end_datetime.time()

        if end_time > workday.end_time:
            raise forms.ValidationError(
                f"Usługa kończy się poza godzinami pracy pracownika. "
                f"Ostatni dostępny czas usługo to "
                f"{(datetime.datetime.combine(self.date, workday.end_time) - duration).time().strftime('%H:%M')}."
            )

        reservations = Reservation.objects.filter(
            employee=self.employee,
            reservation_date=self.date,
            status__in=["PENDING", "CONFIRMED"],
        )

        for reservation in reservations:
            reservation_end = reservation.end_time
            reservation_start = reservation.start_time

            if (
                (reservation_start <= time < reservation_end)
                or (reservation_start < end_time <= reservation_end)
                or (time <= reservation_start and end_time >= reservation_end)
            ):
                raise forms.ValidationError(
                    "Czas rezerwacji nakłada się na inną rezerwację"
                )

        return time


class ConfirmationForm(forms.Form):
    notes = forms.CharField(
        label="Dodaj notatkę (opcjonalnie)",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        required=False,
    )
