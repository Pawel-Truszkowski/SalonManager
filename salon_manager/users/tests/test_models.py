from django.core.exceptions import ValidationError
from django.test import TestCase

from services.models import Service, ServiceCategory
from users.models import CustomUser, Employee


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
