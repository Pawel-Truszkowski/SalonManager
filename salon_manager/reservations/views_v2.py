from datetime import datetime, time, timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from services.models import Service
from users.models import Employee

from .models import Reservation, WorkDay


def reservation_create(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    employees = Employee.objects.filter(services=service)
    return render(
        request,
        "reservations/appointment.html",
        context={"service": service, "employees": employees},
    )
