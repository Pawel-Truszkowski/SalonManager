from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from utils.mixins import OwnerRequiredMixin

from .forms import ServiceForm
from .models import Service, ServiceCategory


class ServiceListView(ListView):
    model = Service
    template_name = "services/services_list.html"
    context_object_name = "services"
    queryset = Service.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["service_categories"] = ServiceCategory.objects.all()
        return context


# Services Management  ###############
class ManageServicesListView(OwnerRequiredMixin, ListView):
    model = Service
    template_name = "services/manage_services_list.html"
    context_object_name = "services"


class ServiceCreateView(OwnerRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "services/manage_services_form.html"
    success_url = reverse_lazy("manage_services_list")

    def form_valid(self, form):
        messages.success(self.request, "Service created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "Form contains errors. Please check all fields.")
        return super().form_invalid(form)


class ServiceUpdateView(OwnerRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "services/manage_services_form.html"
    success_url = reverse_lazy("manage_services_list")

    def form_valid(self, form):
        messages.success(self.request, "Service updated successfully!")
        return super().form_valid(form)


class ServiceDeleteView(OwnerRequiredMixin, DeleteView):
    model = Service
    template_name = "services/manage_services_delete.html"
    success_url = reverse_lazy("manage_services_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Service deleted successfully!")
        return super().delete(request, *args, **kwargs)
