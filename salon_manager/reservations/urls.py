from django.urls import path

from . import views

urlpatterns = [
    path("", views.ReservationWizard.as_view(views.FORMS), name="reservation_wizard"),
    path(
        "booking-success/",
        views.ReservationSuccessView.as_view(),
        name="reservation_success",
    ),
    path(
        "your-reservations/",
        views.ReservationsListView.as_view(),
        name="your_reservation_list",
    ),
    path(
        "reservation-cancel/<int:pk>/",
        views.CancelReservationView.as_view(),
        name="cancel_reservation",
    ),
    # Ajax URLs
    path("ajax/get-employees/", views.get_employees, name="get_employees"),
    path("ajax/get-dates/", views.get_available_dates, name="get_available_dates"),
    path("ajax/get-times/", views.get_available_times, name="get_available_times"),
]
