# Generated by Django 5.1.6 on 2025-02-21 19:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="services",
            field=models.ManyToManyField(
                related_name="employees", to="services.service"
            ),
        ),
    ]
