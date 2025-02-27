from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from services.models import Service
from users.models import Employee

from .forms import ReservationForm
from .models import Reservation, WorkDay


@login_required(redirect_field_name="login")
def reservation(request):
    employees = Employee.objects.all()
    services = Service.objects.all()

    if request.method == "POST":
        form = ReservationForm(request.POST)

        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.customer = request.user
            workday = WorkDay.objects.filter(
                employee=reservation.employee_id, date=reservation.reservation_date
            ).first()
            if not workday:
                form.add_error(
                    "reservation_date", "Wybrany pracownik nie pracuje w tym dniu."
                )
            else:
                if not (
                    workday.start_time <= reservation.start_time <= workday.end_time
                ):
                    form.add_error(
                        "start_time",
                        "Wybrana godzina jest poza godzinami pracy pracownika.",
                    )
                else:
                    existing_reservation = Reservation.objects.filter(
                        employee=reservation.employee,
                        reservation_date=reservation.reservation_date,
                        start_time=reservation.start_time,
                    )

                    if existing_reservation.exists():
                        form.add_error(
                            None,
                            "W tym terminie istnieje już rezerwacja dla wybranego pracownika.",
                        )
                    else:
                        reservation.save()
                        messages.success(request, "Twoja rezerwacja została dodana!")

    else:
        form = ReservationForm()

    return render(
        request,
        "reservations/reservation.html",
        context={"form": form, "employees": employees, "services": services},
    )
