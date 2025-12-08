from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import ContactForm
from .tasks import send_email_to_admin, send_email_to_customer


class HomeView(TemplateView):
    template_name = "dashboard/index.html"


class AboutView(TemplateView):
    template_name = "dashboard/about.html"


class ContactView(FormView):
    form_class = ContactForm
    template_name = "dashboard/contact.html"
    success_url = reverse_lazy("dashboard:contact")

    def form_valid(self, form):
        con = form.save()
        messages.success(self.request, "Your message has been sent.")

        send_email_to_customer.delay_on_commit(  # type: ignore[attr-defined]
            first_name=con.first_name, last_name=con.last_name, email=con.email
        )
        send_email_to_admin.delay_on_commit(  # type: ignore[attr-defined]
            first_name=con.first_name,
            last_name=con.last_name,
            email=con.email,
            subject=con.subject,
            message=con.message,
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)
