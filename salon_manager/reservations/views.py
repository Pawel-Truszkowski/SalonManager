import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.urls import reverse_lazy
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


class ReservationSuccessView(TemplateView):
    template_name = "reservations/reservation_success.html"


class UserReservationsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "reservations/reservation_list.html"
    model = Reservation
    context_object_name = "reservations"

    def get_queryset(self):
        return Reservation.objects.filter(customer=self.request.user).order_by(
            "-reservation_request__date"
        )

    def test_func(self):
        return self.request.user.is_authenticated


class CancelUserReservationView(LoginRequiredMixin, UserPassesTestMixin, View):
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


# WorkDay Management ###################
class WorkDayListView(OwnerRequiredMixin, ListView):
    model = WorkDay
    template_name = "reservations/workday_list.html"
    context_object_name = "workdays"

    def get_queryset(self):
        return WorkDay.objects.all().order_by("-date")


class WorkDayCreateView(OwnerRequiredMixin, CreateView):
    model = WorkDay
    form_class = WorkDayForm
    template_name = "reservations/workday_form.html"
    success_url = reverse_lazy("workday_list")

    def form_valid(self, form):
        messages.success(self.request, "Work day created successfully!")
        return super().form_valid(form)


class WorkDayUpdateView(OwnerRequiredMixin, UpdateView):
    model = WorkDay
    form_class = WorkDayForm
    template_name = "reservations/workday_form.html"
    success_url = reverse_lazy("workday_list")

    def form_valid(self, form):
        messages.success(self.request, "Work day updated successfully!")
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        is_ajax = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.content_type == "application/json"
        )

        if is_ajax:
            self.object = self.get_object()

            try:
                if request.content_type == "application/json":
                    data = json.loads(request.body)
                    form = self.form_class(data, instance=self.object)
                else:
                    form = self.form_class(request.POST, instance=self.object)

                if form.is_valid():
                    self.object = form.save()
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "Work day updated successfully!",
                        }
                    )
                else:
                    return JsonResponse(
                        {"status": "error", "errors": form.errors}, status=400
                    )
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return super().post(request, *args, **kwargs)


class WorkDayDeleteView(OwnerRequiredMixin, DeleteView):
    model = WorkDay
    template_name = "reservations/workday_confirm_delete.html"
    success_url = reverse_lazy("workday_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Work day deleted successfully!")
        return super().delete(request, *args, **kwargs)


def workday_api(request):
    workdays = WorkDay.objects.all()
    # workdays = WorkDay.objects.select_related('employee').all()
    events = []

    for workday in workdays:
        events.append(
            {
                "id": workday.pk,
                "title": f"{workday.employee.name}: {workday.start_time.strftime('%H:%M')} - {workday.end_time.strftime('%H:%M')}",
                "start": f"{workday.date.isoformat()}T{workday.start_time.strftime('%H:%M:%S')}",
                "end": f"{workday.date.isoformat()}T{workday.end_time.strftime('%H:%M:%S')}",
                "extendedProps": {
                    "startTime": workday.start_time.strftime("%H:%M"),
                    "endTime": workday.end_time.strftime("%H:%M"),
                    "employeeId": workday.employee.id,
                    "employeeName": workday.employee.name,
                },
            }
        )

    return JsonResponse(events, safe=False)


@require_POST
def update_workday_date(request, pk):
    try:
        workday = WorkDay.objects.get(pk=pk)
        data = json.loads(request.body)
        new_date = data.get("date")

        if new_date:
            workday.date = datetime.strptime(new_date, "%Y-%m-%d").date()
            workday.save()

            return JsonResponse(
                {"status": "success", "message": "Work day updated successfully!"}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Date is required"}, status=400
            )

    except WorkDay.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Work day not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Reservations Management ########
class ManageReservationsListView(OwnerRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/manage_reservations_list.html"
    context_object_name = "reservations"

    def get_queryset(self):
        return Reservation.objects.all().order_by("-reservation_request__date")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context["employees"] = Employee.objects.all()
        return context


def reservations_api(request):
    """API endpoint to provide reservations data for FullCalendar"""

    employee_id = request.GET.get("employee")

    if employee_id:
        reservations = Reservation.objects.filter(
            reservation_request__employee__id=employee_id
        )
    else:
        try:
            reservations = Reservation.objects.all()
        except Reservation.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Reservations not found"}, status=404
            )

    events = []

    for reservation in reservations:
        events.append(
            {
                "id": reservation.pk,
                "title": f"{reservation.get_service_name()}, {reservation.name} ",
                "start": f"{reservation.get_date().isoformat()}T{reservation.get_start_time().strftime('%H:%M')}",
                "end": f"{reservation.get_date().isoformat()}T{reservation.get_end_time().strftime('%H:%M')}",
                "color": "#28a745" if reservation.status == "CONFIRMED" else "#ffc107",
                "extendedProps": {
                    "startTime": reservation.get_start_time().strftime("%H:%M"),
                    "endTime": reservation.get_end_time().strftime("%H:%M"),
                },
            }
        )

    return JsonResponse(events, safe=False)


class ReservationCreateView(OwnerRequiredMixin, View):
    template_name = "reservations/manage_reservations_form.html"
    success_url = reverse_lazy("manage_reservations_list")

    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
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

    def get_context_data(self, **kwargs):
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

    def post(self, request, *args, **kwargs):
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

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Reservation deleted successfully!")
        return super().delete(request, *args, **kwargs)


class ConfirmReservationView(OwnerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=pk)
        reservation.status = "CONFIRMED"
        reservation.save()
        messages.success(request, "Reservation confirmed")

        return redirect(reverse("manage_reservations_list"))
