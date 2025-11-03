from datetime import date, time, timedelta
from unittest.mock import Mock, patch

from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from reservations.models import WorkDay
from services.models import Service, ServiceCategory
from users.models import CustomUser, Employee

from ..models import ReservationRequest
from .base_test import BaseTestCase


class TestReservationRequestView(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "reservation_request", kwargs={"service_id": self.service1.id}
        )
        self.employee2 = Employee.objects.create(
            user=self.users["employee2"], name="Samantha"
        )
        self.employee2.services.add(self.service1)
        self.workday2 = WorkDay.objects.create(
            employee=self.employee2,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

    def test_successful_reservation_request_with_valid_service_id(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservations/reservation_create.html")
        self.assertIn("service", response.context)
        self.assertEqual(response.context["service"], self.service1)

    def test_service_not_found_redirects_to_services_list(self):
        non_existent_id = 99999
        url = reverse("reservation_request", kwargs={"service_id": non_existent_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_context_contains_required_data(self):
        response = self.client.get(self.url)
        self.assertIn("service", response.context)
        self.assertIn("all_staff_members", response.context)
        self.assertIn("date_chosen", response.context)
        self.assertIn("timezoneTxt", response.context)
        self.assertIn("locale", response.context)

    def test_all_staff_members_are_in_context(self):
        response = self.client.get(self.url)

        staff_members = response.context["all_staff_members"]
        self.assertEqual(staff_members.count(), 2)
        self.assertIn(self.employee1, staff_members)
        self.assertIn(self.employee2, staff_members)

    def test_single_staff_member_is_preselected(self):
        service_category = ServiceCategory.objects.create(
            name="Pedicure", description="This is category of service for testing"
        )
        single_staff_service = Service.objects.create(
            name="Single Staff Service",
            description="Service with one employee",
            category=service_category,
            price=50.00,
            duration=30,
        )
        self.employee1.services.add(single_staff_service)

        response = self.client.get(
            reverse(
                "reservation_request", kwargs={"service_id": single_staff_service.id}
            )
        )
        self.assertIn("staff_member", response.context)
        self.assertEqual(response.context["staff_member"], self.employee1)


class ReservationRequestTestCase(BaseTestCase):
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
