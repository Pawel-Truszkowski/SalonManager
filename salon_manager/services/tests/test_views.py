from django.test import Client, TestCase
from django.urls import reverse

from services.forms import ServiceForm
from services.models import Service, ServiceCategory
from users.models import CustomUser


class ServiceViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        username = "testuser"
        test_password = "testpassword123"  # nosec

        self.user = CustomUser.objects.create_user(
            username=username, password=test_password
        )

        self.category = ServiceCategory.objects.create(
            name="Test", description="Test Category"
        )
        self.service = Service.objects.create(
            name="Test", category=self.category, price=50.00, duration=30
        )


class ServiceListViewTest(ServiceViewsTestCase):
    def test_list_view_if_success(self):
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
