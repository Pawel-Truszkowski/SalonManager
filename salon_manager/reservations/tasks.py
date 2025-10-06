from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now, timedelta

from .models import Reservation, ReservationRequest


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


@shared_task
def send_upcoming_reminder():
    today = now()
    tomorrow = today.date() + timedelta(days=1)

    reservations = Reservation.objects.filter(
        reservation_request__date=tomorrow, status="CONFIRMED"
    )

    email_counter = 0

    for reservation in reservations:
        subject = "Your appointment is tomorrow!"
        to_email = reservation.email
        context = {
            "name": reservation.name,
            "date": reservation.reservation_request.date,
            "time": reservation.reservation_request.start_time,
            "service": reservation.get_service_name(),
        }
        html_message = render_to_string("emails/upcoming_reminder.html", context)
        send_mail(
            subject,
            f"Hi {reservation.name}, don't forget your appointment tomorrow at {reservation.reservation_request.start_time}.",
            "noreply@twojsalon.pl",
            [to_email],
            html_message=html_message,
        )
        email_counter += 1

    return f"Sent {email_counter} reminder emails."


@shared_task
def change_reservation_status():
    today = now().date()

    reservations = Reservation.objects.filter(
        status="CONFIRMED", reservation_request__date__lte=today
    )

    updated_count = 0

    for reservation in reservations:
        end_time = reservation.get_end_time()
        if reservation.get_date() < today or (
            reservation.get_date() == today and end_time and today > end_time
        ):
            reservation.status = "PAST"
            reservation.save()
            updated_count += 1

    return f"Updated {updated_count} reservations as PAST"


@shared_task
def cleanup_expired_requests():
    expired_requests = ReservationRequest.objects.filter(
        expires_at__lt=now(), reservation__isnull=True
    )
    count = expired_requests.count()
    expired_requests.delete()
    return f"Deleted {count} expired requests"
