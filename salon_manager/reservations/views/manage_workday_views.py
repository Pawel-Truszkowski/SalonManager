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
from reservations.forms import (
    ClientDataForm,
    ReservationForm,
    ReservationRequestForm,
    WorkDayForm,
)
from reservations.models import Reservation, WorkDay
from reservations.tasks import send_confirmation_email
from users.models import Employee
from utils.mixins import OwnerRequiredMixin

logger = logging.getLogger(__name__)


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
