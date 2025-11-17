from datetime import date, time, timedelta

from django.contrib.messages import get_messages
from django.urls import reverse
from reservations.models import Reservation, ReservationRequest

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
