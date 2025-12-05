from django.core.validators import MinValueValidator
from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Optional description of the category (purpose, group of services, etc.).",
    )

    def __str__(self) -> str:
        return self.name


class Service(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Service name.",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Details of the service, notes or treatment composition.",
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
        help_text="Category this service belongs to.",
    )
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(limit_value=0)],
        help_text="Price in PLN (e.g. 99.99). Must be non-negative.",
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(limit_value=15)],
        help_text="Duration of the service in minutes (minimum 15).",
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.duration} min"
