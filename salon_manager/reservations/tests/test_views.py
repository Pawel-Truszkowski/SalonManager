import json
from datetime import date, time, timedelta

from django.contrib.messages import get_messages
from django.urls import reverse
from reservations.models import Reservation, ReservationRequest

from ..models import WorkDay
from .base_test import BaseTestCase


class UserReservationsListViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("user_reservations_list")

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
        self.request3 = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            service=self.service1,
            employee=self.employee1,
        )

        self.reservation1 = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request1,
            name="Georges Hammond",
            status="CONFIRMED",
        )
        self.reservation2 = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request2,
            name="Georges Hammond",
            status="PENDING",
        )
        self.reservation3 = Reservation.objects.create(
            customer=self.users["client1"],
            reservation_request=self.request3,
            name="Georges Hammond",
            status="PAST",
        )

    def test_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_view_accessible_for_authenticated_user(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "reservations/reservation_list.html")

    def test_view_shows_only_user_reservations(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        reservations = response.context["reservations"]
        self.assertEqual(reservations.count(), 3)

        for reservation in reservations:
            self.assertEqual(reservation.customer, self.users["client1"])

    def test_view_excludes_other_users_reservations(self):
        request_other = ReservationRequest.objects.create(
            date=date.today() + timedelta(days=7),
            start_time=time(11, 0),
            end_time=time(12, 0),
            service=self.service1,
            employee=self.employee1,
        )
        Reservation.objects.create(
            customer=self.users["client2"],
            reservation_request=request_other,
            name="Tealc Kree",
        )

        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        reservations = response.context["reservations"]
        self.assertEqual(reservations.count(), 3)
        self.assertNotIn(self.users["client2"], [r.customer for r in reservations])

    def test_queryset_ordered_by_date_descending(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        reservations = list(response.context["reservations"])
        self.assertEqual(reservations[0], self.reservation1)
        self.assertEqual(reservations[1], self.reservation2)
        self.assertEqual(reservations[2], self.reservation3)

    def test_context_object_name_is_reservations(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertIn("reservations", response.context)

    def test_empty_queryset_when_no_reservations(self):
        self.client.force_login(self.users["client2"])
        response = self.client.get(self.url)

        reservations = response.context["reservations"]
        self.assertEqual(reservations.count(), 0)

    def test_employee_cannot_access_view(self):
        self.client.force_login(self.users["employee1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_displays_all_reservation_statuses(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        reservations = list(response.context["reservations"])
        statuses = [r.status for r in reservations]

        self.assertIn("CONFIRMED", statuses)
        self.assertIn("PENDING", statuses)
        self.assertIn("PAST", statuses)


class CancelUserReservationViewTest(BaseTestCase):
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
            status="CONFIRMED",
        )
        self.url = reverse("reservation_cancel", kwargs={"pk": self.reservation.pk})

    def test_view_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_post_cancels_reservation(self):
        self.client.force_login(self.users["client1"])
        self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")

    def test_post_redirects_to_user_reservations_list(self):
        self.client.force_login(self.users["client1"])
        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("user_reservations_list"))

    def test_post_shows_success_message(self):
        self.client.force_login(self.users["client1"])
        response = self.client.post(self.url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "The reservation has been canceled!")

    def test_cancelling_already_cancelled_reservation_shows_info_message(self):
        self.reservation.status = "CANCELLED"
        self.reservation.save()

        self.client.force_login(self.users["client1"])
        response = self.client.post(self.url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "The reservation has already been canceled.")

    def test_cancelling_already_cancelled_reservation_does_not_change_status(self):
        self.reservation.status = "CANCELLED"
        self.reservation.save()

        self.client.force_login(self.users["client1"])
        self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")

    def test_get_method_not_allowed(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_invalid_reservation_id_returns_404(self):
        self.client.force_login(self.users["client1"])
        url = reverse("reservation_cancel", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_cancel_pending_reservation(self):
        self.reservation.status = "PENDING"
        self.reservation.save()

        self.client.force_login(self.users["client1"])
        self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")

    def test_cancel_past_reservation(self):
        self.reservation.status = "PAST"
        self.reservation.save()

        self.client.force_login(self.users["client1"])
        response = self.client.post(self.url, follow=True)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "The reservation has been canceled!")

    def test_different_user_can_cancel_reservation(self):
        self.client.force_login(self.users["client2"])
        response = self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")
        self.assertRedirects(response, reverse("user_reservations_list"))

    def test_employee_can_cancel_reservation(self):
        self.client.force_login(self.users["employee1"])
        self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")

    def test_superuser_can_cancel_reservation(self):
        self.client.force_login(self.users["superuser"])
        self.client.post(self.url)

        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "CANCELLED")


class WorkDayListViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workday_list")

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_queryset_ordered_by_date_descending(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        workdays = list(response.context["workdays"])

        self.assertEqual(workdays[0], self.workday)


class WorkDayCreateViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workday_create")

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_create_workday_success(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": date.today() + timedelta(days=10),
            "start_time": time(9, 0),
            "end_time": time(17, 0),
        }
        response = self.client.post(self.url, data)

        self.assertEqual(WorkDay.objects.count(), 2)
        self.assertRedirects(response, reverse("workday_list"))

    def test_create_workday_shows_success_message(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": date.today() + timedelta(days=10),
            "start_time": time(9, 0),
            "end_time": time(17, 0),
        }
        response = self.client.post(self.url, data, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Work day created successfully!")

    def test_invalid_form_does_not_create_workday(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": date.today() + timedelta(days=10),
            "start_time": time(17, 0),
            "end_time": time(9, 0),
        }
        response = self.client.post(self.url, data)

        self.assertEqual(WorkDay.objects.count(), 1)
        self.assertEqual(response.status_code, 200)


class WorkDayUpdateViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workday_update", kwargs={"pk": self.workday.pk})

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_workday_success(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": date.today() + timedelta(days=2),
            "start_time": time(10, 0),
            "end_time": time(18, 0),
        }
        response = self.client.post(self.url, data)

        self.workday.refresh_from_db()
        self.assertEqual(self.workday.start_time, time(10, 0))
        self.assertRedirects(response, reverse("workday_list"))

    def test_update_workday_shows_success_message(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": date.today() + timedelta(days=2),
            "start_time": time(10, 0),
            "end_time": time(18, 0),
        }
        response = self.client.post(self.url, data, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Work day updated successfully!")

    def test_ajax_update_returns_json(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": str(date.today() + timedelta(days=2)),
            "start_time": "10:00",
            "end_time": "18:00",
        }
        response = self.client.post(
            self.url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "success")

    def test_ajax_update_with_json_body(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": str(date.today() + timedelta(days=2)),
            "start_time": "10:00:00",
            "end_time": "18:00:00",
        }
        response = self.client.post(
            self.url,
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.workday.refresh_from_db()
        self.assertEqual(self.workday.start_time, time(10, 0))

    def test_ajax_invalid_form_returns_errors(self):
        self.client.force_login(self.users["superuser"])
        data = {
            "employee": self.employee1.pk,
            "date": str(date.today()),
            "start_time": "18:00",
            "end_time": "10:00",
        }
        response = self.client.post(
            self.url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 400)
        json_data = response.json()
        self.assertEqual(json_data["status"], "error")
        self.assertIn("errors", json_data)

    def test_invalid_workday_id_returns_404(self):
        self.client.force_login(self.users["superuser"])
        url = reverse("workday_update", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class WorkDayDeleteViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("workday_delete", kwargs={"pk": self.workday.pk})

    def test_view_requires_owner_permission(self):
        self.client.force_login(self.users["client1"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_view(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_delete_workday_success(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.post(self.url)

        self.assertEqual(WorkDay.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Work day deleted successfully!")
        self.assertRedirects(response, reverse("workday_list"))

    def test_invalid_workday_id_returns_404(self):
        self.client.force_login(self.users["superuser"])
        url = reverse("workday_delete", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_shows_confirmation_page(self):
        self.client.force_login(self.users["superuser"])
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "reservations/workday_confirm_delete.html")


class ManageReservationsListViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("manage_reservations_list")

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
        self.assertRedirects(response, reverse("manage_reservations_list"))

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
        self.assertRedirects(response, reverse("manage_reservations_list"))

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
        self.assertRedirects(response, reverse("manage_reservations_list"))

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
