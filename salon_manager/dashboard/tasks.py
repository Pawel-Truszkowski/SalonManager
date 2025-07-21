from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_email_to_customer(first_name, last_name, email):
    message = (
        f"Hello {first_name} {last_name}! \n\n"
        f"Thanks for contacting, we will get back to you shortly. \n"
        f"Your Beauty Salon - Royal Beauty"
    )
    return send_mail(
        "Thanks for contacting!",
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )


@shared_task
def send_email_to_admin(first_name, last_name, email, subject, message):
    return send_mail(
        subject,
        f"Sent by,\n    Name: {first_name} {last_name} \n    Email: {email} \n\n{message}",
        settings.DEFAULT_FROM_EMAIL,
        [settings.OWNER_EMAIL],
        fail_silently=False,
    )
