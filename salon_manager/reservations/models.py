import datetime

from django.core.exceptions import ValidationError
from django.db import models
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

    def __str__(self):
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

    def __str__(self):
        return (
            f"{self.date} - {self.start_time} to {self.end_time} - {self.service.name}"
        )

    def clean(self):
        duration = datetime.timedelta(minutes=self.service.duration)
        if self.start_time is not None and self.end_time is not None:
            if self.start_time > self.end_time:
                raise ValidationError(_("Start time must be before end time"))
            if self.start_time == self.end_time:
                raise ValidationError(_("Start time and end time cannot be the same"))
            if time_difference(self.start_time, self.end_time) > duration:
                raise ValidationError(_("Duration cannot exceed the service duration"))

        if self.date and self.date < datetime.date.today():
            raise ValidationError(_("Date cannot be in the past"))

    def save(self, *args, **kwargs):
        if self.id_request is None:
            self.id_request = (
                f"{get_timestamp()}{self.service.id}{generate_random_id()}"
            )
        super().save(*args, **kwargs)

    def get_service_name(self):
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
    phone = PhoneNumberField(blank=True)
    status = models.CharField(
        max_length=10, choices=RESERVATION_STATUS_CHOICES, default="PENDING"
    )
    reservation_request = models.OneToOneField(
        ReservationRequest, on_delete=models.CASCADE, related_name="reservations"
    )
    id_request = models.CharField(max_length=100, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Reservation {self.customer.username} for {self.reservation_request.date} at {self.reservation_request.start_time}"

    def save(self, *args, **kwargs):
        if not hasattr(self, "reservation_request"):
            raise ValidationError("Reservation request is required")

        if self.get_start_time() and self.get_service():
            start_datetime = self.get_start_time()
            duration = datetime.timedelta(minutes=self.get_service_duration())
            end_datetime = start_datetime + duration
            self.end_time = end_datetime

        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{self.reservation_request.service.id}{generate_random_id()}"

        return super().save(*args, **kwargs)

    @property
    def calculate_end_time(self) -> datetime.time:
        start_datetime = self.get_start_time()
        duration = datetime.timedelta(minutes=self.get_service_duration())
        end_datetime = start_datetime + duration
        return end_datetime.time()

    def get_date(self):
        return self.reservation_request.date

    def get_start_time(self):
        return datetime.datetime.combine(
            self.get_date(), self.reservation_request.start_time
        )

    def get_end_time(self):
        return datetime.datetime.combine(
            self.get_date(), self.reservation_request.end_time
        )

    def get_service(self):
        return self.reservation_request.service

    def get_service_name(self):
        return self.reservation_request.service.name

    def get_service_duration(self):
        return self.reservation_request.service.duration

    def get_staff_member_name(self):
        if not self.reservation_request.employee:
            return ""
        return self.reservation_request.employee.name

    def get_staff_member(self):
        return self.reservation_request.employee

    def get_service_price(self):
        return self.reservation_request.service.price

    def get_reservation_date(self):
        return self.reservation_request.date
