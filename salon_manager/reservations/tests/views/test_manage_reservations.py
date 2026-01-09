import json
from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils.timezone import now
from reservations.models import Reservation, ReservationRequest, WorkDay
from reservations.tasks import send_confirmation_email
from reservations.tests.base_test import BaseTestCase


class ManageReservationsListViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("reservations:manage_reservations_list")

        self.request1 = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.request2 = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=3),
            start_time=time(14, 0),
            end_time=time(15, 0),
            service=self.service1,
            employee=self.employee1,
        )

        self.reservation1 = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request1,
            name="Georges Hammond",
        )
        self.reservation2 = Reservation.objects.create(
            customer=self.users["client2"],
            reservation_request=self.request2,
            name="Tealc Kree",
        )

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_queryset_ordered_by_date_descending(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        reservations = list(response.context["reservations"])
        self.assertEqual(reservations[0], self.reservation1)
        self.assertEqual(reservations[1], self.reservation2)

    def test_context_contains_employees(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertIn("employees", response.context)
        self.assertEqual(response.context["employees"].count(), 1)

    def test_shows_all_reservations(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertEqual(response.context["reservations"].count(), 2)


class ReservationCreateViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("reservation_create")

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_get_renders_all_three_forms(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertIn("request_reservation_form", response.context)
        self.assertIn("client_data_form", response.context)
        self.assertIn("reservation_form", response.context)

    def test_create_reservation_success(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(10, 0),
            "end_time": time(11, 0),
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "John Doe",
            "email": "john@example.com",
            "phone_0": "PL",
            "phone_1": "500111222",
            "status": "CONFIRMED",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(ReservationRequest.objects.count(), 1)
        self.assertRedirects(response, reverse("reservations:manage_reservations_list"))

    def test_create_reservation_shows_success_message(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(10, 0),
            "end_time": time(11, 0),
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "John Doe",
            "email": "john@example.com",
            "phone_0": "PL",
            "phone_1": "500111222",
            "status": "CONFIRMED",
        }
        response = self.client.post(self.url, data, follow=True)
        messages = list(get_messages(response.wsgi_request))

        reservation = Reservation.objects.first()
        self.assertEqual(data["name"], reservation.name)
        self.assertEqual(str(messages[0]), "Reservation created successfully!")

    def test_created_reservation_has_correct_data(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(10, 0),
            "end_time": time(11, 0),
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "John Doe",
            "email": "john@example.com",
            "phone_0": "PL",
            "phone_1": "500111222",
            "status": "CONFIRMED",
        }
        self.client.post(self.url, data)

        reservation = Reservation.objects.first()
        self.assertEqual(reservation.name, "John Doe")
        self.assertEqual(reservation.email, "john@example.com")
        self.assertEqual(reservation.status, "PENDING")

    def test_invalid_request_reservation_form_does_not_create(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(17, 0),
            "end_time": time(10, 0),
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "John Doe",
            "email": "john@example.com",
            "status": "CONFIRMED",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_invalid_client_data_form_does_not_create(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(10, 0),
            "end_time": time(11, 0),
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "",
            "email": "invalid-email",
            "status": "CONFIRMED",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_invalid_reservation_form_does_not_create(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(10, 0),
            "end_time": time(11, 0),
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "John Doe",
            "email": "john@example.com",
            "status": "INVALID_STATUS",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_all_forms_returned_on_validation_error(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": time(17, 0),
            "end_time": time(10, 0),
            "service": self.service1.pk,
            "name": "John Doe",
        }
        response = self.client.post(self.url, data)

        self.assertIn("request_reservation_form", response.context)
        self.assertIn("client_data_form", response.context)
        self.assertIn("reservation_form", response.context)


class ReservationUpdateViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request1 = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request1,
            name="Georges Hammond",
            email="georges@test.com",
            phone="+48600700800",
            status="PENDING",
        )
        self.url = reverse("reservation_edit", kwargs={"pk": self.reservation.pk})

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_renders_all_three_forms(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertIn("request_reservation_form", response.context)
        self.assertIn("client_data_form", response.context)
        self.assertIn("reservation_form", response.context)

    def test_forms_prepopulated_with_existing_data(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        client_form = response.context["client_data_form"]
        self.assertEqual(client_form.initial["name"], "Georges Hammond")
        self.assertEqual(client_form.initial["email"], "georges@test.com")

    def test_update_reservation_success(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=7),
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "Updated Name",
            "email": "updated@test.com",
            "phone_0": "PL",
            "phone_1": "+48600800700",
        }
        response = self.client.post(self.url, data)

        self.reservation.refresh_from_db()

        self.assertEqual(self.reservation.name, "Updated Name")
        self.assertEqual(self.reservation.email, "updated@test.com")
        self.assertRedirects(response, reverse("reservations:manage_reservations_list"))

    def test_update_reservation_shows_success_message(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=7),
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "Updated Name",
            "email": "updated@test.com",
            "phone_0": "PL",
            "phone_1": "600800700",
            "status": "CONFIRMED",
        }
        response = self.client.post(self.url, data, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Reservation updated successfully!")

    def test_update_reservation_request_data(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=10),
            "start_time": "16:00:00",
            "end_time": "17:00:00",
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "Georges Hammond",
            "email": "georges@test.com",
            "phone_0": "PL",
            "phone_1": "+48500600700",
            "status": "PENDING",
        }
        self.client.post(self.url, data)

        self.request1.refresh_from_db()
        self.assertEqual(self.request1.date, date.today() + timedelta(days=10))
        self.assertEqual(self.request1.start_time, time(16, 0))

    def test_invalid_form_does_not_update(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": "17:00:00",
            "end_time": "10:00:00",
            "service": self.service1.pk,
            "employee": self.employee1.pk,
            "name": "Georges Hammond",
            "email": "georges@test.com",
            "status": "PENDING",
        }
        response = self.client.post(self.url, data)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.reservation_request.start_time, time(10, 0))
        self.assertEqual(response.status_code, 200)

    def test_invalid_reservation_id_returns_404(self):
        self.client.force_login(self.users["superuser"])
        url = reverse("reservation_edit", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_all_forms_returned_on_validation_error(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "date": date.today() + timedelta(days=5),
            "start_time": "17:00:00",
            "end_time": "10:00:00",
            "service": self.service1.pk,
            "name": "",
        }
        response = self.client.post(self.url, data)

        self.assertIn("request_reservation_form", response.context)
        self.assertIn("client_data_form", response.context)
        self.assertIn("reservation_form", response.context)


class ReservationDeleteViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request1 = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request1,
            name="Georges Hammond",
            email="georges@test.com",
            phone="+48600700800",
            status="PENDING",
        )
        self.url = reverse("reservation_delete", kwargs={"pk": self.reservation.pk})

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_delete_reservation_success(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.post(self.url)

        self.assertEqual(Reservation.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Reservation deleted successfully!")
        self.assertRedirects(response, reverse("reservations:manage_reservations_list"))

    def test_invalid_workday_id_returns_404(self):
        self.client.force_login(self.users["superuser"])
        url = reverse("reservation_delete", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_shows_confirmation_page(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertTemplateUsed(
            response, "reservations/manage_reservations_delete.html"
        )


class ConfirmReservationViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request1 = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(11, 0),
            service=self.service1,
            employee=self.employee1,
        )
        self.reservation = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request1,
            name="Georges Hammond",
            email="georges@test.com",
            phone="+48123456789",
            status="PENDING",
        )
        self.url = reverse("reservation_confirm", kwargs={"pk": self.reservation.pk})

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_method_not_allowed(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch("reservations.views.manage_reservations_views.send_confirmation_email.delay")
    def test_confirm_reservation_success(self, mock_email):
        self.client.force_login(self.users["superuser"])
        response = self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CONFIRMED")
        self.assertRedirects(response, reverse("reservations:manage_reservations_list"))

    @patch("reservations.views.manage_reservations_views.send_confirmation_email.delay")
    def test_confirm_reservation_sends_email(self, mock_email):
        self.client.force_login(self.users["superuser"])
        self.client.post(self.url)
        mock_email.assert_called_once()
        call_kwargs = mock_email.call_args[1]

        self.assertEqual(call_kwargs["customer_email"], "georges@test.com")
        self.assertEqual(call_kwargs["customer_name"], "Georges Hammond")

    @patch("reservations.views.manage_reservations_views.send_confirmation_email.delay")
    def test_confirm_reservation_shows_success_message(self, mock_email):
        self.client.force_login(self.users["superuser"])
        response = self.client.post(self.url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertIn("confirmed", str(messages[0]).lower())

    def test_already_confirmed_reservation_shows_info_message(self):
        self.reservation.status = "CONFIRMED"
        self.reservation.save()

        self.client.force_login(self.users["superuser"])
        response = self.client.post(self.url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Reservation already confirmed!")

    @patch("reservations.views.manage_reservations_views.send_confirmation_email.delay")
    def test_already_confirmed_does_not_send_email(self, mock_email):
        self.reservation.status = "CONFIRMED"
        self.reservation.save()

        self.client.force_login(self.users["superuser"])
        self.client.post(self.url)

        mock_email.assert_not_called()

    @patch("reservations.views.manage_reservations_views.send_confirmation_email.delay")
    def test_email_failure_logs_error(self, mock_email):
        mock_email.side_effect = Exception("SMTP Error")

        with self.assertLogs("reservations.views", level="ERROR") as logs:
            self.client.force_login(self.users["superuser"])
            self.client.post(self.url, follow=True)

            self.reservation.refresh_from_db()
            self.assertEqual(self.reservation.status, "CONFIRMED")

            self.assertTrue(any("SMTP Error" in log for log in logs.output))

    def test_reservation_without_email_still_confirms(self):
        self.reservation.email = None
        self.reservation.save()

        self.client.force_login(self.users["superuser"])
        self.client.post(self.url, follow=True)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CONFIRMED")

    def test_invalid_reservation_id_returns_404(self):
        self.client.force_login(self.users["superuser"])
        url = reverse("reservation_confirm", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    @patch("reservations.views.manage_reservations_views.send_confirmation_email.delay")
    def test_cancel_url_in_email_is_absolute(self, mock_email):
        self.client.force_login(self.users["superuser"])
        self.client.post(self.url)

        call_kwargs = mock_email.call_args[1]
        self.assertIn("http", call_kwargs["cancel_url"])
