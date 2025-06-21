from django.contrib import messages
from django.shortcuts import render

from .forms import ContactForm
from .models import Contact
from .tasks import send_email_to_admin, send_email_to_customer


def home(request):
    return render(request, "dashboard/index.html")


def about(request):
    return render(request, "dashboard/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            con = form.save()

            con.save()
            messages.success(request, "Your message has been sent.")

            send_email_to_customer.delay_on_commit(
                first_name=con.first_name, last_name=con.last_name, email=con.email
            )
            send_email_to_admin.delay_on_commit(
                first_name=con.first_name,
                last_name=con.last_name,
                email=con.email,
                subject=con.subject,
                message=con.message,
            )

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ContactForm()

    return render(request, "dashboard/contact.html", {"form": form})
