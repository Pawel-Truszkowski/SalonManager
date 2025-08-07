from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from services.forms import ServiceForm
from services.models import Service, ServiceCategory
from users.models import CustomUser


class ServiceViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner_user = CustomUser.objects.create_user(
            username="owner", password="test", role=CustomUser.Role.OWNER
        )
        cls.other_user = CustomUser.objects.create_user(
            username="not_owner", password="test"
        )

    def login_owner(self):
        self.client.login(username="owner", password="test")

    def login_user(self):
        self.client.login(username="not_owner", password="test")


class ServiceListViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.url = reverse("services_list")

        self.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is category test"
        )
        self.service = Service.objects.create(
            name="TestService", category=self.category, price=50.00, duration=30
        )

    def test_view_if_return_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "services/services_list.html")

    def test_view_with_services_in_context(self):
        response = self.client.get(self.url)
        self.assertIn(self.service, response.context["services"])

    def test_view_with_service_category_in_context(self):
        response = self.client.get(self.url)
        self.assertIn(self.category, response.context["service_categories"])

    def test_view_with_no_services(self):
        Service.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["services"]), 0)


class ManageServicesListViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.url = reverse("manage_services_list")

        self.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is category test"
        )
        self.service = Service.objects.create(
            name="TestService", category=self.category, price=50.00, duration=30
        )

    def test_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redirects_to_login_page_when_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, "/login/?next=/services/manage-services/")

    def test_view_for_login_other_user_if_redirect_to_home_page(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/")

    def test_view_for_login_owner(self):
        self.login_owner()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.login_owner()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "services/manage_services_list.html")

    def test_view_for_services_in_context_data(self):
        self.login_owner()
        response = self.client.get(self.url)
        self.assertIn(self.service, response.context["services"])

    def test_view_with_no_data_in_context(self):
        Service.objects.all().delete()
        self.login_owner()
        response = self.client.get(self.url)
        self.assertQuerySetEqual(response.context["services"], [])
        self.assertContains(response, "No services found.")


class CreateServiceViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.url = reverse("service_create")

        self.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is category test"
        )
        self.service = Service.objects.create(
            name="TestService", category=self.category, price=50.00, duration=30
        )

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
            "name": "CreateService",
            "category": self.category.id,
            "price": 100.00,
            "duration": 60,
        }
        self.login_owner()
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("manage_services_list"))
        self.assertTrue(Service.objects.filter(name="CreateService").exists())
        self.assertContains(response, "Service created successfully!")

    def test_form_invalid_with_missing_required_fields(self):
        self.login_owner()
        initial_count = Service.objects.count()
        form_data = {"name": "", "price": "invalid_price"}

        response = self.client.post(self.url, data=form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), initial_count)
        self.assertContains(response, "Form contains errors. Please check all fields.")

    def test_form_is_valid_directly(self):
        form_data = {
            "name": "TestForm",
            "category": self.category.id,
            "price": 100.00,
            "duration": 60,
        }
        form = ServiceForm(form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_directly(self):
        form_data = {
            "name": "InvalidTestForm",
            "category": "Test Category",
            "price": -10,
            "duration": 10,
        }
        form = ServiceForm(data=form_data)
        self.assertIn(
            "Select a valid choice. That choice is not one of the available choices.",
            form.errors["category"],
        )
        self.assertIn(
            "Ensure this value is greater than or equal to 0.", form.errors["price"]
        )
        self.assertIn(
            "Ensure this value is greater than or equal to 15.", form.errors["duration"]
        )

    def test_form_contains_expected_fields(self):
        self.login_owner()
        response = self.client.get(self.url)
        form = response.context["form"]
        expected_fields = ["name", "category", "price", "duration", "description"]
        for field in expected_fields:
            self.assertIn(field, form.fields)


class ServiceUpdateViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is a test category"
        )
        self.service = Service.objects.create(
            name="OriginalService",
            category=self.category,
            price=50.00,
            duration=30,
        )
        self.url = reverse("service_update", args=[self.service.id])

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

    def test_update_service_valid_data_by_owner(self):
        self.login_owner()
        form_data = {
            "name": "UpdatedService",
            "category": self.category.id,
            "price": 120.00,
            "duration": 45,
            "description": "Updated description",
        }
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("manage_services_list"))

        self.service.refresh_from_db()
        self.assertEqual(self.service.name, "UpdatedService")
        self.assertEqual(self.service.price, 120.00)
        self.assertEqual(self.service.duration, 45)
        self.assertEqual(self.service.description, "Updated description")

        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Service updated successfully!", [m.message for m in messages])

    def test_update_service_invalid_data(self):
        self.login_owner()
        initial_name = self.service.name
        form_data = {"name": "", "price": "invalid_price"}
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.service.refresh_from_db()
        self.assertEqual(self.service.name, initial_name)
        self.assertContains(response, "This field is required.")

    def test_form_fields_in_context(self):
        self.login_owner()
        response = self.client.get(self.url)
        form = response.context["form"]
        expected_fields = ["name", "category", "price", "duration", "description"]
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_form_valid_directly(self):
        form_data = {
            "name": "DirectFormTest",
            "category": self.category.id,
            "price": 80.00,
            "duration": 30,
        }
        form = ServiceForm(data=form_data, instance=self.service)
        self.assertTrue(form.is_valid())


class ServiceDeleteViewTest(ServiceViewsTestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name="TestCategory", description="This is a test category"
        )
        self.service = Service.objects.create(
            name="ServiceToDelete",
            category=self.category,
            price=50.00,
            duration=30,
        )
        self.url = reverse("service_delete", args=[self.service.id])

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
        self.assertTemplateUsed(response, "services/manage_services_delete.html")

    def test_delete_service_by_owner(self):
        self.login_owner()
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("manage_services_list"))
        self.assertFalse(Service.objects.filter(id=self.service.id).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Service deleted successfully!", [m.message for m in messages])

    def test_delete_service_requires_post(self):
        self.login_owner()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Service.objects.filter(id=self.service.id).exists())
