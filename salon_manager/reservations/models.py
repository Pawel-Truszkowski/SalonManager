import datetime

from django.db import models
from services.models import Service
from users.models import CustomUser, Employee

RESERVATION_STATUS_CHOICES = (
    ("PENDING", "Oczekujące"),
    ("CONFIRMED", "Potwierdzone"),
    ("CANCELLED", "Anulowane"),
)


class Reservation(models.Model):
    customer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="reservations"
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="reservations"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="reservations"
    )
    reservation_date = models.DateTimeField()
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
