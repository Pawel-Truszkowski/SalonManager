from django.contrib.auth import get_user_model
from django.test import TestCase

from users.forms import UserRegisterForm

User = get_user_model()


class UserRegisterFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            "username": "newuser",
            "first_name": "Test",
            "last_name": "User",
            "phone_number_0": "PL",
            "phone_number_1": "500111222",
            "email": "new@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_email(self):
        User.objects.create_user(
            username="user1", email="test@example.com", password="pass123"
        )
        form_data = {
            "username": "user2",
            "first_name": "Test",
            "last_name": "User",
            "phone_number_0": "PL",
            "phone_number_1": "500111222",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
