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
    json_response,
)

from .forms import ClientDataForm, ReservationForm, ReservationRequestForm, SlotForm
from .models import Reservation, ReservationRequest, WorkDay


def get_available_slots_ajax(request):
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
    )
    work_day = WorkDay.objects.get(employee=sm.id, date=selected_date)

    available_slots = generate_available_slots(
        work_day.start_time, work_day.end_time, service_duration, existing_reservations
    )

    if selected_date == date.today():
        current_time = timezone.now().time().strftime("%H:%M")
        available_slots = [slot for slot in available_slots if slot > current_time]

    custom_data["available_slots"] = available_slots
    if not available_slots:
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

    reservation = Reservation(
        customer=customer,
        phone=phone,
        reservation_request=reservation_request_obj,
        id_request=id_request,
        additional_info=additional_info,
        email=email,
        name=name,
    )

    reservation.save()

    return True
