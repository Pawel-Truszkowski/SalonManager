import io
import os.path
import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from PIL import Image

from services.models import Service, ServiceCategory
from users.models import CustomUser, Employee, Profile

MEDIA_ROOT = tempfile.mkdtemp()


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            username="owner", password="test", role=CustomUser.Role.OWNER
        )
        self.employee = CustomUser.objects.create_user(
            username="employee", password="test", role=CustomUser.Role.EMPLOYEE
        )
        self.customer = CustomUser.objects.create_user(
            username="customer", password="test"
        )

    def test_default_role_is_customer(self):
        self.assertEqual(self.customer.role, CustomUser.Role.CUSTOMER)
        self.assertFalse(self.customer.is_owner)
        self.assertFalse(self.customer.is_employee)

    def test_is_customer_property(self):
        self.assertTrue(self.customer.is_customer)
        self.assertFalse(self.customer.is_owner)
        self.assertFalse(self.customer.is_employee)

    def test_is_owner_property(self):
        self.assertTrue(self.owner.is_owner)
        self.assertFalse(self.owner.is_customer)
        self.assertFalse(self.owner.is_employee)

    def test_is_employee_property(self):
        self.assertTrue(self.employee.is_employee)
        self.assertFalse(self.employee.is_customer)
        self.assertFalse(self.employee.is_owner)

    def test_phone_number_can_be_blank(self):
        self.assertEqual(self.customer.phone_number, "")

    def test_phone_number_validation(self):
        user = CustomUser.objects.create_user(
            username="testuser", phone_number="+48123456789"
        )
        self.assertEqual(str(user.phone_number), "+48123456789")

    def test_invalid_phone_number_rising_error(self):
        with self.assertRaises(ValidationError):
            user = CustomUser.objects.create_user(
                username="testuser", phone_number="invalid_number"
            )
            user.full_clean()

    def test_invalid_role_raises_error(self):
        with self.assertRaises(ValidationError):
            user = CustomUser(username="testuser", role="INVALID_ROLE")
            user.full_clean()


class EmployeeModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="user", password="test")
        self.employee = Employee.objects.create(user=self.user, name="TestEmployee")

    def test_employee_creation_with_user(self):
        self.assertEqual(self.employee.user, self.user)
        self.assertEqual(self.employee.name, "TestEmployee")

    def test_save_sets_user_role_to_employee(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, CustomUser.Role.EMPLOYEE)
        self.assertTrue(self.user.is_employee)

    def test_employee_services_relationship(self):
        category = ServiceCategory.objects.create(name="TestCategory")
        service1 = Service.objects.create(
            name="Service1", category=category, price=100, duration=60
        )
        service2 = Service.objects.create(
            name="Service2", category=category, price=50, duration=30
        )
        self.employee.services.add(service1, service2)

        self.assertEqual(self.employee.services.count(), 2)
        self.assertIn(service1, self.employee.services.all())
        self.assertIn(service2, self.employee.services.all())

    def test_string_representation(self):
        self.assertEqual(str(self.employee), "TestEmployee")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ProfileModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_default_image()

    @classmethod
    def create_default_image(cls):
        default_image_path = os.path.join(MEDIA_ROOT, "default.jpg")
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(default_image_path, "JPEG")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = CustomUser.objects.create_user(username="testuser", password="test")

    def create_test_image(self, width=300, height=300, format="JPEG"):
        image = Image.new("RGB", (width, height), color="red")
        image_file = io.BytesIO()
        image.save(image_file, format=format)
        image_file.seek(0)

        return SimpleUploadedFile(
            "test_img.jpg", content=image_file.getvalue(), content_type="image/jpeg"
        )

    def test_profile_auto_created_by_signal(self):
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertEqual(self.user.profile.user, self.user)

    def test_profile_deleted_when_user_deleted(self):
        profile_id = self.user.profile.id
        self.user.delete()

        with self.assertRaises(Profile.DoesNotExist):
            Profile.objects.get(id=profile_id)

    def test_large_image_get_resized(self):
        large_image = self.create_test_image(width=500, height=500)
        profile = self.user.profile
        profile.image = large_image
        profile.save()

        with Image.open(profile.image.path) as img:
            self.assertLessEqual(img.width, 300)
            self.assertLessEqual(img.height, 300)

    def test_small_image_get_resized(self):
        small_image = self.create_test_image(width=100, height=100)
        profile = self.user.profile
        profile.image = small_image
        profile.save()

        with Image.open(profile.image.path) as img:
            self.assertLessEqual(img.width, 300)
            self.assertLessEqual(img.height, 300)
