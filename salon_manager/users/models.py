from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image
from services.models import Service


class CustomUser(AbstractUser):
    phone_number = PhoneNumberField(blank=True)
    is_customer = models.BooleanField(default=True)
    is_employee = models.BooleanField(default=False)


class Employee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    work_start = models.TimeField()
    work_end = models.TimeField()
    services = models.ManyToManyField(Service, related_name="employees")

    def __str__(self):
        return self.user.get_full_name()


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
