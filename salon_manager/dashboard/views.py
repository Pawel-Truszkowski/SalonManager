import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from reservations.forms import ClientDataForm, ReservationForm, ReservationRequestForm
from reservations.models import Reservation, WorkDay
from services.models import Service
from users.models import Employee

from .forms import EmployeeForm, ServiceForm, WorkDayForm


def home(request):
    return render(request, "dashboard/index.html")


def about(request):
    return render(request, "dashboard/about.html")


def contact(request):
    return render(request, "dashboard/contact.html")


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "OWNER"


# Employee Manage Views ###########
class EmployeeListView(OwnerRequiredMixin, ListView):
    model = Employee
    template_name = "dashboard/employee_list.html"
    context_object_name = "employees"


class EmployeeCreateView(OwnerRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "dashboard/employee_form.html"
    success_url = reverse_lazy("employee_list")

    def form_valid(self, form):
        messages.success(self.request, "Employee created successfully!")
        return super().form_valid(form)


class EmployeeUpdateView(OwnerRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "dashboard/employee_form.html"
    success_url = reverse_lazy("employee_list")

    def form_valid(self, form):
        messages.success(self.request, "Employee updated successfully!")
        return super().form_valid(form)


class EmployeeDeleteView(OwnerRequiredMixin, DeleteView):
    model = Employee
    template_name = "dashboard/employee_confirm_delete.html"
    success_url = reverse_lazy("employee_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Employee deleted successfully!")
        return super().delete(request, *args, **kwargs)


# WorkDay Views
class WorkDayListView(OwnerRequiredMixin, ListView):
    model = WorkDay
    template_name = "dashboard/workday_list.html"
    context_object_name = "workdays"

    def get_queryset(self):
        return WorkDay.objects.all().order_by("-date")


class WorkDayCreateView(OwnerRequiredMixin, CreateView):
    model = WorkDay
    form_class = WorkDayForm
    template_name = "dashboard/workday_form.html"
    success_url = reverse_lazy("workday_list")

    def form_valid(self, form):
        messages.success(self.request, "Work day created successfully!")
        return super().form_valid(form)


class WorkDayUpdateView(OwnerRequiredMixin, UpdateView):
    model = WorkDay
    form_class = WorkDayForm
    template_name = "dashboard/workday_form.html"
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
    template_name = "dashboard/workday_confirm_delete.html"
    success_url = reverse_lazy("workday_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Work day deleted successfully!")
        return super().delete(request, *args, **kwargs)


def workday_api(request):
    """API endpoint to provide workday data for FullCalendar"""
    workdays = WorkDay.objects.all()
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


# Services Management  ###############
class ManageServicesListView(OwnerRequiredMixin, ListView):
    model = Service
    template_name = "dashboard/manage_services_list.html"
    context_object_name = "services"


class ServiceCreateView(OwnerRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/manage_services_form.html"
    success_url = reverse_lazy("manage_services_list")

    def form_valid(self, form):
        messages.success(self.request, "Service created successfully!")
        return super().form_valid(form)


class ServiceUpdateView(OwnerRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/manage_services_form.html"
    success_url = reverse_lazy("manage_services_list")

    def form_valid(self, form):
        messages.success(self.request, "Service updated successfully!")
        return super().form_valid(form)


class ServiceDeleteView(OwnerRequiredMixin, DeleteView):
    model = Service
    template_name = "dashboard/manage_services_delete.html"
    success_url = reverse_lazy("manage_services_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Service deleted successfully!")
        return super().delete(request, *args, **kwargs)


# Reservations Management ########
class ManageReservationsListView(OwnerRequiredMixin, ListView):
    model = Reservation
    template_name = "dashboard/manage_reservations_list.html"
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
    template_name = "dashboard/manage_reservations_form.html"
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


class ReservationDeleteView(OwnerRequiredMixin, DeleteView):
    model = Reservation
    template_name = "dashboard/manage_reservations_delete.html"
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
