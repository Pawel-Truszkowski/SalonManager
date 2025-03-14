import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from formtools.wizard.views import SessionWizardView
from services.models import Service
from users.models import Employee

from . import forms
from .models import Reservation, WorkDay

FORMS = [
    ("customer", forms.CustomerInfoForm),
    ("select", forms.ReservationSelectionForm),
    ("confirm", forms.ConfirmationForm),
]


TEMPLATES = {
    "customer": "reservations/wizard/customer_info.html",
    "select": "reservations/wizard/reservation_select.html",
    "confirm": "reservations/wizard/confirmation.html",
}


@method_decorator(login_required, name="dispatch")
class ReservationWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def post(self, *args, **kwargs):
        if "wizard_goto_step" in self.request.POST:
            return self.render_goto_step(self.request.POST["wizard_goto_step"])
        return super().post(self, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if (
            self.steps.current != self.steps.last
            and "wizard_goto_step" in self.request.POST
        ):
            kwargs.update({"data": None})

        if step == "customer":
            kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == "confirm":
            select_data = self.get_cleaned_data_for_step("select")
            if select_data:
                service = select_data["service"]
                employee = select_data["employee"]
                date = select_data["reservation_date"]
                time = select_data["start_time"]

                time_obj = datetime.datetime.strptime(time, "%H:%M").time()

                start_datetime = datetime.datetime.combine(date, time_obj)
                duration = datetime.timedelta(minutes=service.duration)
                end_datetime = start_datetime + duration

                context.update(
                    {
                        "service": service,
                        "employee": employee,
                        "reservation_date": date,
                        "start_time": time_obj,
                        "end_time": end_datetime.time(),
                    }
                )

        return context

    def done(self, form_list, **kwargs):
        select_data = self.get_cleaned_data_for_step("select")

        time_str = select_data["start_time"]
        time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()

        reservation = Reservation(
            customer=self.request.user,
            service=select_data["service"],
            employee=select_data["employee"],
            reservation_date=select_data["reservation_date"],
            start_time=time_obj,
            status="PENDING",
        )

        reservation.save()

        messages.success(self.request, "Your appointment has been successfully booked!")
        return redirect("reservation_success")


@login_required
def get_employees(request):
    service_id = request.GET.get("service_id")
    if service_id:
        employees = Employee.objects.filter(services__id=service_id)
        return JsonResponse(
            {"employees": [{"id": emp.id, "name": emp.name} for emp in employees]}
        )
    return JsonResponse({"employees": []})


@login_required
def get_available_dates(request):
    employee_id = request.GET.get("employee_id")
    if employee_id:
        today = datetime.date.today()
        workdays = WorkDay.objects.filter(
            employee_id=employee_id,
            date__gte=today,
            date__lte=today + datetime.timedelta(days=30),
        ).order_by("date")

        return JsonResponse(
            {
                "dates": [
                    {
                        "date": workday.date.strftime("%Y-%m-%d"),
                        "display": workday.date.strftime("%A, %B %d, %Y"),
                    }
                    for workday in workdays
                ]
            }
        )
    return JsonResponse({"dates": []})


@login_required
def get_available_times(request):
    employee_id = request.GET.get("employee_id")
    service_id = request.GET.get("service_id")
    date_str = request.GET.get("date")

    if all([employee_id, service_id, date_str]):
        try:
            selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            employee = Employee.objects.get(id=employee_id)
            service = Service.objects.get(id=service_id)
            workday = WorkDay.objects.get(employee=employee, date=selected_date)

            existing_reservations = Reservation.objects.filter(
                employee=employee,
                reservation_date=selected_date,
                status__in=["PENDING", "CONFIRMED"],
            )

            # Generate time slots
            available_slots = []
            service_duration = datetime.timedelta(minutes=service.duration)

            current_time = datetime.datetime.combine(selected_date, workday.start_time)
            end_time = datetime.datetime.combine(selected_date, workday.end_time)

            while current_time + service_duration <= end_time:
                slot_end = current_time + service_duration
                is_available = True

                for reservation in existing_reservations:
                    res_start = datetime.datetime.combine(
                        selected_date, reservation.start_time
                    )
                    res_end = datetime.datetime.combine(
                        selected_date, reservation.end_time
                    )

                    if current_time < res_end and slot_end > res_start:
                        is_available = False
                        break

                if is_available:
                    time_value = current_time.strftime("%H:%M")
                    time_display = current_time.strftime("%I:%M %p")
                    available_slots.append(
                        {"value": time_value, "display": time_display}
                    )

                # Move to next 15-minute slot
                current_time += datetime.timedelta(minutes=15)

            return JsonResponse({"times": available_slots})

        except (WorkDay.DoesNotExist, Employee.DoesNotExist, Service.DoesNotExist):
            return JsonResponse({"times": [], "error": "Invalid selection"})

    return JsonResponse({"times": []})


@login_required(redirect_field_name="login")
def reservation_success(request):
    return render(request, "reservations/reservation_success.html")
