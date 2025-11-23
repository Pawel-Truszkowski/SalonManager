from django.test import TestCase
from services.models import Service, ServiceCategory


class ServiceCategoryModel(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name="Test", description="Test Category"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.category), "Test")

    def test_service_category_creation(self):
        self.assertEqual(self.category.name, "Test")
        self.assertEqual(self.category.description, "Test Category")


class ServiceModelTest(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name="Test", description="Test Category"
        )
        self.service = Service.objects.create(
            name="Test", category=self.category, price=50.00, duration=30
        )

    def test_str_representation(self):
        self.assertEqual(str(self.service), "Test - 30 min")

    def test_service_creation(self):
        self.assertEqual(self.service.name, "Test")
        self.assertEqual(self.service.price, 50.00)
