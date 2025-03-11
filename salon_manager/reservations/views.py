import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from formtools.wizard.views import SessionWizardView

from . import forms
from .models import Reservation

FORMS = [
    ("customer", forms.CustomerInfoForm),
    ("service", forms.ServiceSelectionForm),
    ("employee", forms.EmployeeSelectionForm),
    ("date", forms.DateSelectionForm),
    ("time", forms.TimeSelectionForm),
    ("confirm", forms.ConfirmationForm),
]


TEMPLATES = {
    "customer": "reservations/wizard/customer_info.html",
    "service": "reservations/wizard/service_selection.html",
    "employee": "reservations/wizard/employee_selection.html",
    "date": "reservations/wizard/date_selection.html",
    "time": "reservations/wizard/time_selection.html",
    "confirm": "reservations/wizard/confirmation.html",
}


@method_decorator(login_required, name="dispatch")
class ReservationWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if step == "customer":
            kwargs["user"] = self.request.user

        elif step == "employee":
            service_data = self.get_cleaned_data_for_step("service")
            if service_data:
                kwargs["service"] = service_data["service"]

        elif step == "date":
            employee_data = self.get_cleaned_data_for_step("employee")
            if employee_data:
                kwargs["employee"] = employee_data["employee"]

        elif step == "time":
            employee_data = self.get_cleaned_data_for_step("employee")
            date_data = self.get_cleaned_data_for_step("date")
            service_data = self.get_cleaned_data_for_step("service")

            if employee_data and date_data and service_data:
                kwargs["employee"] = employee_data["employee"]
                kwargs["date"] = date_data["reservation_date"]
                kwargs["service"] = service_data["service"]

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == "confirm":
            service_data = self.get_cleaned_data_for_step("service")
            employee_data = self.get_cleaned_data_for_step("employee")
            date_data = self.get_cleaned_data_for_step("date")
            time_data = self.get_cleaned_data_for_step("time")

            start_datetime = datetime.datetime.combine(
                date_data["reservation_date"], time_data["start_time"]
            )
            duration = datetime.timedelta(minutes=service_data["service"].duration)
            end_datetime = start_datetime + duration

            context["end_time"] = end_datetime.time()

            context.update(
                {
                    "service": service_data["service"],
                    "employee": employee_data["employee"],
                    "reservation_date": date_data["reservation_date"],
                    "start_time": time_data["start_time"],
                }
            )

        return context

    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()

        reservation = Reservation(
            customer=self.request.user,
            service=all_data["service"],
            employee=all_data["employee"],
            reservation_date=all_data["reservation_date"],
            start_time=all_data["start_time"],
            status="PENDING",
        )

        reservation.save()

        messages.success(self.request, "Twoja wizyta została dodana pomyślnie!")
        return redirect("reservation_success")


@login_required(redirect_field_name="login")
def reservation_success(request):
    return render(request, "reservations/reservation_success.html")
