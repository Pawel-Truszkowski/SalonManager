from django.test import RequestFactory, TestCase
from django.urls import reverse

from services.forms import ServiceForm
from services.models import Service, ServiceCategory
from users.models import CustomUser


class ServiceViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner_user = CustomUser.objects.create_user(
            username="owner", password="test", role="OWNER"
        )
        cls.other_user = CustomUser.objects.create_user(
            username="not_owner", password="test"
        )

        cls.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is category test"
        )
        cls.service = Service.objects.create(
            name="TestService", category=cls.category, price=50.00, duration=30
        )

    def login_owner(self):
        self.client.login(username="owner", password="test")

    def login_user(self):
        self.client.login(username="not_owner", password="test")


class ServiceListViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.url = reverse("services_list")
        self.response = self.client.get(self.url)

    def test_view_if_return_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.assertTemplateUsed(self.response, "services/services_list.html")

    def test_view_with_services_in_context(self):
        self.assertIn(self.service, self.response.context["services"])

    def test_view_with_service_category_in_context(self):
        self.assertIn(self.category, self.response.context["service_categories"])

    def test_view_with_no_services(self):
        Service.objects.all().delete()
        self.response = self.client.get(self.url)
        self.assertEqual(len(self.response.context["services"]), 0)


class ManageServicesListViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.url = reverse("manage_services_list")

    def test_redirects_when_not_logged_in(self):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 302)

    def test_redirects_to_login_page_when_anonymous(self):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 302)
        self.assertRedirects(self.response, "/login/?next=/services/manage-services/")

    def test_view_for_login_other_user_if_redirect_to_home_page(self):
        self.login_user()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 302)
        self.assertRedirects(self.response, "/")

    def test_view_for_login_owner(self):
        self.login_owner()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.login_owner()
        self.response = self.client.get(self.url)
        self.assertTemplateUsed(self.response, "services/manage_services_list.html")

    def test_view_for_services_in_context_data(self):
        self.login_owner()
        self.response = self.client.get(self.url)
        self.assertIn(self.service, self.response.context["services"])

    def test_view_with_no_data_in_context(self):
        Service.objects.all().delete()
        self.login_owner()
        self.response = self.client.get(self.url)
        self.assertQuerySetEqual(self.response.context["services"], [])
        self.assertContains(self.response, "No services found.")


class CreateServiceViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.url = reverse("service_create")
        self.factory = RequestFactory()

    def test_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_denies_access_for_non_owner_user(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_allows_access_for_owner_user(self):
        self.login_owner()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.login_owner()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "services/manage_services_form.html")

    def test_create_service_valid_data_by_owner(self):
        form_data = {
            "name": "TestService2",
            "category": self.category.id,
            "price": 100.00,
            "duration": 60,
        }
        self.login_owner()
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("manage_services_list"))
        self.assertTrue(Service.objects.filter(name="TestService2").exists())
        self.assertContains(response, "Service created successfully!")

    def test_form_invalid_with_missing_required_fields(self):
        self.login_owner()
        initial_count = Service.objects.count()

        form_data = {"name": "", "price": "invalid_price"}

        response = self.client.post(self.url, data=form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), initial_count)

    def test_form_is_valid(self):
        form_data = {
            "name": "TestService2",
            "category": self.category.id,
            "price": 100.00,
            "duration": 60,
        }
        form = ServiceForm(form_data)
        self.assertTrue(form.is_valid())

    def test_form_contains_expected_fields(self):
        self.login_owner()
        response = self.client.get(self.url)
        form = response.context["form"]
        expected_fields = ["name", "category", "price", "duration", "description"]
        for field in expected_fields:
            self.assertIn(field, form.fields)
