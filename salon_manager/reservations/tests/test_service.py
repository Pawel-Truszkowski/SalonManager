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

        with patch("reservations.service.timezone.localtime") as mock_now:
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
        past_date = date.today() - timedelta(days=10)
        result = self.service._filter_past_slots(self.available_slots, past_date)
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

    @patch("reservations.service.SlotAvailabilityService._filter_past_slots")
    @patch("reservations.service.SlotAvailabilityService._calculate_available_slots")
    @patch("reservations.service.SlotAvailabilityService._get_existing_reservations")
    @patch("reservations.service.SlotAvailabilityService._get_work_days")
    @patch("reservations.service.SlotAvailabilityService._get_service")
    @patch("reservations.service.SlotAvailabilityService._validate_working_day")
    def test_get_available_slots_returns_correct_structure(
        self,
        mock_validate,
        mock_get_service,
        mock_work_days,
        mock_existing_reservations,
        mock_calculate,
        mock_filter,
    ):
        mock_service = Mock()
        mock_service.duration = 30
        mock_get_service.return_value = mock_service
        mock_work_days.return_value = []
        mock_existing_reservations.return_value = []
        mock_calculate.return_value = ["10:00", "11:00"]
        mock_filter.return_value = ["10:00", "11:00"]

        result = self.service.get_available_slots_(
            self.selected_date, self.employee, self.service_id
        )

        self.assertIn("available_slots", result)
        self.assertIn("date_chosen", result)
        self.assertIn("staff_member", result)
        self.assertIn("error", result)
        self.assertEqual(result["available_slots"], ["10:00", "11:00"])
        self.assertEqual(result["staff_member"], "Test Case")
        self.assertFalse(result["error"])

    @patch("reservations.service.SlotAvailabilityService._validate_working_day")
    def test_get_available_slots_raises_error_when_no_working_day(self, mock_validate):
        mock_validate.side_effect = ValueError("Day off. Please select another date!")

        with pytest.raises(ValueError, match="Day off"):
            self.service.get_available_slots_(
                self.selected_date, self.employee, self.service_id
            )

    @patch("reservations.service.SlotAvailabilityService._filter_past_slots")
    @patch("reservations.service.SlotAvailabilityService._calculate_available_slots")
    @patch("reservations.service.SlotAvailabilityService._get_existing_reservations")
    @patch("reservations.service.SlotAvailabilityService._get_work_days")
    @patch("reservations.service.SlotAvailabilityService._get_service")
    @patch("reservations.service.SlotAvailabilityService._validate_working_day")
    def test_get_available_slots_raises_error_when_no_slots_available(
        self,
        mock_validate,
        mock_get_service,
        mock_work_days,
        mock_existing_reservations,
        mock_calculate,
        mock_filter,
    ):
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_work_days.return_value = []
        mock_existing_reservations.return_value = []
        mock_calculate.return_value = []
        mock_filter.return_value = []  # <-- Lack of available slots

        with pytest.raises(ValueError, match="No availability"):
            self.service.get_available_slots_(
                self.selected_date, self.employee, self.service_id
            )

    @patch("reservations.service.WorkDay.objects.filter")
    @patch("reservations.service.SlotAvailabilityService._get_service")
    def test_get_next_available_date_returns_first_available_date(
        self, mock_get_service, mock_filter
    ):
        mock_service = Mock()
        mock_service.id = self.service_id
        mock_get_service.return_value = mock_service

        tomorrow = date.today() + timedelta(days=1)
        mock_workday1 = Mock()
        mock_workday1.date = tomorrow

        mock_filter.return_value.order_by.return_value = [mock_workday1]

        with patch.object(self.service, "get_available_slots_") as mock_get_slots:
            mock_get_slots.return_value = {
                "available_slots": ["10:00", "11:00"],
                "date_chosen": tomorrow.strftime("%a, %B %d, %Y"),
            }

            result = self.service.get_next_available_date(
                self.employee, self.service_id, date.today()
            )

            self.assertEqual(result, tomorrow)

    @patch("reservations.service.WorkDay.objects.filter")
    @patch("reservations.service.SlotAvailabilityService._get_service")
    def test_get_next_available_date_skips_days_without_slots(
        self, mock_get_service, mock_filter
    ):
        """Test że get_next_available_date pomija dni bez dostępnych slotów."""
        mock_service = Mock()
        mock_service.id = self.service_id
        mock_get_service.return_value = mock_service

        tomorrow = date.today() + timedelta(days=1)
        in_two_days = date.today() + timedelta(days=2)

        mock_workday1 = Mock()
        mock_workday1.date = tomorrow
        mock_workday2 = Mock()
        mock_workday2.date = in_two_days

        mock_filter.return_value.order_by.return_value = [mock_workday1, mock_workday2]

        with patch.object(self.service, "get_available_slots_") as mock_get_slots:
            # Pierwszy dzień - brak slotów (ValueError)
            # Drugi dzień - są sloty
            mock_get_slots.side_effect = [
                ValueError("No availability"),
                {"available_slots": ["10:00", "11:00"]},
            ]

            result = self.service.get_next_available_date(
                self.employee, self.service_id, date.today()
            )

            self.assertEqual(result, in_two_days)

    @patch("reservations.service.WorkDay.objects.filter")
    @patch("reservations.service.SlotAvailabilityService._get_service")
    def test_get_next_available_date_raises_error_when_no_working_days(
        self, mock_get_service, mock_filter
    ):
        mock_service = Mock()
        mock_service.id = self.service_id
        mock_get_service.return_value = mock_service

        mock_filter.return_value.order_by.return_value = []

        with pytest.raises(ValueError, match="No available dates found"):
            self.service.get_next_available_date(
                self.employee, self.service_id, date.today()
            )

    @patch("reservations.service.WorkDay.objects.filter")
    @patch("reservations.service.SlotAvailabilityService._get_service")
    def test_get_next_available_date_raises_error_when_no_slots_in_any_day(
        self, mock_get_service, mock_filter
    ):
        mock_service = Mock()
        mock_service.id = self.service_id
        mock_get_service.return_value = mock_service

        tomorrow = date.today() + timedelta(days=1)
        mock_workday = Mock()
        mock_workday.date = tomorrow

        mock_filter.return_value.order_by.return_value = [mock_workday]

        with patch.object(self.service, "get_available_slots_") as mock_get_slots:
            mock_get_slots.side_effect = ValueError("No availability")

            with pytest.raises(ValueError, match="No available dates found"):
                self.service.get_next_available_date(
                    self.employee, self.service_id, date.today()
                )
