from django.core.validators import MinValueValidator
from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.CASCADE, related_name="services"
    )
    price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(limit_value=0)]
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(limit_value=15)]
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.duration} min"
