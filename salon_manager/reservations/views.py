from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from services.models import Service
from users.models import Employee

from .forms import ReservationForm
from .models import Reservation, WorkDay


@login_required
def reservation(request):
    employees = Employee.objects.all()
    services = Service.objects.all()

    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.customer = request.user
            print(reservation.employee_id)
            print("Employee:", reservation.employee_id, type(reservation.employee))
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
                        return redirect("reservation_success")
            print("Form errors:", form.errors)

    else:
        form = ReservationForm()

    return render(
        request,
        "reservations/reservation.html",
        context={"form": form, "employees": employees, "services": services},
    )


def reservation_success(request):
    return render(request, "reservations/reservation_success.html")
