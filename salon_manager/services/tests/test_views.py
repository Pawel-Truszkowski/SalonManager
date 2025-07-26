from django.test import Client, TestCase
from django.urls import reverse

from services.forms import ServiceForm
from services.models import Service, ServiceCategory
from users.models import CustomUser


class ServiceViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.owner_user = CustomUser.objects.create_user(
            username="owner", password="test", role="OWNER"
        )
        self.other_user = CustomUser.objects.create_user(
            username="not_owner", password="test"
        )

        self.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is category test"
        )
        self.service = Service.objects.create(
            name="TestService", category=self.category, price=50.00, duration=30
        )


class ServiceListViewTest(ServiceViewsTestCase):
    def test_view_if_success(self):
        response = self.client.get(reverse("services_list"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("services_list"))
        self.assertTemplateUsed(response, "services/services_list.html")

    def test_view_with_services_in_context(self):
        response = self.client.get(reverse("services_list"))
        self.assertIn(self.service, response.context["services"])

    def test_view_with_service_category_in_context(self):
        response = self.client.get(reverse("services_list"))
        self.assertIn(self.category, response.context["service_categories"])

    def test_view_with_no_services(self):
        Service.objects.all().delete()
        response = self.client.get(reverse("services_list"))
        self.assertEqual(len(response.context["services"]), 0)


class ManageServicesListViewTest(ServiceViewsTestCase):
    def test_view_for_nobody_login(self):
        response = self.client.get(reverse("manage_services_list"))
        self.assertEqual(response.status_code, 302)

    def test_view_for_login_other_user(self):
        self.client.login(username="not_owner", password="test")
        response = self.client.get(reverse("manage_services_list"))
        self.assertEqual(response.status_code, 302)

    def test_view_for_login_owner(self):
        self.client.login(username="owner", password="test")
        response = self.client.get(reverse("manage_services_list"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.login(username="owner", password="test")
        response = self.client.get(reverse("manage_services_list"))
        self.assertTemplateUsed(response, "services/manage_services_list.html")

    def test_view_for_services_in_context_data(self):
        self.client.login(username="owner", password="test")
        response = self.client.get(reverse("manage_services_list"))
        self.assertIn(self.service, response.context["services"])

    def test_view_with_no_data_in_context(self):
        Service.objects.all().delete()
        self.client.login(username="owner", password="test")
        response = self.client.get(reverse("manage_services_list"))
        self.assertQuerysetEqual(response.context["services"], [])
        self.assertContains(response, "No services found.")
