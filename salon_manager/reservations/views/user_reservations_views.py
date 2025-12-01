import logging
from datetime import timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.generic import (
    ListView,
    TemplateView,
    View,
)
from reservations.models import Reservation, WorkDay

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
