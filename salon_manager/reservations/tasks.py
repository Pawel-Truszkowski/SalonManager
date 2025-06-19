from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
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
