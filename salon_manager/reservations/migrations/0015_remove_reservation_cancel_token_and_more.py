# Generated by Django 5.1.6 on 2025-06-20 14:29

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0014_alter_reservation_cancel_token"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="reservation",
            name="cancel_token",
        ),
        migrations.RemoveField(
            model_name="reservation",
            name="cancel_token_created_at",
        ),
    ]
