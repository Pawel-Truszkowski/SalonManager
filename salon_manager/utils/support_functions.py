import uuid
from datetime import date, datetime, time, timedelta
from typing import List

from django.http import JsonResponse
from django.utils import timezone


def generate_available_slots(
    start_time, end_time, service_duration, existing_reservations
) -> List[str]:
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
    employee,
    reservation_date,
    start_time,
    duration,
    conflicting_reservations,
    exclude_id=None,
) -> bool:
    """Check if there's a conflicting reservation"""
    # Calculate end time
    start_datetime = datetime.combine(reservation_date, start_time)
    end_datetime = start_datetime + timedelta(minutes=duration)
    end_time = end_datetime.time()

    # Exclude current reservation if updating
    if exclude_id:
        conflicting_reservations = conflicting_reservations.exclude(id=exclude_id)

    # Check for time conflicts
    for reservation in conflicting_reservations:
        res_start = reservation.start_time
        res_end = reservation.end_time

        # Check if slots overlap
        if start_time < res_end and end_time > res_start:
            return True

    return False


def json_response(
    message, status=200, success=True, custom_data=None, error_code=None, **kwargs
):
    """Return a generic JSON response."""
    response_data = {"message": message, "success": success}
    if error_code:
        response_data["errorCode"] = error_code.value
    if custom_data:
        response_data.update(custom_data)
    return JsonResponse(response_data, status=status, **kwargs)


def generate_random_id() -> str:
    """Generate a random UUID and return it as a hexadecimal string."""

    return uuid.uuid4().hex


def get_timestamp() -> str:
    """Get the current timestamp as a string without the decimal part.

    :return: The current timestamp (e.g. "1612345678")
    """
    timestamp = str(timezone.now().timestamp())
    return timestamp.replace(".", "")


def time_difference(time1, time2) -> timedelta:
    # If inputs are datetime.time objects, convert them to datetime.datetime objects for the same day
    if isinstance(time1, time) and isinstance(time2, time):
        today = datetime.today()
        datetime1 = datetime.combine(today, time1)
        datetime2 = datetime.combine(today, time2)
    elif isinstance(time1, datetime) and isinstance(time2, datetime):
        datetime1 = time1
        datetime2 = time2
    else:
        raise ValueError(
            "Both inputs should be of the same type, either datetime.time or datetime.datetime"
        )

    # Check if datetime2 is earlier than datetime1
    if datetime2 < datetime1:
        raise ValueError(
            "The second time provided (time2) should not be earlier than the first time (time1)."
        )

    # Find the difference
    delta = datetime2 - datetime1

    return delta
