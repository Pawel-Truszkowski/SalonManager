import uuid
from datetime import date, time, timedelta
from decimal import Decimal
from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from services.models import Service
from users.models import CustomUser, Employee
from utils.support_functions import generate_random_id, get_timestamp, time_difference


class WorkDay(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="work_day"
    )

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    {"end_time": "The end time must be later than the start time!"}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.employee} - {self.date}"


class ReservationRequest(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    id_request = models.CharField(max_length=100, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    def __str__(self) -> str:
        return (
            f"{self.date} - {self.start_time} to {self.end_time} - {self.service.name}"
        )

    def clean(self) -> None:
        duration = timedelta(minutes=self.service.duration)
        if self.start_time is not None and self.end_time is not None:
            if self.start_time > self.end_time:
                raise ValidationError(_("Start time must be before end time"))
            if self.start_time == self.end_time:
                raise ValidationError(_("Start time and end time cannot be the same"))
            if time_difference(self.start_time, self.end_time) > duration:
                raise ValidationError(_("Duration cannot exceed the service duration"))

        if self.date and self.date < date.today():
            raise ValidationError(_("Date cannot be in the past"))

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.id_request is None:
            self.id_request = (
                f"{get_timestamp()}{self.service.id}{generate_random_id()}"
            )
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def get_service_name(self) -> str:
        return self.service.name


class Reservation(models.Model):
    RESERVATION_STATUS_CHOICES = (
        ("PENDING", "pending"),
        ("CONFIRMED", "confirmed"),
        ("CANCELLED", "cancelled"),
        ("PAST", "past"),
    )

    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="reservations",
        limit_choices_to={"is_customer": True},
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=10, choices=RESERVATION_STATUS_CHOICES, default="PENDING"
    )
    reservation_request = models.OneToOneField(
        ReservationRequest, on_delete=models.CASCADE, related_name="reservation"
    )
    id_request = models.CharField(max_length=100, blank=True, null=True)

    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(blank=True)
    additional_info = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Reservation {self.customer.username} for {self.reservation_request.date} at {self.reservation_request.start_time}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not hasattr(self, "reservation_request"):
            raise ValidationError("Reservation request is required")

        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{self.reservation_request.service.id}{generate_random_id()}"

        return super().save(*args, **kwargs)

    @property
    def calculate_end_time(self) -> time:
        start_datetime = self.get_start_time()
        duration = timedelta(minutes=self.get_service_duration())
        end_datetime = start_datetime + duration
        return end_datetime.time()

    def get_date(self) -> date:
        return self.reservation_request.date

    def get_start_time(self) -> time:
        return self.reservation_request.start_time

    def get_end_time(self) -> time:
        return self.reservation_request.end_time

    def get_service(self) -> "Service":
        return self.reservation_request.service

    def get_service_name(self) -> str:
        return self.reservation_request.service.name

    def get_service_duration(self) -> int:
        return self.reservation_request.service.duration

    def get_employee_name(self) -> str:
        if not self.reservation_request.employee:
            return ""
        return self.reservation_request.employee.name

    def get_employee(self) -> Optional["Employee"]:
        return self.reservation_request.employee

    def get_service_price(self) -> "Decimal":
        return self.reservation_request.service.price

    def get_customer_name(self) -> str:
        return self.name
