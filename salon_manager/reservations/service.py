from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from services.models import Service
from utils.support_functions import (
    check_for_conflicting_reservation,
    generate_available_slots,
    handle_invalid_form,
    json_response,
)

from .models import ReservationRequest, WorkDay

if TYPE_CHECKING:
    from users.models import Employee


class SlotAvailabilityService:
    def get_available_slots_(self, selected_date, employee, service_id):
        self._validate_working_day(employee, selected_date)

        service = self._get_service(service_id)
        work_days = self._get_work_days(employee, selected_date)
        existing_reservations = self._get_existing_reservations(employee, selected_date)
        available_slots = self._calculate_available_slots(
            work_days, service.duration, existing_reservations
        )
        available_slots = self._filter_past_slots(available_slots, selected_date)

        if not available_slots:
            raise ValueError(_("No availability"))

        return {
            "available_slots": available_slots,
            "date_chosen": selected_date.strftime("%a, %B %d, %Y"),
            "staff_member": employee.name,
            "error": False,
        }

    def get_next_available_date(
        self, employee: "Employee", service_id: int, from_date: date
    ) -> date:
        service = self._get_service(service_id)
        working_days = WorkDay.objects.filter(
            employee=employee, date__gt=from_date
        ).order_by("date")

        for working_day in working_days:
            try:
                result = self.get_available_slots_(
                    working_day.date, employee, service.id
                )

                if result.get("available_slots"):
                    return working_day.date
            except ValueError:
                continue
        raise ValueError(_("No available dates found for this employee and service."))

    @staticmethod
    def _get_service(service_id) -> QuerySet[Service]:
        return Service.objects.get(id=service_id)

    @staticmethod
    def _validate_working_day(employee: "Employee", selected_date: date):
        working_day_exists = WorkDay.objects.filter(
            employee=employee.id, date=selected_date
        ).exists()
        if not working_day_exists:
            raise ValueError(_("Day off. Please select another date!"))

    @staticmethod
    def _get_work_days(employee: "Employee", selected_date: date) -> QuerySet[WorkDay]:
        return WorkDay.objects.filter(employee=employee.id, date=selected_date)

    @staticmethod
    def _get_existing_reservations(
        employee, selected_date
    ) -> QuerySet[ReservationRequest]:
        return ReservationRequest.objects.filter(
            employee=employee.id, date=selected_date
        )

    @staticmethod
    def _calculate_available_slots(work_days, service_duration, existing_reservations):
        available_slots = []
        for work_day in work_days:
            available_slots += generate_available_slots(
                work_day.start_time,
                work_day.end_time,
                service_duration,
                existing_reservations,
            )
        return available_slots

    @staticmethod
    def _filter_past_slots(available_slots, selected_date):
        if selected_date <= date.today():
            current_time = timezone.now().time().strftime("%H:%M")
            return [slot for slot in available_slots if slot > current_time]
        return available_slots
