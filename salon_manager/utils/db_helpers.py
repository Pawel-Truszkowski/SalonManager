import datetime
import uuid

from django.http import JsonResponse
from django.utils import timezone


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


def get_weekday_num_from_date(date: datetime.date = None) -> int:
    """Get the number of the weekday from the given date."""
    if date is None:
        date = datetime.date.today()
    return get_weekday_num(date.strftime("%A"))


def get_weekday_num(weekday: str) -> int:
    """Get the number of the weekday.

    :param weekday: The weekday (e.g. "Monday", "Tuesday", etc.)
    :return: The number of the weekday (0 for Sunday, 1 for Monday, etc.)
    """
    weekdays = {
        "monday": 1,
        "tuesday": 2,
        "wednesday": 3,
        "thursday": 4,
        "friday": 5,
        "saturday": 6,
        "sunday": 0,
    }
    return weekdays.get(weekday.lower(), -1)


def generate_random_id() -> str:
    """Generate a random UUID and return it as a hexadecimal string.

    :return: The randomly generated UUID as a hex string
    """
    return uuid.uuid4().hex


def get_timestamp() -> str:
    """Get the current timestamp as a string without the decimal part.

    :return: The current timestamp (e.g. "1612345678")
    """
    timestamp = str(timezone.now().timestamp())
    return timestamp.replace(".", "")


def time_difference(time1, time2):
    # If inputs are datetime.time objects, convert them to datetime.datetime objects for the same day
    if isinstance(time1, datetime.time) and isinstance(time2, datetime.time):
        today = datetime.datetime.today()
        datetime1 = datetime.datetime.combine(today, time1)
        datetime2 = datetime.datetime.combine(today, time2)
    elif isinstance(time1, datetime.datetime) and isinstance(time2, datetime.datetime):
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
