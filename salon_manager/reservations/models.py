import datetime

from django.db import models
from services.models import Service
from users.models import CustomUser, Employee


class WorkDay(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="work_day"
    )


class Reservation(models.Model):
    RESERVATION_STATUS_CHOICES = (
        ("PENDING", "Oczekujące"),
        ("CONFIRMED", "Potwierdzone"),
        ("CANCELLED", "Anulowane"),
    )

    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="reservations",
        limit_choices_to={"is_customer": True},
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="reservations"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="reservations"
    )
    reservation_date = models.DateField()
    start_time = models.TimeField()
    status = models.CharField(
        max_length=10, choices=RESERVATION_STATUS_CHOICES, default="PENDING"
    )

    def __str__(self) -> str:
        return f"Rezerwacja {self.customer.username} na {self.reservation_date} o {self.start_time}"

    @property
    def end_time(self) -> datetime.time:
        start_datetime = datetime.datetime.combine(
            self.reservation_date, self.start_time
        )
        duration = datetime.timedelta(minutes=self.service.duration)
        end_datetime = start_datetime + duration
        return end_datetime.time()
