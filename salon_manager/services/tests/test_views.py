from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from services.forms import ServiceForm
from services.models import Service, ServiceCategory


class ServiceViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        test_password = "testpassword123"  # nosec

        self.user = User.objects.create_user(
            username="testuser", password=test_password
        )

        self.category = ServiceCategory.objects.create(
            name="Test", description="Test Category"
        )
        self.service = Service.objects.create(
            name="Test", category=self.category, price=50.00, duration=30
        )


class ServiceListViewTest(ServiceViewsTestCase):
    pass
