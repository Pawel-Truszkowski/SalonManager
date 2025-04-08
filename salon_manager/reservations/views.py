import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, TemplateView, View
from formtools.wizard.views import SessionWizardView
from services.models import Service
from users.models import Employee
from utils.error_codes import ErrorCode

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


class ReservationWizard(LoginRequiredMixin, SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def post(self, *args, **kwargs):
        if "wizard_goto_step" in self.request.POST:
            return self.render_goto_step(self.request.POST["wizard_goto_step"])
        return super().post(self, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

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


# Przerobic na CBV
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

        except (WorkDay.DoesNotExist, Employee.DoesNotExist, Service.DoesNotExist):
            return JsonResponse({"times": [], "error": "Invalid selection"})

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
                res_end = datetime.datetime.combine(selected_date, reservation.end_time)

                if current_time < res_end and slot_end > res_start:
                    is_available = False
                    break

            if is_available:
                time_value = current_time.strftime("%H:%M")
                time_display = current_time.strftime("%I:%M %p")
                available_slots.append({"value": time_value, "display": time_display})

            current_time += datetime.timedelta(minutes=15)

        return JsonResponse({"times": available_slots})

    return JsonResponse({"times": []})


class ReservationSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "reservations/reservation_success.html"


class ReservationsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "reservations/reservation_list.html"
    model = Reservation
    context_object_name = "reservations"

    def get_queryset(self):
        return Reservation.objects.filter(customer=self.request.user)

    def test_func(self):
        return self.request.user.is_authenticated


class CancelReservationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs["pk"])
        if reservation.status != "CANCEL":
            reservation.status = "CANCEL"
            reservation.save()
            messages.success(request, "The reservation has been canceled")
        else:
            messages.warning(request, "The reservation has already been canceled")

        return redirect("your_reservation_list")


#################### Tworzenie nowej rezerwacji !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


def reservation_create(request, service_id):
    if service_id:
        service = Service.objects.get(id=service_id)
    return render(
        request, "reservations/reservation_create.html", context={"service": service}
    )


def get_available_slots_ajax(request):
    """This view function handles AJAX requests to get available slots for a selected date.

    :param request: The request instance.
    :return: A JSON response containing available slots, selected date, an error flag, and an optional error message.
    """

    slot_form = SlotForm(request.GET)
    error_code = 0
    if not slot_form.is_valid():
        custom_data = {"error": True, "available_slots": [], "date_chosen": ""}
        if "selected_date" in slot_form.errors:
            error_code = ErrorCode.PAST_DATE
        elif "staff_member" in slot_form.errors:
            error_code = ErrorCode.STAFF_ID_REQUIRED
        message = list(slot_form.errors.as_data().items())[0][1][0].messages[
            0
        ]  # dirty way to keep existing behavior
        return json_response(
            message=message,
            custom_data=custom_data,
            success=False,
            error_code=error_code,
        )

    selected_date = slot_form.cleaned_data["selected_date"]
    sm = slot_form.cleaned_data["staff_member"]
    date_chosen = selected_date.strftime("%a, %B %d, %Y")
    custom_data = {"date_chosen": date_chosen}

    days_off_exist = check_day_off_for_staff(staff_member=sm, date=selected_date)
    if days_off_exist:
        message = _("Day off. Please select another date!")
        custom_data["available_slots"] = []
        return json_response(
            message=message,
            custom_data=custom_data,
            success=False,
            error_code=ErrorCode.INVALID_DATE,
        )
    # if selected_date is not a working day for the staff, return an empty list of slots and 'message' is Day Off
    weekday_num = get_weekday_num_from_date(selected_date)
    is_working_day_ = is_working_day(staff_member=sm, day=weekday_num)

    custom_data["staff_member"] = sm.get_staff_member_name()
    if not is_working_day_:
        message = _(
            "Not a working day for {staff_member}. Please select another date!"
        ).format(staff_member=sm.get_staff_member_first_name())
        custom_data["available_slots"] = []
        return json_response(
            message=message,
            custom_data=custom_data,
            success=False,
            error_code=ErrorCode.INVALID_DATE,
        )
    available_slots = get_available_slots_for_staff(selected_date, sm)

    # Check if the selected_date is today and filter out past slots
    if selected_date == date.today():
        current_time = timezone.now().time()
        available_slots = [
            slot for slot in available_slots if slot.time() > current_time
        ]

    custom_data["available_slots"] = [
        slot.strftime("%I:%M %p") for slot in available_slots
    ]
    if len(available_slots) == 0:
        custom_data["error"] = True
        message = _("No availability")
        return json_response(
            message=message,
            custom_data=custom_data,
            success=False,
            error_code=ErrorCode.INVALID_DATE,
        )
    custom_data["error"] = False
    return json_response(
        message="Successfully retrieved available slots",
        custom_data=custom_data,
        success=True,
    )
