from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from reservations.models import Reservation, ReservationRequest, WorkDay
from reservations.views_reservation import create_reservation
from users.models import CustomUser, Employee

from salon_manager.reservations.tests.base_test import BaseTestCase


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
        self.client = Client()
        self.client_user = self.users["client1"]

        self.reservation_request = ReservationRequest.objects.create(
            date=date.today(),
            start_time="10:00",
            end_time="11:00",
            service=self.service1,
            employee=self.employee1,
            id_request=1234567890,
        )

        self.url = reverse(
            "reservation_client_information",
            kwargs={
                "reservation_request_id": self.reservation_request.id,
                "id_request": self.reservation_request.id_request,
            },
        )
        self.valid_client_data_form = {
            "name": "Georges Hammond",
            "email": "georges.s.hammond@test.com",
        }
        self.valid_reservation_form = {
            "phone_0": "PL",
            "phone_1": "611711911",
            "additional_info": "Please contact me!",
        }

    def test_get_view_anonymous_user(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"])
        self.assertIn("form", response.context)
        self.assertIn("client_data_form", response.context)
        self.assertTemplateUsed(
            response, "reservations/reservation_client_information.html"
        )

    def test_get_view_authenticated_user_prefilled_data(self):
        self.client.force_login(self.client_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        client_form = response.context["client_data_form"]
        self.assertEqual(client_form.initial["email"], self.client_user.email)

    def test_get_view_already_submitted(self):
        session = self.client.session
        session["reservation_completed_1234567890"] = True
        session.save()

        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "reservations/304_already_submitted.html")

    @patch("reservations.views_reservation.create_reservation")
    def test_post_valid_forms_success(self, mock_create_reservation):
        mock_create_reservation.return_value = True
        post_data = {**self.valid_client_data_form, **self.valid_reservation_form}

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("reservation_success"))
        mock_create_reservation.assert_called_once()
        self.assertTrue(
            self.client.session.get(
                f"reservation_completed_{self.reservation_request.id_request}", False
            )
        )

    @patch("reservations.views_reservation.create_reservation")
    def test_post_valid_form_but_create_fails(self, mock_create_reservation):
        mock_create_reservation.return_value = False
        post_data = {**self.valid_client_data_form, **self.valid_reservation_form}

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 200)

        messages = list(m.message for m in get_messages(response.wsgi_request))

        self.assertIn(
            "There was an error creating your reservation. Please try again.", messages
        )

    def test_post_invalid_data_forms(self):
        post_data = {"email": "invalid-email"}
        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 200)

        messages = list(m.message for m in get_messages(response.wsgi_request))

        self.assertIn(
            "There was an error in your submission. Please check the form and try again.",
            messages,
        )

    def test_create_reservation_with_correct_data_should_return_reservation(self):
        reservation_data = {
            "phone": "+48611711911",
            "additional_info": "Please contact me!",
        }
        result = create_reservation(
            reservation_request_obj=self.reservation_request,
            id_request=self.reservation_request.id_request,
            client_data=self.valid_client_data_form,
            reservation_data=reservation_data,
        )

        self.assertIsNotNone(result)
        self.assertTrue(result)
        self.assertEqual(result.customer, self.client_user)
        self.assertEqual(result.email, "georges.s.hammond@test.com")
        self.assertEqual(result.name, "Georges Hammond")
        self.assertEqual(result.phone, "+48611711911")
        self.assertEqual(result.additional_info, "Please contact me!")

    def test_missing_required_field_raises_error(self):
        incomplete_data = {"email": "test@example.com"}

        with self.assertRaises(KeyError):
            create_reservation(
                reservation_request_obj=self.reservation_request,
                id_request=self.reservation_request.id_request,
                client_data=self.valid_client_data_form,
                reservation_data=incomplete_data,
            )

    def test_duplicate_reservation_request_raises_error(self):
        reservation_data = {
            "phone": "+48611711911",
            "additional_info": "Please contact me!",
        }
        create_reservation(
            reservation_request_obj=self.reservation_request,
            id_request=6,
            client_data=self.valid_client_data_form,
            reservation_data=reservation_data,
        )

        with self.assertRaises(Exception):
            create_reservation(
                reservation_request_obj=self.reservation_request,
                id_request=7,
                client_data=self._valid_client_data_form,
                reservation_data=reservation_data,
            )

    @patch(
        "reservations.views_reservation.send_reservation_notification.delay_on_commit"
    )
    def test_notification_is_sent(self, mock_notification):
        reservation_data = {
            "phone": "+48611711911",
            "additional_info": "Please contact me!",
        }
        create_reservation(
            reservation_request_obj=self.reservation_request,
            id_request=3,
            client_data=self.valid_client_data_form,
            reservation_data=reservation_data,
        )

        mock_notification.assert_called_once_with(
            customer=self.valid_client_data_form["name"],
            service=self.reservation_request.service.name,
            date=self.reservation_request.date,
            time=self.reservation_request.start_time,
        )

    @patch(
        "reservations.views_reservation.send_reservation_notification.delay_on_commit"
    )
    @patch("reservations.views_reservation.logger")
    def test_notification_failure_does_not_prevent_reservation(
        self, mock_logger, mock_notification
    ):
        mock_notification.side_effect = Exception("Email service down")

        reservation_data = {
            "phone": "+48611711911",
            "additional_info": "Please contact me!",
        }
        reservation = create_reservation(
            reservation_request_obj=self.reservation_request,
            id_request=4,
            client_data=self.valid_client_data_form,
            reservation_data=reservation_data,
        )

        self.assertIsNotNone(reservation)
        self.assertTrue(Reservation.objects.filter(id=reservation.id).exists())

        mock_logger.exception.assert_called_once()
