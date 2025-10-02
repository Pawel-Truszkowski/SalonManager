from datetime import date, time, timedelta
from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from reservations.service import SlotAvailabilityService


class TestSlotAvailabilityService(TestCase):
    def setUp(self):
        self.service = SlotAvailabilityService()
        self.employee = Mock()
        self.employee.id = 1
        self.employee.name = "Test Case"
        self.service_id = 1
        self.selected_date = date.today()
        self.available_slots = ["10:00", "12:00", "13:30"]

    @patch("reservations.service.WorkDay.objects.filter")
    def test_validate_working_day_raises_error_when_no_work_day(self, mock_filter):
        mock_filter.return_value.exists.return_value = False

        with pytest.raises(ValueError, match="Day off"):
            self.service._validate_working_day(self.employee, self.selected_date)

    @patch("reservations.service.WorkDay.objects.filter")
    def test_validate_working_day_passes_when_work_day_exists(self, mock_filter):
        mock_filter.return_value.exists.return_value = True
        self.service._validate_working_day(self.employee, self.selected_date)

    @patch("reservations.service.date")
    def test_filter_past_slots_returns_only_future_slots_for_today(self, mock_date):
        mock_date.today.return_value = self.selected_date

        with patch("reservations.service.timezone.now") as mock_now:
            mock_now.return_value.time.return_value = time(11, 0)
            result = self.service._filter_past_slots(
                self.available_slots, self.selected_date
            )
            expected = ["12:00", "13:30"]
            self.assertEqual(result, expected)

    def test_filter_past_slots_return_all_for_future_date(self):
        future_date = date.today() + timedelta(days=10)
        result = self.service._filter_past_slots(self.available_slots, future_date)
        self.assertEqual(result, self.available_slots)

    def test_filter_past_slots_return_empty_list_for_past_date(self):
        future_date = date.today() - timedelta(days=10)
        result = self.service._filter_past_slots(self.available_slots, future_date)
        self.assertEqual(result, [])

    @patch("reservations.service.Service.objects.get")
    def test_get_service_if_getting_correct_data(self, mock_get):
        service = Mock()
        service.duration = 30
        mock_get.return_value = service
        result = self.service._get_service(self.service_id)
        self.assertEqual(result, service)
        mock_get.assert_called_once_with(id=self.service_id)

    @patch("reservations.service.WorkDay.objects.filter")
    def test_get_workday_if_getting_correct_data(self, mock_filter):
        workday = Mock()
        workday.employee = self.employee
        mock_filter.return_value = workday
        self.service._get_work_days(self.employee, self.selected_date)
        mock_filter.assert_called_once_with(
            employee=self.employee.id, date=self.selected_date
        )

    @patch("reservations.service.generate_available_slots")
    def test_calculate_available_slots(self, mock_generate):
        mock_workday = Mock()
        mock_workday.start_time = "10:00"
        mock_workday.end_time = "12:00"
        work_days = [mock_workday]
        service_duration = 30
        mock_generate.return_value = ["10:00", "10:30"]
        result = self.service._calculate_available_slots(
            work_days, service_duration, []
        )
        self.assertEqual(result, ["10:00", "10:30"])
        mock_generate.assert_called_once_with("10:00", "12:00", 30, [])
