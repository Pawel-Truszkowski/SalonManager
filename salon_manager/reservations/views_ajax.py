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
from users.models import Employee
from utils.db_helpers import get_weekday_num_from_date, json_response
from utils.error_codes import ErrorCode

from .forms import ReservationRequestForm, SlotForm
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
    """This view function handles AJAX requests to get the next available date for a service.

    :param request: The request instance.
    :return: A JSON response containing the next available date.
    """
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

    # Get service id from URL parameters
    # service_id = request.GET.get('service_id')
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


# @require_POST
# def appointment_request_submit(request):
#     """Handle appointment request submission"""
#     # Get form data
#     service_id = request.POST.get("service_id")
#     staff_id = request.POST.get("staff_member")
#     date_selected = request.POST.get("date_selected")
#     time_selected = request.POST.get("time_selected")
#     print(date_selected, time_selected)
#     date_selected = date_selected.split("T")[0]
#
#     # Validate required fields
#     if not all([service_id, staff_id, date_selected, time_selected]):
#         return JsonResponse({"success": False, "message": "Missing required fields"})
#
#     try:
#         # Get service and employee
#         service = Service.objects.get(id=service_id)
#         employee = Employee.objects.get(id=staff_id)
#
#         # Convert date and time strings to datetime objects
#         reservation_date = datetime.strptime(date_selected, "%Y-%m-%d").date()
#         start_time = datetime.strptime(time_selected, "%H:%M").time()
#
#         # Check if there's a conflicting reservation
#         conflicting_reservation = check_for_conflicting_reservation(
#             employee, reservation_date, start_time, service.duration
#         )
#
#         if conflicting_reservation:
#             return JsonResponse(
#                 {
#                     "success": False,
#                     "message": "This time slot is no longer available. Please select another time.",
#                 }
#             )
#
#         # Create the reservation
#         Reservation.objects.create(
#             customer=request.user,
#             employee=employee,
#             service=service,
#             reservation_date=reservation_date,
#             start_time=start_time,
#             status="PENDING",
#         )
#
#         # Return success with redirect URL
#         return JsonResponse(
#             {"success": True, "redirect_url": reverse("reservation_success")}
#         )
#
#     except (Service.DoesNotExist, Employee.DoesNotExist):
#         return JsonResponse(
#             {"success": False, "message": "Invalid service or staff member"}
#         )
#     except Exception as e:
#         return JsonResponse(
#             {"success": False, "message": f"An error occurred: {str(e)}"}
#         )


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

    ar = ReservationRequest.objects.get(id_request=id_request)

    context = {
        "reservation_request_id": reservation_request_id,
        "id_request": id_request,
        "ar": ar,
    }
    return render(
        request, "reservations/reservation_client_information.html", context=context
    )


@login_required
@require_POST
def reschedule_appointment_submit(request):
    """Handle appointment rescheduling"""
    appointment_id = request.POST.get("appointment_request_id")
    date_selected = request.POST.get("date_selected")
    time_selected = request.POST.get("time_selected")
    # reason = request.POST.get("reason_for_rescheduling", "")

    # Validate required fields
    if not all([appointment_id, date_selected, time_selected]):
        return JsonResponse({"success": False, "message": "Missing required fields"})

    try:
        # Get the reservation
        reservation = get_object_or_404(Reservation, id=appointment_id)

        # Check if user owns this reservation
        if reservation.customer != request.user:
            return JsonResponse(
                {
                    "success": False,
                    "message": "You do not have permission to reschedule this appointment",
                }
            )

        # Convert date and time strings to datetime objects
        new_date = datetime.strptime(date_selected, "%Y-%m-%d").date()
        new_time = datetime.strptime(time_selected, "%H:%M").time()

        # Check for conflicting reservations
        conflicting_reservation = check_for_conflicting_reservation(
            reservation.employee,
            new_date,
            new_time,
            reservation.service.duration,
            exclude_id=reservation.id,
        )

        if conflicting_reservation:
            return JsonResponse(
                {
                    "success": False,
                    "message": "This time slot is no longer available. Please select another time.",
                }
            )

        # Update the reservation
        reservation.reservation_date = new_date
        reservation.start_time = new_time
        reservation.save()

        # Record rescheduling reason (you might want to create a model for this)
        # RescheduleReason.objects.create(reservation=reservation, reason=reason)

        # Return success with redirect URL
        return JsonResponse(
            {"success": True, "redirect_url": reverse("your_reservation_list")}
        )

    except Reservation.DoesNotExist:
        return JsonResponse({"success": False, "message": "Appointment not found"})
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"An error occurred: {str(e)}"}
        )


# Helper functions
def generate_available_slots(
    start_time, end_time, service_duration, existing_reservations
):
    """Generate available time slots based on work hours and existing reservations"""
    # Convert times to datetime for easier manipulation
    base_date = datetime.now().date()
    start_datetime = datetime.combine(base_date, start_time)
    end_datetime = datetime.combine(base_date, end_time)

    # Calculate slot duration in minutes
    # Adding 15 minutes buffer between appointments
    # slot_duration = timedelta(minutes=service_duration + 15)

    # Create a list of existing reservation times
    booked_slots = []
    for reservation in existing_reservations:
        start = reservation.start_time
        # Calculate end time using the property from the model
        end = reservation.end_time
        booked_slots.append((start, end))

    # Generate potential slots
    available_slots = []
    current_slot_start = start_datetime

    while current_slot_start + timedelta(minutes=service_duration) <= end_datetime:
        # Calculate slot end time
        current_slot_end = current_slot_start + timedelta(minutes=service_duration)

        # Check if slot overlaps with any existing reservation
        is_available = True
        for start, end in booked_slots:
            # Convert all times to comparable format
            res_start = datetime.combine(base_date, start)
            res_end = datetime.combine(base_date, end)

            # Check for overlap
            if current_slot_start <= res_end and current_slot_end >= res_start:
                is_available = False
                break

        # If slot is available, add to list
        if is_available:
            available_slots.append(current_slot_start.strftime("%H:%M"))

        # Move to next potential slot (15-minute intervals)
        current_slot_start += timedelta(minutes=15)
    return available_slots


def check_for_conflicting_reservation(
    employee, date, start_time, duration, exclude_id=None
) -> bool:
    """Check if there's a conflicting reservation"""
    # Calculate end time
    start_datetime = datetime.combine(date, start_time)
    end_datetime = start_datetime + timedelta(minutes=duration)
    end_time = end_datetime.time()

    # Query for conflicting reservations
    conflicting_query = Reservation.objects.filter(
        employee=employee, reservation_date=date, status__in=["PENDING", "CONFIRMED"]
    )

    # Exclude current reservation if updating
    if exclude_id:
        conflicting_query = conflicting_query.exclude(id=exclude_id)

    # Check for time conflicts
    for reservation in conflicting_query:
        res_start = reservation.start_time
        res_end = reservation.end_time

        # Check if slots overlap
        if start_time < res_end and end_time > res_start:
            return True

    return False
