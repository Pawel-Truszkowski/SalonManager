from django.urls import path

from . import views

urlpatterns = [
    path(
        "book/", views.ReservationWizard.as_view(views.FORMS), name="reservation_wizard"
    ),
    path("booking-success/", views.reservation_success, name="reservation_success"),
    # Ajax URLs
    path("ajax/get-employees/", views.get_employees, name="get_employees"),
    path("ajax/get-dates/", views.get_available_dates, name="get_available_dates"),
    path("ajax/get-times/", views.get_available_times, name="get_available_times"),
]
