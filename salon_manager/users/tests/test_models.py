from django.core.exceptions import ValidationError
from django.test import TestCase

from users.models import CustomUser


class CustomUserTest(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            username="owner", password="test", role=CustomUser.Role.OWNER
        )
        self.employee = CustomUser.objects.create_user(
            username="employee", password="test", role=CustomUser.Role.EMPLOYEE
        )
        self.customer = CustomUser.objects.create_user(
            username="customer", password="test", role=CustomUser.Role.CUSTOMER
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
