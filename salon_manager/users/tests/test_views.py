import io
import os.path
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from users.forms import ProfileUpdateForm, UserUpdateForm
from users.models import Profile

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()


class RegisterViewTest(TestCase):
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


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        if not hasattr(self.user, "profile"):
            Profile.objects.create(user=self.user)

        self.profile_url = reverse("profile")

    def tearDown(self):
        if hasattr(self.user, "profile") and hasattr(self.user.profile, "image"):
            if self.user.profile.image:
                self.user.profile.image.delete()

    @classmethod
    def create_default_image(cls):
        default_image_path = os.path.join(MEDIA_ROOT, "default.jpg")
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(default_image_path, "JPEG")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @staticmethod
    def create_test_image(width=300, height=300, format="JPEG"):
        image = Image.new("RGB", (width, height), color="red")
        image_file = io.BytesIO()
        image.save(image_file, format=format)
        image_file.seek(0)

        return SimpleUploadedFile(
            "test_img.jpg", content=image_file.getvalue(), content_type="image/jpeg"
        )

    def test_profile_view_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/login/?next={self.profile_url}")

    def test_profile_view_get_logged_in_user(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")
        self.assertIn("user_form", response.context)
        self.assertIn("profile_form", response.context)

        user_form = response.context["user_form"]
        self.assertEqual(user_form.instance, self.user)

    def test_profile_view_uses_correct_template(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_profile_update_valid_post_data_with_image_upload(self):
        self.client.login(username="testuser", password="testpass123")

        test_image = self.create_test_image(300, 300)

        post_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "phone_number_0": "PL",
            "phone_number_1": "500111222",
            "image": test_image,
        }

        response = self.client.post(self.profile_url, post_data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.first_name, "Updated")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your profile's been updated!")

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.image)

    def test_profile_update_invalid_user_form(self):
        self.client.login(username="testuser", password="testpass123")

        post_data = {
            "email": "invalid-email",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post(self.profile_url, post_data)

        self.assertIn("user_form", response.context)
        user_form = response.context["user_form"]
        self.assertTrue(user_form.errors)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")

    def test_profile_update_invalid_profile_form(self):
        self.client.login(username="testuser", password="testpass123")

        post_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "image": "",
        }

        response = self.client.post(self.profile_url, post_data)

        messages = list(get_messages(response.wsgi_request))
        success_messages = [msg for msg in messages if "updated" in str(msg)]
        self.assertEqual(len(success_messages), 0)

    def test_profile_view_context_contains_forms(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)

        self.assertIsInstance(response.context["user_form"], UserUpdateForm)
        self.assertIsInstance(response.context["profile_form"], ProfileUpdateForm)

    def test_profile_forms_have_correct_instances(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)

        user_form = response.context["user_form"]
        profile_form = response.context["profile_form"]

        self.assertEqual(user_form.instance, self.user)
        self.assertEqual(profile_form.instance, self.user.profile)
