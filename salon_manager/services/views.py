from django.shortcuts import render
from django.views.generic import ListView

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
