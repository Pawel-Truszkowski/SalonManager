from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from dashboard.tasks import send_email_to_admin, send_email_to_customer


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TestSendEmailToCustomer(TestCase):
    def setUp(self):
        mail.outbox = []
        self.first_name = "John"
        self.last_name = "Doe"
        self.email = "john@example.com"

    def test_send_email_to_customer_if_success(self):
        result = send_email_to_customer(self.first_name, self.last_name, self.email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(result)

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Thanks for contacting!")
        self.assertIn("Hello John Doe!", email.body)
        self.assertIn(
            "Thanks for contacting, we will get back to you shortly.", email.body
        )
        self.assertIn("Your Beauty Salon - Royal Beauty", email.body)

        self.assertEqual(email.to, ["john@example.com"])
        self.assertEqual(email.from_email, settings.EMAIL_HOST_USER)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
    OWNER_EMAIL="test@test.com",
)
class TestSendEmailToAdmin(TestCase):
    def setUp(self):
        mail.outbox = []
        self.first_name = "John"
        self.last_name = "Doe"
        self.email = "john@example.com"
        self.subject = "Contact"
        self.message = "Test test test"

    def test_send_email_to_admin_if_success(self):
        result = send_email_to_admin(
            self.first_name, self.last_name, self.email, self.subject, self.message
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(result)

        email = mail.outbox[0]
        self.assertEqual(email.subject, self.subject)
        self.assertIn("Sent by,", email.body)

        self.assertEqual(email.to, ["test@test.com"])
        self.assertEqual(email.from_email, "no-reply@example.com")

        self.assertTrue(result)
