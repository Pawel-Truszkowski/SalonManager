import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from services.models import Service
from users.models import Employee

from .models import Reservation, WorkDay


def reservation_wizard(request, service_id):
    """Reservation wizard page with calendar and available slots"""
    service_categories = Service.objects.values("category__name").distinct()

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

    # Get employees who provide this service
    context["all_staff_members"] = Employee.objects.filter(services=service)

    return render(request, "reservations/reservation_create.html", context)


@require_POST
def available_slots_ajax(request):
    """AJAX endpoint to get available time slots for a specific date and staff member"""
    try:
        data = json.loads(request.body)
        date_str = data.get("date")
        staff_id = data.get("staff_id")
        service_id = data.get("service_id")

        # Validate required parameters
        if not all([date_str, staff_id, service_id]):
            return JsonResponse(
                {"success": False, "message": "Missing required parameters"}
            )

        # Convert date string to date object
        date_only = date_str[:10]
        selected_date = datetime.datetime.strptime(date_only, "%Y-%m-%d").date()

        # Check if date is in past
        if selected_date < timezone.now().date():
            return JsonResponse(
                {"success": False, "message": "Selected date is in the past"}
            )

        # Get staff member and service
        try:
            employee = Employee.objects.get(id=staff_id)
            service = Service.objects.get(id=service_id)
        except (Employee.DoesNotExist, Service.DoesNotExist):
            return JsonResponse(
                {"success": False, "message": "Invalid staff member or service"}
            )

        # Check if employee provides this service
        if service not in employee.services.all():
            return JsonResponse(
                {
                    "success": False,
                    "message": "This staff member does not provide the selected service",
                }
            )

        # Get work day for the employee on the selected date
        try:
            work_day = WorkDay.objects.get(employee=employee, date=selected_date)
        except WorkDay.DoesNotExist:
            return JsonResponse({"success": True, "slots": []})

        # Get existing reservations for the date
        existing_reservations = Reservation.objects.filter(
            employee=employee,
            reservation_date=selected_date,
            status__in=["PENDING", "CONFIRMED"],
        )

        # Calculate service duration in minutes
        service_duration = service.duration

        # Generate time slots based on work hours
        available_slots = generate_available_slots(
            work_day.start_time,
            work_day.end_time,
            service_duration,
            existing_reservations,
        )

        return JsonResponse({"success": True, "slots": available_slots})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"error: {str(e)}"})


@require_POST
def get_non_working_days_ajax(request):
    """AJAX endpoint to get days when staff member is not working"""
    try:
        data = json.loads(request.body)
        staff_id = data.get("staff_id")

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
        date_range = [today + datetime.timedelta(days=i) for i in range(60)]

        # Get days employee is working
        working_days = WorkDay.objects.filter(
            employee=employee,
            date__gte=today,
            date__lte=today + datetime.timedelta(days=60),
        ).values_list("date", flat=True)

        # Calculate non-working days
        non_working_days = [
            d.strftime("%Y-%m-%d") for d in date_range if d not in working_days
        ]
        # print(non_working_days)
        return JsonResponse({"success": True, "non_working_days": non_working_days})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# @login_required
@require_POST
def appointment_request_submit(request):
    """Handle appointment request submission"""
    # Get form data
    service_id = request.POST.get("service_id")
    staff_id = request.POST.get("staff_member")
    date_selected = request.POST.get("date_selected")
    time_selected = request.POST.get("time_selected")

    date_selected = date_selected.split("T")[0]

    # Validate required fields
    if not all([service_id, staff_id, date_selected, time_selected]):
        return JsonResponse({"success": False, "message": "Missing required fields"})

    try:
        # Get service and employee
        service = Service.objects.get(id=service_id)
        employee = Employee.objects.get(id=staff_id)

        # Convert date and time strings to datetime objects
        reservation_date = datetime.datetime.strptime(date_selected, "%Y-%m-%d").date()
        start_time = datetime.datetime.strptime(time_selected, "%H:%M").time()

        # Check if there's a conflicting reservation
        conflicting_reservation = check_for_conflicting_reservation(
            employee, reservation_date, start_time, service.duration
        )

        if conflicting_reservation:
            return JsonResponse(
                {
                    "success": False,
                    "message": "This time slot is no longer available. Please select another time.",
                }
            )

        # Create the reservation
        reservation = Reservation.objects.create(
            customer=request.user,
            employee=employee,
            service=service,
            reservation_date=reservation_date,
            start_time=start_time,
            status="PENDING",
        )

        # Return success with redirect URL
        return JsonResponse(
            {"success": True, "redirect_url": reverse("reservation_success")}
        )

    except (Service.DoesNotExist, Employee.DoesNotExist):
        return JsonResponse(
            {"success": False, "message": "Invalid service or staff member"}
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"An error occurred: {str(e)}"}
        )


@login_required
def request_next_available_slot(request, service_id):
    """Redirect to reservation page with next available slot info"""
    try:
        service = Service.objects.get(id=service_id)

        # You could implement logic here to find the next available slot
        # For now, we'll just redirect to the reservation wizard

        messages.info(request, "Please contact us for the next available slot.")
        return redirect(reverse("reservation_wizard") + f"?service_id={service_id}")

    except Service.DoesNotExist:
        messages.error(request, "Service not found.")
        return redirect("services_list")


@login_required
@require_POST
def reschedule_appointment_submit(request):
    """Handle appointment rescheduling"""
    appointment_id = request.POST.get("appointment_request_id")
    date_selected = request.POST.get("date_selected")
    time_selected = request.POST.get("time_selected")
    reason = request.POST.get("reason_for_rescheduling", "")

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
        new_date = datetime.datetime.strptime(date_selected, "%Y-%m-%d").date()
        new_time = datetime.datetime.strptime(time_selected, "%H:%M").time()

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
    base_date = datetime.datetime.now().date()
    start_datetime = datetime.datetime.combine(base_date, start_time)
    end_datetime = datetime.datetime.combine(base_date, end_time)

    # Calculate slot duration in minutes
    # Adding 15 minutes buffer between appointments
    slot_duration = datetime.timedelta(minutes=service_duration + 15)

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

    while (
        current_slot_start + datetime.timedelta(minutes=service_duration)
        <= end_datetime
    ):
        # Calculate slot end time
        current_slot_end = current_slot_start + datetime.timedelta(
            minutes=service_duration
        )

        # Check if slot overlaps with any existing reservation
        is_available = True
        for start, end in booked_slots:
            # Convert all times to comparable format
            res_start = datetime.datetime.combine(base_date, start)
            res_end = datetime.datetime.combine(base_date, end)

            # Check for overlap
            if current_slot_start <= res_end and current_slot_end >= res_start:
                is_available = False
                break

        # If slot is available, add to list
        if is_available:
            available_slots.append(current_slot_start.strftime("%H:%M"))

        # Move to next potential slot (15-minute intervals)
        current_slot_start += slot_duration

    return available_slots


def check_for_conflicting_reservation(
    employee, date, start_time, duration, exclude_id=None
) -> bool:
    """Check if there's a conflicting reservation"""
    # Calculate end time
    start_datetime = datetime.datetime.combine(date, start_time)
    end_datetime = start_datetime + datetime.timedelta(minutes=duration)
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
