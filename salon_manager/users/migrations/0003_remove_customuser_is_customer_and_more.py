# Generated by Django 5.1.6 on 2025-02-23 09:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_employee_services"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customuser",
            name="is_customer",
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="is_employee",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="user",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="work_end",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="work_start",
        ),
        migrations.AddField(
            model_name="customuser",
            name="role",
            field=models.CharField(
                choices=[("CUSTOMER", "Customer"), ("EMPLOYEE", "Employee")],
                default="CUSTOMER",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="name",
            field=models.CharField(default="Adam", max_length=100),
            preserve_default=False,
        ),
    ]
