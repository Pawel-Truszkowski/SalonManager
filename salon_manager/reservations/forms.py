import datetime
import locale

from django import forms
from services.models import Service
from users.models import Employee

from .models import Reservation, WorkDay


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
        label=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class EmployeeSelectionForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        label=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        service = kwargs.pop("service", None)
        super().__init__(*args, **kwargs)
        if service:
            self.fields["employee"].queryset = Employee.objects.filter(services=service)


class DateSelectionForm(forms.Form):
    reservation_date = forms.ChoiceField(
        label=False, widget=forms.Select(attrs={"class": "form-control"}), choices=[]
    )

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)

        if self.employee:
            today = datetime.date.today()

            workdays = WorkDay.objects.filter(
                employee=self.employee,
                date__gte=today,
                date__lte=today + datetime.timedelta(days=60),
            ).order_by("date")

            locale.setlocale(locale.LC_TIME, "pl_PL.UTF-8")

            date_choices = [
                (
                    workday.date.strftime("%Y-%m-%d"),
                    workday.date.strftime("%A, %d %B, %Y"),
                )
                for workday in workdays
            ]

            if date_choices:
                self.fields["reservation_date"].choices = date_choices
            else:
                self.fields["reservation_date"].choices = [("", "Brak dostępnych dat.")]

    def clean_reservation_date(self):
        date = self.cleaned_data["reservation_date"]
        today = datetime.date.today()

        if isinstance(date, str):
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Niepoprawny format daty. Oczekiwano YYYY-MM-DD.")

        if date < today:
            raise forms.ValidationError("Nie możesz wwybrać daty z przeszłości.")

        if self.employee:
            workday = WorkDay.objects.filter(employee=self.employee, date=date).first()
            if not workday:
                raise forms.ValidationError("Wybrany pracownik nie pracuje w tym dniu.")

        return date


class TimeSelectionForm(forms.Form):
    start_time = forms.ChoiceField(
        label="Select a time",
        widget=forms.Select(attrs={"class": "form-control"}),
        choices=[],
    )

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop("employee", None)
        self.date = kwargs.pop("date", None)
        self.service = kwargs.pop("service", None)
        super().__init__(*args, **kwargs)

        try:
            workday = WorkDay.objects.get(employee=self.employee, date=self.date)
            existing_resevations = Reservation.objects.filter(
                employee=self.employee,
                reservation_date=self.date,
                status__in=["PENDING", "CONFIRMED"],
            )

            available_slots = []
            service_duration = datetime.timedelta(minutes=self.service.duration)

            current_time = datetime.datetime.combine(self.date, workday.start_time)
            end_time = datetime.datetime.combine(self.date, workday.end_time)

            # Create 15-minute intervals
            while current_time + service_duration <= end_time:
                time_slot_end = current_time + service_duration

                is_available = True
                for reservation in existing_resevations:
                    reservation_start = datetime.datetime.combine(
                        self.date, reservation.start_time
                    )
                    reservation_end = datetime.datetime.combine(
                        self.date, reservation.end_time
                    )

                    if (
                        current_time < reservation_end
                        and time_slot_end > reservation_start
                    ):
                        is_available = False
                        break

                if is_available:
                    time_display = current_time.strftime("%I:%M %p")
                    time_value = current_time.strftime("%H:%M")
                    available_slots.append((time_value, time_display))

                current_time += datetime.timedelta(minutes=15)

            if available_slots:
                self.fields["start_time"].choices = available_slots
            else:
                self.fields["start_time"].choices = [("", "Brak dostępnych miejsc.")]

        except WorkDay.DoesNotExist:
            self.fields["start_time"].choices = [
                (
                    "",
                    "Brak dostępnych miejsc w wybranej dacie. Proszę spróbuj inny dzień",
                )
            ]

    def clean_start_time(self):
        time = self.cleaned_data["start_time"]

        if isinstance(time, str):
            try:
                time = datetime.datetime.strptime(time, "%H:%M").time()
            except ValueError:
                raise ValueError("Niepoprawny format czasu.")

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
