import logging
from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from services.models import Service
from users.models import CustomUser, Employee
from utils.support_functions import (
    _build_request_reservation_context,
    _calculate_non_working_days,
    check_for_conflicting_reservation,
    generate_available_slots,
    handle_invalid_form,
    json_response,
)

from .forms import ClientDataForm, ReservationForm, ReservationRequestForm
from .models import Reservation, ReservationRequest
from .tasks import send_reservation_notification

logger = logging.getLogger(__name__)


def reservation_request(request: HttpRequest, service_id: int) -> HttpResponse:
    service = get_object_or_404(Service, id=service_id)
    context = _build_request_reservation_context(request, service)

    if request.method == "POST":
        form = ReservationRequestForm(request.POST)
        if form.is_valid():
            reservation_request = form.save()
            request.session[
                f"reservation_completed_{reservation_request.id_request}"
            ] = False
            return redirect(
                "reservation_client_information",
                reservation_request_id=reservation_request.id,
                id_request=reservation_request.id_request,
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

    context["form"] = form
    return render(request, "reservations/reservation_create.html", context)


def reservation_client_information(
    request: HttpRequest, reservation_request_id: int, id_request: int
) -> HttpResponse:
    reservation_request_obj = get_object_or_404(
        ReservationRequest, pk=reservation_request_id
    )

    if request.session.get(f"reservation_completed_{id_request}", False):
        context = {
            "user": request.user,
            "service_id": reservation_request_obj.service.id,
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
                request.session.setdefault(f"reservation_completed_{id_request}", True)
                return redirect("reservation_success")
            else:
                messages.error(
                    request,
                    _(
                        "There was an error creating your reservation. Please try again."
                    ),
                )
        else:
            messages.error(
                request,
                _(
                    "There was an error in your submission. Please check the form and try again."
                ),
            )

    else:
        initial_data = {}
        if request.user.is_authenticated and isinstance(request.user, CustomUser):
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
    reservation_request_obj: ReservationRequest,
    id_request: int,
    client_data: dict[str, Any],
    reservation_data: dict[str, Any],
) -> Reservation:
    email = client_data["email"]
    name = client_data["name"]
    phone = reservation_data["phone"]
    additional_info = reservation_data["additional_info"]

    customer = CustomUser.objects.filter(email=email).first()

    reservation = Reservation.objects.create(
        reservation_request=reservation_request_obj,
        customer=customer,
        phone=phone,
        id_request=id_request,
        additional_info=additional_info,
        email=email,
        name=name,
    )

    try:
        send_reservation_notification.delay_on_commit(  # type: ignore[attr-defined]
            customer=name,
            service=reservation_request_obj.service.name,
            date=reservation_request_obj.date,
            time=reservation_request_obj.start_time,
        )
    except Exception as e:
        logger.exception(f"Exception occurred: {e}")

    return reservation
