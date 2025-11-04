import logging
from datetime import date

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.translation import gettext as _
from users.models import CustomUser, Employee
from utils.error_codes import ErrorCode
from utils.support_functions import (
    _build_request_reservation_context,
    _calculate_non_working_days,
    check_for_conflicting_reservation,
    generate_available_slots,
    handle_invalid_form,
    json_response,
)

from .forms import SlotForm
from .service import SlotAvailabilityService

logger = logging.getLogger(__name__)


def get_available_slots(request):
    slot_form = SlotForm(request.GET)
    if not slot_form.is_valid():
        return handle_invalid_form(slot_form)

    selected_date = slot_form.cleaned_data["selected_date"]
    staff_member = slot_form.cleaned_data["staff_member"]
    service_id = slot_form.cleaned_data["service_id"]

    slot_service = SlotAvailabilityService()

    try:
        result = slot_service.get_available_slots_(
            selected_date, staff_member, service_id
        )
        return json_response(
            message="Successfully retrieved available slots",
            custom_data=result,
            success=True,
        )
    except ValueError as e:
        result = {
            "error": True,
            "available_slots": [],
            "date_chosen": selected_date.strftime("%a, %B %d, %Y"),
        }
        return json_response(
            message=str(e),
            success=False,
            custom_data=result,
            error_code=ErrorCode.INVALID_DATE,
        )


def get_next_available_date(request: HttpRequest, service_id) -> JsonResponse:
    staff_id = request.GET.get("staff_member")

    if not staff_id or staff_id.lower() == "none":
        data = {"error": True, "next_available_date": ""}
        message = _("No staff member selected")
        return json_response(
            message=message,
            custom_data=data,
            success=False,
            error_code=ErrorCode.STAFF_ID_REQUIRED,
        )

    try:
        employee = Employee.objects.get(pk=staff_id)
    except Employee.DoesNotExist:
        return json_response(
            message=_("Staff member not found"),
            custom_data={"error": True, "next_available_date": ""},
            success=False,
            error_code=ErrorCode.STAFF_MEMBER_NOT_FOUND,
        )

    current_date = date.today()
    slot_service = SlotAvailabilityService()

    try:
        next_date = slot_service.get_next_available_date(
            employee=employee, service_id=service_id, from_date=current_date
        )

        if not next_date:
            raise ValueError(_("No available slots found"))

        return json_response(
            message=_("Successfully retrieved next available date"),
            custom_data={"next_available_date": next_date.isoformat()},
            success=True,
        )
    except ValueError as e:
        return json_response(
            message=str(e),
            custom_data={"error": True, "next_available_date": ""},
            success=False,
            error_code=ErrorCode.NO_AVAILABLE_SLOTS,
        )


def get_non_working_days(request):
    staff_id = request.GET.get("staff_id")

    if not staff_id or staff_id.lower() == "none":
        return json_response(
            message=_("No staff member selected"),
            success=False,
            error_code=ErrorCode.STAFF_ID_REQUIRED,
        )

    try:
        staff_id_int = int(staff_id)
    except (ValueError, TypeError):
        return json_response(
            message=_("Invalid staff ID format"),
            success=False,
            error_code=ErrorCode.STAFF_MEMBER_NOT_FOUND,
        )

    try:
        employee = Employee.objects.get(id=staff_id_int)
    except Employee.DoesNotExist:
        return json_response(
            message=_("Staff member not found"),
            success=False,
            error_code=ErrorCode.STAFF_MEMBER_NOT_FOUND,
        )

    non_working_days = _calculate_non_working_days(employee=employee, days_ahead=60)

    return json_response(
        message=_("Successfully retrieved non-working days"),
        success=True,
        custom_data={"non_working_days": non_working_days},
    )
