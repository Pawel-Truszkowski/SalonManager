import json
from datetime import date, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from services.models import Service
from users.models import CustomUser, Employee
from utils.error_codes import ErrorCode
from utils.support_functions import (
    check_for_conflicting_reservation,
    generate_available_slots,
    handle_invalid_form,
    json_response,
)

from .forms import ClientDataForm, ReservationForm, ReservationRequestForm, SlotForm
from .models import Reservation, ReservationRequest, WorkDay
from .service import SlotAvailabilityService
from .tasks import send_reservation_notification


def get_available_slots_ajax(request):
    slot_form = SlotForm(request.GET)
    if not slot_form.is_valid():
        return handle_invalid_form(slot_form)

    selected_date = slot_form.cleaned_data["selected_date"]
    staff_member = slot_form.cleaned_data["staff_member"]
    service_id = slot_form.cleaned_data["service_id"]

    slot_service = SlotAvailabilityService()

    try:
        result = slot_service.get_available_slots(
            selected_date, staff_member, service_id
        )
        return json_response(
            message="Successfully retrieved available slots",
            custom_data=result,
            success=True,
        )
    except ValueError as e:
        return json_response(
            message=str(e),
            success=False,
            custom_data={
                "error": True,
                "available_slots": [],
                "date_chosen": selected_date.strftime("%a, %B %d, %Y"),
            },
            error_code=ErrorCode.INVALID_DATE,
        )


def get_next_available_date_ajax(request):
    staff_id = request.GET.get("staff_member")

    if staff_id and staff_id != "none":
        staff_member = get_object_or_404(Employee, pk=staff_id)

        current_date = date.today()

        working_days = WorkDay.objects.filter(
            employee=staff_member, date__gt=current_date
        ).order_by("date")
        next_available_date = None

        print("working days:", working_days)

        if not working_days.exists():
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
    try:
        staff_id_str = request.GET.get("staff_id")

        if not staff_id_str or staff_id_str == "none":
            return JsonResponse({"success": True, "non_working_days": []})

        staff_id = int(staff_id_str)

        try:
            employee = Employee.objects.get(id=staff_id)
        except Employee.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invalid staff member"})

        today = timezone.now().date()

        date_range = [today + timedelta(days=i) for i in range(60)]

        working_days = WorkDay.objects.filter(
            employee_id=employee.id,
            date__gte=today,
            date__lte=today + timedelta(days=60),
        ).values_list("date", flat=True)

        working_days = set(working_days)
        non_working_days = [
            d.strftime("%Y-%m-%d") for d in date_range if d not in working_days
        ]

        return JsonResponse({"success": True, "non_working_days": non_working_days})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


def reservation_request(request, service_id):
    service_categories = Service.objects.values_list(
        "category__name", flat=True
    ).distinct()
    staff_member = None

    context = {
        "service_categories": service_categories,
        "timezoneTxt": str(timezone.get_current_timezone()),
        "locale": "en",
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
    reservation_request_obj = get_object_or_404(
        ReservationRequest, pk=reservation_request_id
    )

    if request.session.get(f"reservation_submitted_{id_request}", False):
        context = {
            "user": request.user,
            "service_id": reservation_request_obj.service_id,
        }
        return render(
            request, "reservations/304_already_submitted.html", context=context
        )

    if request.method == "POST":
        reservation_form = ReservationForm(request.POST)
        client_data_form = ClientDataForm(request.POST)

        if reservation_form.is_valid() and client_data_form.is_valid():
            client_data = client_data_form.cleaned_data
            reservation_data = reservation_form.cleaned_data

            response = create_reservation(
                reservation_request_obj, id_request, client_data, reservation_data
            )

            if response:
                request.session.setdefault(f"reservation_submitted_{id_request}", True)
                return redirect("reservation_success")
            else:
                messages.error(
                    request,
                    _(
                        "There was an error creating your reservation. Please try again."
                    ),
                )
        else:
            print(reservation_form.errors, client_data_form.errors)
            messages.error(
                request,
                _(
                    "There was an error in your submission. Please check the form and try again."
                ),
            )

    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                "name": f"{request.user.first_name} {request.user.last_name}".strip(),
                "email": request.user.email,
                "phone": request.user.phone_number,
            }
        reservation_form = ReservationForm(initial=initial_data)
        client_data_form = ClientDataForm(initial=initial_data)

    context = {
        "reservation_request_id": reservation_request_id,
        "id_request": id_request,
        "ar": reservation_request_obj,
        "form": reservation_form,
        "client_data_form": client_data_form,
        "service_name": reservation_request_obj.service.name,
    }
    return render(
        request, "reservations/reservation_client_information.html", context=context
    )


def create_reservation(
    reservation_request_obj, id_request, client_data, reservation_data
):
    email = client_data["email"]
    name = client_data["name"]
    phone = reservation_data["phone"]
    additional_info = reservation_data["additional_info"]

    customer = CustomUser.objects.filter(email=email).first()

    Reservation.objects.update_or_create(
        reservation_request=reservation_request_obj,
        defaults={
            "customer": customer,
            "phone": phone,
            "id_request": id_request,
            "additional_info": additional_info,
            "email": email,
            "name": name,
        },
    )

    send_reservation_notification.delay_on_commit(
        customer=name,
        service=reservation_request_obj.service.name,
        date=reservation_request_obj.date,
        time=reservation_request_obj.start_time,
    )

    return True
