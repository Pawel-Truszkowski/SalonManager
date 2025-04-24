import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, TemplateView, View
from services.models import Service
from users.models import Employee

from . import forms
from .models import Reservation, WorkDay


class ReservationSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "reservations/reservation_success.html"


class ReservationsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "reservations/reservation_list.html"
    model = Reservation
    context_object_name = "reservations"

    def get_queryset(self):
        return Reservation.objects.filter(customer=self.request.user)

    def test_func(self):
        return self.request.user.is_authenticated


class CancelReservationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs["pk"])
        if reservation.status != "CANCEL":
            reservation.status = "CANCEL"
            reservation.save()
            messages.success(request, "The reservation has been canceled")
        else:
            messages.warning(request, "The reservation has already been canceled")

        return redirect("your_reservation_list")

    def test_func(self):
        return self.request.user.is_authenticated
