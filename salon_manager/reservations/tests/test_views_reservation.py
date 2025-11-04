from datetime import date, time, timedelta
from unittest.mock import Mock, patch

from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from reservations.models import ReservationRequest, WorkDay
from services.models import Service, ServiceCategory
from users.models import CustomUser, Employee

from .base_test import BaseTestCase


class TestReservationRequestView(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse(
            "reservation_request", kwargs={"service_id": self.service1.id}
        )
        self.valid_form_data = {
            "service": self.service1.id,
            "employee": self.employee1.id,
            "date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "11:00",
        }

    def test_get_displays_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservations/reservation_create.html")
        self.assertIn("form", response.context)
        self.assertIn("service", response.context)

    def test_get_with_nonexistent_service_returns_404(self):
        url = reverse("reservation_request", kwargs={"service_id": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_post_valid_data_creates_reservation(self):
        initial_count = ReservationRequest.objects.count()

        response = self.client.post(self.url, data=self.valid_form_data)

        self.assertEqual(ReservationRequest.objects.count(), initial_count + 1)

        reservation = ReservationRequest.objects.latest("id")
        self.assertRedirects(
            response,
            reverse(
                "reservation_client_information",
                kwargs={
                    "reservation_request_id": reservation.id,
                    "id_request": reservation.id_request,
                },
            ),
        )

    def test_post_invalid_data_shows_form_with_errors(self):
        invalid_data = self.valid_form_data.copy()
        invalid_data["employee"] = 99999

        response = self.client.post(self.url, data=invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservations/reservation_create.html")
        self.assertIn("form", response.context)
        self.assertFalse(response.context["form"].is_valid())

        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)

    def test_form_preselects_employee_if_only_one(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["staff_member"], self.employee1)
        self.assertEqual(list(response.context["all_staff_members"]), [self.employee1])

    def test_all_staff_members_when_have_the_same_service(self):
        self.employee2 = Employee.objects.create(
            user=self.users["employee2"], name="Samantha"
        )
        self.employee2.services.add(self.service1)
        response = self.client.get(self.url)
        self.assertFalse(response.context["staff_member"])
        self.assertEqual(
            list(response.context["all_staff_members"]),
            [self.employee1, self.employee2],
        )
        self.assertEqual(len(response.context["all_staff_members"]), 2)


class TestReservationClientInformationView(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client_user = self.users["client1"]

        self.reservation_request = Mock()
        self.reservation_request.id = 1
        self.reservation_request.id_request = 1234567890

        self.url = reverse(
            "reservation_client_information",
            kwargs={
                "reservation_request_id": self.reservation_request.id,
                "id_request": self.reservation_request.id_request,
            },
        )
        self.valid_client_data_form = {"name": "Test Case", "email": "test@case.com"}
