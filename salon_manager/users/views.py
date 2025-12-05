from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
    View,
)
from utils.mixins import OwnerRequiredMixin

from .forms import EmployeeForm, ProfileUpdateForm, UserRegisterForm, UserUpdateForm
from .models import Employee


class RegisterView(FormView):
    template_name = "users/register.html"
    form_class = UserRegisterForm

    def form_valid(self, form):
        form.save()
        username = form.cleaned_data.get("username")
        messages.success(
            self.request,
            f"Dear {username}, you have been successfully signed up! Now, you can log-in!",
        )
        return render(self.request, "users/register_done.html", {"username": username})


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        return render(
            request,
            "users/profile.html",
            {"user_form": user_form, "profile_form": profile_form},
        )

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile's been updated!")
            return redirect("profile")

        return render(
            request,
            "users/profile.html",
            {"user_form": user_form, "profile_form": profile_form},
        )


# Employee Views
class EmployeeListView(OwnerRequiredMixin, ListView):
    model = Employee
    template_name = "users/employee_list.html"
    context_object_name = "employees"


class EmployeeCreateView(OwnerRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "users/employee_form.html"
    success_url = reverse_lazy("employee_list")

    def form_valid(self, form):
        messages.success(self.request, "Employee created successfully!")
        return super().form_valid(form)


class EmployeeUpdateView(OwnerRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "users/employee_form.html"
    success_url = reverse_lazy("employee_list")

    def form_valid(self, form):
        messages.success(self.request, "Employee updated successfully!")
        return super().form_valid(form)


class EmployeeDeleteView(OwnerRequiredMixin, DeleteView):
    model = Employee
    template_name = "users/employee_confirm_delete.html"
    success_url = reverse_lazy("employee_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Employee deleted successfully!")
        return super().delete(request, *args, **kwargs)
