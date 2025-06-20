import uuid

from django.db import migrations


def generate_tokens(apps, schema_editor):
    Reservation = apps.get_model("reservations", "Reservation")
    for reservation in Reservation.objects.all():
        reservation.cancel_token = uuid.uuid4()
        reservation.save()


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0008_reservation_cancel_token_and_more"),
    ]

    operations = [
        migrations.RunPython(generate_tokens),
    ]
