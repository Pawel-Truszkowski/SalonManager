from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from reservations.models import WorkDay
from users.models import Employee

from .forms import EmployeeForm, WorkDayForm


def home(request):
    return render(request, "dashboard/index.html")


def about(request):
    return render(request, "dashboard/about.html")


def contact(request):
    return render(request, "dashboard/contact.html")


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "OWNER"


# Employee Views
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


class WorkDayDeleteView(OwnerRequiredMixin, DeleteView):
    model = WorkDay
    template_name = "dashboard/workday_confirm_delete.html"
    success_url = reverse_lazy("workday_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Work day deleted successfully!")
        return super().delete(request, *args, **kwargs)
