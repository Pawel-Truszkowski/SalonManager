import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

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


# New API views for FullCalendar
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
    """API endpoint to update workday date (for drag and drop)"""
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


##### Reservations Management ########
class ManageReservationsListView(OwnerRequiredMixin, ListView):
    model = Reservation
    template_name = "dashboard/manage_reservations_list.html"
    context_object_name = "reservations"


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
