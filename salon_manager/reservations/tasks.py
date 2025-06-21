from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task
def send_reservation_notification(customer, service, date, time):
    subject = "New reservation!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.OWNER_EMAIL]

    context = {
        "customer": customer,
        "service": service,
        "date": date,
        "time": time,
    }

    text_content = (
        f"Customer name: {customer}\n"
        f"Service: {service}\n"
        f"Date: {date}\n"
        f"Time: {time}\n\n"
        "Login to owner panel to look more details."
    )

    html_content = render_to_string("emails/reservation_notification.html", context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")

    return msg.send()


@shared_task
def send_confirmation_email(
    customer_email, customer_name, service_name, date, time, cancel_url
):
    subject = "Reservation confirmation"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [customer_email]

    context = {
        "customer_name": customer_name,
        "service_name": service_name,
        "date": date,
        "time": time,
        "cancel_url": cancel_url,
        "current_year": date.today().year,
    }

    html_content = render_to_string("emails/confirmation_email.html", context)
    text_content = (
        f"Cześć {customer_name},\n\n"
        f'Twoja rezerwacja na usługę "{service_name}" została potwierdzona.\n'
        f"Data: {date}, Godzina: {time}\n\n"
        "Do zobaczenia w salonie!"
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    return msg.send()
