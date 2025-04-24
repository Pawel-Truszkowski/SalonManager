import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from formtools.wizard.views import SessionWizardView
from services.models import Service
from users.models import CustomUser, Employee
from utils.db_helpers import (
    check_for_conflicting_reservation,
    generate_available_slots,
    json_response,
)
from utils.error_codes import ErrorCode

from .forms import ClientDataForm, ReservationForm, ReservationRequestForm, SlotForm
from .models import Reservation, ReservationRequest, WorkDay


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
        message = list(slot_form.errors.as_data().items())[0][1][0].messages[0]
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
    service_id = slot_form.cleaned_data["service_id"]

    # days_off_exist = check_day_off_for_staff(staff_member=sm, date=selected_date)
    working_day_exists = WorkDay.objects.filter(
        employee=sm.id, date=selected_date
    ).exists()
    if not working_day_exists:
        message = _("Day off. Please select another date!")
        custom_data["available_slots"] = []
        return json_response(
            message=message,
            custom_data=custom_data,
            success=False,
            error_code=ErrorCode.INVALID_DATE,
        )

    custom_data["staff_member"] = sm.name

    service = Service.objects.get(id=service_id)
    service_duration = service.duration

    existing_reservations = ReservationRequest.objects.filter(
        employee=sm.id,
        date=selected_date,
        # status__in=["PENDING", "CONFIRMED"],
    )
    work_day = WorkDay.objects.get(employee=sm.id, date=selected_date)

    available_slots = generate_available_slots(
        work_day.start_time, work_day.end_time, service_duration, existing_reservations
    )

    if selected_date == date.today():
        current_time = timezone.now().time()
        available_slots = [
            slot for slot in available_slots if slot.time() > current_time
        ]

    custom_data["available_slots"] = available_slots
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


def get_next_available_date_ajax(request):
    """This view function handles AJAX requests to get the next available date for a service."""

    staff_id = request.GET.get("staff_member")

    # If staff_id is not provided, you should handle it accordingly.
    if staff_id and staff_id != "none":
        staff_member = get_object_or_404(Employee, pk=staff_id)

        current_date = date.today()
        working_days = WorkDay.objects.filter(employee=staff_member).filter(
            Q(date__gt=current_date)
        )
        next_available_date = None

        if not working_days:
            message = _("No available dates.")
            data = {"next_available_date": next_available_date}
            return json_response(message=message, custom_data=data, success=True)

        next_available_date = working_days[0].date

        message = _("Successfully retrieved next available date")
        data = {"next_available_date": next_available_date.isoformat()}
        return json_response(message=message, custom_data=data, success=True)
    else:
        data = {"error": True}
        message = _("No staff member selected")
        return json_response(
            message=message,
            custom_data=data,
            success=False,
            error_code=ErrorCode.STAFF_ID_REQUIRED,
        )


def get_non_working_days_ajax(request):
    """AJAX endpoint to get days when staff member is not working"""
    try:
        staff_id = int(request.GET.get("staff_id"))

        # If no staff selected, return empty list
        if not staff_id or staff_id == "none":
            return JsonResponse({"success": True, "non_working_days": []})

        # Get staff member
        try:
            employee = Employee.objects.get(id=staff_id)
        except Employee.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invalid staff member"})

        # Get current date
        today = timezone.now().date()

        # Get next 60 days
        date_range = [today + timedelta(days=i) for i in range(60)]

        # Get days employee is working
        working_days = WorkDay.objects.filter(
            employee_id=employee.id,
            date__gte=today,
            date__lte=today + timedelta(days=60),
        ).values_list("date", flat=True)

        # Calculate non-working days
        non_working_days = [
            d.strftime("%Y-%m-%d") for d in date_range if d not in working_days
        ]

        return JsonResponse({"success": True, "non_working_days": non_working_days})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def reservation_request(request, service_id):
    """Reservation wizard page with calendar and available slots"""
    service_categories = Service.objects.values("category__name").distinct()

    service = None
    staff_member = None
    all_staff_members = None

    context = {
        "service_categories": service_categories,
        "timezoneTxt": str(timezone.get_current_timezone()),
        "locale": "en",  # You can make this dynamic based on user preferences
    }

    if service_id:
        try:
            service = Service.objects.get(id=service_id)
            context["service"] = service
        except Service.DoesNotExist:
            messages.error(request, "Service not found.")
            return redirect("services_list")
    else:
        messages.error(request, "No service selected.")
        return redirect("services_list")

    all_staff_members = Employee.objects.filter(services=service)

    if all_staff_members.count() == 1:
        staff_member = all_staff_members.first()

    context["all_staff_members"] = all_staff_members
    context["staff_member"] = staff_member
    context["date_chosen"] = date.today().strftime("%a, %B %d, %Y")

    return render(request, "reservations/reservation_create.html", context)


def reservation_request_submit(request):
    if request.method == "POST":
        print(request.POST.dict())
        form = ReservationRequestForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data["employee"]
            employee_exists = Employee.objects.filter(id=employee.id).exists()
            if not employee_exists:
                messages.error(request, _("Selected staff member does not exist."))
            else:
                ar = form.save()
                request.session[f"reservation_completed_{ar.id_request}"] = False
                return redirect(
                    "reservation_client_information",
                    reservation_request_id=ar.id,
                    id_request=ar.id_request,
                )
        else:
            print("Error: ", form.errors)
            messages.error(
                request,
                _(
                    "There was an error in your submission. Please check the form and try again."
                ),
            )
    else:
        form = ReservationRequestForm()

    return render(
        request, "reservations/reservation_create.html", context={"form": form}
    )


def reservation_client_information(request, reservation_request_id, id_request):
    """This view function handles client information submission for an appointment.

    :param request: The request instance.
    :param reservation_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """

    ar = get_object_or_404(ReservationRequest, pk=reservation_request_id)

    if request.session.get(f"reservation_submitted_{id_request}", False):
        context = {"user": request.user, "service_id": ar.service_id}
        return redirect(
            request, "reservations/304_already_submitted.html", context=context
        )

    if request.method == "POST":
        reservation_form = ReservationForm(request.POST)
        client_data_form = ClientDataForm(request.POST)

        if reservation_form.is_valid() and client_data_form.is_valid():
            client_data = client_data_form.cleaned_data
            reservation_data = reservation_form.cleaned_data

            response = create_reservation(ar, client_data, reservation_data)

            return response
    else:
        reservation_form = ReservationForm()
        client_data_form = ClientDataForm(request.POST)

    context = {
        "reservation_request_id": reservation_request_id,
        "id_request": id_request,
        "ar": ar,
        "form": reservation_form,
        "client_data_form": client_data_form,
        "service_name": ar.service.name,
    }
    return render(
        request, "reservations/reservation_client_information.html", context=context
    )


def create_reservation(reservation_request_obj, client_data, reservation_data):
    date = reservation_request_obj["date"]
    start_time = reservation_request_obj["start_time"]
    end_time = reservation_request_obj["end_time"]

    email = client_data["email"]
    customer = CustomUser.objects.get(email=email)

    reservation = Reservation(date=date)

    return redirect("reservation_success")
