# Generated by Django 5.1.6 on 2025-05-10 09:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0005_alter_reservation_customer"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="email",
            field=models.EmailField(default="email@email.com", max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="reservation",
            name="name",
            field=models.CharField(default="name", max_length=100),
            preserve_default=False,
        ),
    ]
