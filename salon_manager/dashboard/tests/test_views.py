from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from dashboard.forms import ContactForm
from dashboard.models import Contact


class TestHomeView(TestCase):
    def test_home_view_response_status_code_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_view_which_contains_correct_words(self):
        response = self.client.get("/")
        self.assertTemplateUsed(response, "dashboard/index.html")

    def test_home_view_uses_correct_template(self):
        response = self.client.get("/")
        self.assertTemplateUsed(response, "dashboard/index.html")


class TestAboutView(TestCase):
    def setUp(self):
        self.url = reverse("about")
        self.response = self.client.get(self.url)

    def test_about_view_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_home_view_which_contains_correct_words(self):
        self.assertTemplateUsed(self.response, "dashboard/about.html")

    def test_home_view_uses_correct_template(self):
        self.assertTemplateUsed(self.response, "dashboard/about.html")


class TestContactView(TestCase):
    def setUp(self):
        self.url = reverse("contact")
        self.valid_data = {
            "first_name": "Test",
            "last_name": "Case",
            "email": "test@test.com",
            "subject": "Test-Case",
            "message": "Testing massage was sent",
        }
        self.invalid_data = {
            "first_name": "",
            "last_name": "",
            "email": "testtest.com",
            "subject": "",
            "message": "Testing massage was sent",
        }

    def test_contact_view_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/contact.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ContactForm)

    @patch("dashboard.views.send_email_to_customer")
    @patch("dashboard.views.send_email_to_admin")
    def test_contact_view_post_valid_data(self, mock_admin_email, mock_customer_email):
        response = self.client.post(self.url, self.valid_data)
        contact_exists = Contact.objects.filter(email="test@test.com").exists()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(contact_exists)
        form = response.context["form"]
        self.assertTrue(form.is_valid())
        mock_customer_email.delay_on_commit.assert_called_once()
        mock_admin_email.delay_on_commit.assert_called_once()
        message = list(get_messages(response.wsgi_request))
        self.assertEqual(str(message[0]), "Your message has been sent.")

    def test_contact_view_post_invalid_data(self):
        response = self.client.post(self.url, self.invalid_data)
        form = response.context["form"]
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/contact.html")
        contact_exists = Contact.objects.filter(first_name="Test").exists()
        self.assertFalse(contact_exists)
        self.assertFalse(form.is_valid())
        message = list(get_messages(response.wsgi_request))
        self.assertEqual(str(message[0]), "Please correct the errors below.")

    def test_contact_view_form_fields_present(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name="last_name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="subject"')
        self.assertContains(response, 'name="message"')
