import json
from datetime import date, time, timedelta

from django.contrib.messages import get_messages
from django.urls import reverse
from reservations.models import Reservation, ReservationRequest, WorkDay

from salon_manager.reservations.tests.base_test import BaseTestCase


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
        self.url = reverse("workday_edit", kwargs={"pk": self.workday.pk})

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
        url = reverse("workday_edit", kwargs={"pk": 99999})
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
