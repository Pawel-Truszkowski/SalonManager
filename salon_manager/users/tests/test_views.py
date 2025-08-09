from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegisterUserViewTest(TestCase):
    def setUp(self):
        self.url = reverse("register")

    def test_register_view_get_request(self):
        response = self.client.get("/register/")
        self.assertLessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
        self.assertIn("form", response.context)

    def test_register_post_valid_form(self):
        data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "phone_number_0": "PL",
            "phone_number_1": "500111222",
            "email": "test@example.com",
            "password1": "SuperSecure123!",
            "password2": "SuperSecure123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register_done.html")
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertIn("username", response.context)
        self.assertEqual(response.context["username"], "testuser")

    def test_register_post_invalid_form(self):
        data = {
            "username": "",
            "password1": "pass123",
            "password2": "differentpass123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertFalse(User.objects.exists())

    def test_register_new_user_with_existing_email_should_fail(self):
        User.objects.create_user(
            username="testuser", email="test@test.com", password="securepassword123"
        )

        data = {
            "username": "user",
            "first_name": "Test",
            "last_name": "User",
            "phone_number_0": "PL",
            "phone_number_1": "500111222",
            "email": "test@test.com",
            "password1": "SuperSecure123!",
            "password2": "SuperSecure123!",
        }

        response = self.client.post(self.url, data)
        form = response.context["form"]

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("This email address is already in use.", form.errors["email"])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
