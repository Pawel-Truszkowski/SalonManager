import json
import logging
from datetime import datetime, timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from users.models import Employee
from utils.mixins import OwnerRequiredMixin

from .forms import ClientDataForm, ReservationForm, ReservationRequestForm, WorkDayForm
from .models import Reservation, WorkDay
from .tasks import send_confirmation_email

logger = logging.getLogger(__name__)


class ReservationSuccessView(TemplateView):
    template_name = "reservations/reservation_success.html"


class UserReservationsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "reservations/reservation_list.html"
    model = Reservation
    context_object_name = "reservations"

    def get_queryset(self) -> QuerySet[Reservation]:
        return Reservation.objects.filter(customer=self.request.user).order_by(
            "-reservation_request__date"
        )

    def test_func(self) -> bool:
        return self.request.user.is_authenticated


class CancelUserReservationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        reservation = get_object_or_404(Reservation, id=self.kwargs["pk"])
        if reservation.status != "CANCELLED":
            reservation.status = "CANCELLED"
            reservation.save()
            messages.success(request, "The reservation has been canceled!")
        else:
            messages.info(request, "The reservation has already been canceled.")

        return redirect("user_reservations_list")

    def test_func(self) -> bool:
        return self.request.user.is_authenticated


# WorkDay Management ###################
class WorkDayListView(OwnerRequiredMixin, ListView):
    model = WorkDay
    template_name = "reservations/workday_list.html"
    context_object_name = "workdays"

    def get_queryset(self) -> QuerySet[WorkDay]:
        return WorkDay.objects.all().order_by("-date")


class WorkDayCreateView(OwnerRequiredMixin, CreateView):
    model = WorkDay
    form_class = WorkDayForm
    template_name = "reservations/workday_form.html"
    success_url = reverse_lazy("workday_list")

    def form_valid(self, form: WorkDayForm) -> HttpResponse:
        messages.success(self.request, "Work day created successfully!")
        return super().form_valid(form)


class WorkDayUpdateView(OwnerRequiredMixin, UpdateView):
    model = WorkDay
    form_class = WorkDayForm
    template_name = "reservations/workday_form.html"
    success_url = reverse_lazy("workday_list")

    def form_valid(self, form: WorkDayForm) -> HttpResponse:
        is_ajax = self.request.headers.get("x-requested-with") == "XMLHttpRequest"

        if is_ajax:
            self.object = form.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Work day updated successfully!",
                }
            )
        else:
            messages.success(self.request, "Work day updated successfully!")
            return super().form_valid(form)

    def form_invalid(self, form: WorkDayForm) -> HttpResponse:
        is_ajax = self.request.headers.get("x-requested-with") == "XMLHttpRequest"

        if is_ajax:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            if self.request.content_type == "application/json":
                kwargs["data"] = json.loads(self.request.body)
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Work day updated successfully!")
        return self.success_url


class WorkDayDeleteView(OwnerRequiredMixin, DeleteView):
    model = WorkDay
    template_name = "reservations/workday_confirm_delete.html"
    success_url = reverse_lazy("workday_list")

    def get_success_url(self):
        messages.success(self.request, "Work day deleted successfully!")
        return self.success_url


# Reservations Management ########
class ManageReservationsListView(OwnerRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/manage_reservations_list.html"
    context_object_name = "reservations"

    def get_queryset(self) -> QuerySet[Reservation]:
        return Reservation.objects.all().order_by("-reservation_request__date")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["employees"] = Employee.objects.all()
        return context


class ReservationCreateView(OwnerRequiredMixin, View):
    template_name = "reservations/manage_reservations_form.html"
    success_url = reverse_lazy("manage_reservations_list")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        request_reservation_form = ReservationRequestForm()
        client_data_form = ClientDataForm()
        reservation_form = ReservationForm()
        return render(
            request,
            self.template_name,
            {
                "request_reservation_form": request_reservation_form,
                "client_data_form": client_data_form,
                "reservation_form": reservation_form,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        request_reservation_form = ReservationRequestForm(request.POST)
        client_data_form = ClientDataForm(request.POST)
        reservation_form = ReservationForm(request.POST)

        if (
            request_reservation_form.is_valid()
            and client_data_form.is_valid()
            and reservation_form.is_valid()
        ):
            request_reservation = request_reservation_form.save()
            reservation = reservation_form.save(commit=False)
            reservation.reservation_request = request_reservation
            reservation.name = client_data_form.cleaned_data["name"]
            reservation.email = client_data_form.cleaned_data["email"]
            reservation.save()

            messages.success(request, "Reservation created successfully!")
            return redirect(self.success_url)

        return render(
            request,
            self.template_name,
            {
                "request_reservation_form": request_reservation_form,
                "client_data_form": client_data_form,
                "reservation_form": reservation_form,
            },
        )


class ReservationUpdateView(OwnerRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/manage_reservations_form.html"
    success_url = reverse_lazy("manage_reservations_list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data()
        reservation = self.get_object()

        if self.request.POST:
            context["request_reservation_form"] = ReservationRequestForm(
                self.request.POST,
                instance=reservation.reservation_request,
            )
            context["client_data_form"] = ClientDataForm(
                initial={"name": reservation.name, "email": reservation.email}
            )
        else:
            context["request_reservation_form"] = ReservationRequestForm(
                instance=reservation.reservation_request
            )
            context["client_data_form"] = ClientDataForm(
                initial={"name": reservation.name, "email": reservation.email}
            )
        context["reservation_form"] = self.get_form()
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        request_form = ReservationRequestForm(
            request.POST, instance=self.object.reservation_request
        )
        client_form = ClientDataForm(request.POST)
        reservation_form = ReservationForm(request.POST, instance=self.object)

        if (
            request_form.is_valid()
            and client_form.is_valid()
            and reservation_form.is_valid()
        ):
            request_reservation = request_form.save()
            reservation = reservation_form.save(commit=False)
            reservation.reservation_request = request_reservation
            reservation.name = client_form.cleaned_data["name"]
            reservation.email = client_form.cleaned_data["email"]
            reservation.save()

            messages.success(request, "Reservation updated successfully!")
            return redirect(self.success_url)

        return render(
            request,
            self.template_name,
            {
                "request_reservation_form": request_form,
                "client_data_form": client_form,
                "reservation_form": reservation_form,
            },
        )


class ReservationDeleteView(OwnerRequiredMixin, DeleteView):
    model = Reservation
    template_name = "reservations/manage_reservations_delete.html"
    success_url = reverse_lazy("manage_reservations_list")

    def get_success_url(self):
        messages.success(self.request, "Reservation deleted successfully!")
        return self.success_url


class ConfirmReservationView(OwnerRequiredMixin, View):
    def post(
        self, request: HttpRequest, pk: int, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        reservation = get_object_or_404(Reservation, pk=pk)

        if reservation.status == "CONFIRMED":
            messages.info(request, "Reservation already confirmed!")
            return redirect(reverse("manage_reservations_list"))

        reservation.status = "CONFIRMED"
        reservation.save()

        if reservation.email:
            cancel_url = request.build_absolute_uri(
                reverse("cancel_reservation", args=[reservation.id_request])
            )
            try:
                send_confirmation_email.delay(  # type: ignore[attr-defined]
                    customer_email=reservation.email,
                    customer_name=reservation.name,
                    service_name=reservation.reservation_request.service.name,
                    date=str(reservation.reservation_request.date),
                    time=str(reservation.reservation_request.start_time),
                    cancel_url=cancel_url,
                )
                messages.success(request, "Reservation confirmed and email sent!")
            except Exception as e:
                logger.exception(f"Failed to send confirmation email: {e}")
                messages.warning(
                    request, "Reservation confirmed but email failed to send."
                )
        else:
            messages.success(request, "Reservation confirmed!")

        return redirect(reverse("manage_reservations_list"))


class CancelReservationByUserView(View):
    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        reservation = get_object_or_404(Reservation, id_request=token)

        if now() - reservation.created_at > timedelta(days=7):
            return render(request, "reservations/cancel_expired.html")

        if reservation.status == "CANCELLED":
            return render(request, "reservations/already_cancelled.html")

        reservation.status = "CANCELLED"
        reservation.save()

        return render(request, "reservations/cancel_success.html")
