from datetime import date, time, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse

from reservations.models import WorkDay
from services.models import Service, ServiceCategory
from users.models import CustomUser, Employee

from .base_test import BaseTestCase


class TestGetAvailableSlots(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        self.url = reverse("get_available_slots")

    @patch("reservations.views_ajax.SlotAvailabilityService")
    def test_get_available_slots_with_correct_data(self, mock_slot_service):
        """get_available_slots view should return a JSON response with available slots for the selected date."""
        mock_result = mock_slot_service.return_value
        mock_result.get_available_slots_.return_value = {
            "available_slots": ["10:00", "10:15", "10:30"],
            "date_chosen": date.today(),
            "staff_member": "Daniel",
            "error": False,
        }

        data = {
            "selected_date": date.today().isoformat(),
            "staff_member": "1",
            "service_id": "1",
        }

        response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("date_chosen", response_data)
        self.assertIn("available_slots", response_data)
        self.assertFalse(response_data.get("error"))
        mock_result.get_available_slots_.assert_called_once()

    def test_get_available_slots_when_no_work_day(self):
        """get_available_slots_ajax view should return an error if the selected date is in non working day of the employee."""

        selected_date = date.today() + timedelta(days=1)

        data = {
            "selected_date": selected_date.isoformat(),
            "staff_member": "1",
            "service_id": "1",
        }

        response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("date_chosen", response_data)
        self.assertIn("available_slots", response_data)
        self.assertTrue(response_data.get("error"))
        self.assertEqual(
            response_data["message"], "Day off. Please select another date!"
        )

    def test_get_available_slots_ajax_past_date(self):
        """get_available_slots_ajax view should return an error if the selected date is in the past."""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.get(self.url, {"selected_date": past_date})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["error"], True)
        self.assertEqual(response.json()["message"], "Date is in the past")
