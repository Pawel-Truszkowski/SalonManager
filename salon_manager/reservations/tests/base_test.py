from datetime import date, time

from django.test import TestCase
from reservations.models import WorkDay
from services.models import Service, ServiceCategory
from users.models import CustomUser, Employee


class BaseTestCase(TestCase):
    USER_SPECS = {
        "employee1": {
            "first_name": "Daniel",
            "last_name": "Jackson",
            "email": "daniel.jackson@test.com",
            "username": "daniel.jackson",
            "phone_number": "+48600700900",
            "role": "EMPLOYEE",
        },
        "employee2": {
            "first_name": "Samantha",
            "last_name": "Carter",
            "email": "samantha.carter@test.com",
            "username": "samantha.carter",
            "phone_number": "+48900700900",
            "role": "EMPLOYEE",
        },
        "client1": {
            "first_name": "Georges",
            "last_name": "Hammond",
            "email": "georges.s.hammond@test.com",
            "username": "georges.hammond",
            "phone_number": "+48611711911",
            "role": "CUSTOMER",
        },
        "client2": {
            "first_name": "Tealc",
            "last_name": "Kree",
            "email": "tealc.kree@test.com",
            "username": "tealc.kree",
            "phone_number": "+48700600900",
            "role": "CUSTOMER",
        },
        "superuser": {
            "first_name": "Jack",
            "last_name": "O'Neill",
            "email": "jack-oneill@test.com",
            "username": "jack.o.neill",
            "phone_number": "+48600700900",
            "role": "OWNER",
        },
    }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.users = {}
        for key, details in cls.USER_SPECS.items():
            user = CustomUser.objects.create_user(**details)
            cls.users[key] = user

        cls.service_category1 = ServiceCategory.objects.create(
            name="Manicure", description="This is category of service for testing"
        )
        cls.service1 = Service.objects.create(
            name="Manicure classic",
            description="This is service1 for testing",
            category=cls.service_category1,
            duration=60,
            price=200,
        )
        cls.employee1 = Employee.objects.create(
            user=cls.users["employee1"], name="Daniel"
        )
        cls.employee1.services.add(cls.service1)
        cls.workday = WorkDay.objects.create(
            employee=cls.employee1,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
