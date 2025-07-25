from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image

from services.models import Service


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        CUSTOMER = "CUSTOMER", "Customer"
        EMPLOYEE = "EMPLOYEE", "Employee"

    phone_number = PhoneNumberField(blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)

    @property
    def is_customer(self) -> bool:
        return self.role == self.Role.CUSTOMER

    @property
    def is_owner(self) -> bool:
        return self.role == self.Role.OWNER

    @property
    def is_employee(self) -> bool:
        return self.role == self.Role.EMPLOYEE


class Employee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    services = models.ManyToManyField(Service, related_name="employees")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.user.role != self.Role.EMPLOYEE:
            self.user.role = self.Role.EMPLOYEE
            self.user.save()

        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    image = models.ImageField(default="default.jpg", upload_to="profile_pics")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def __str__(self):
        return f"Profile of {self.user.username}"
