from django.urls import path

from . import views, views_ajax

urlpatterns = [
    ######## Stara rezerwacja ##############
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
    # Ajax for New Reservations
    path(
        "<int:service_id>/",
        views_ajax.reservation_request,
        name="reservation_wizard",
    ),
    path(
        "request-submit/",
        views_ajax.reservation_request_submit,
        name="reservation_request_submit",
    ),
    path(
        "available_slots/",
        views_ajax.get_available_slots_ajax,
        name="get_available_slots_ajax",
    ),
    path(
        "request_next_available_slot/",
        views_ajax.get_next_available_date_ajax,
        name="get_next_available_date_ajax",
    ),
    path(
        "request_staff_info/",
        views_ajax.get_non_working_days_ajax,
        name="get_non_working_days_ajax",
    ),
    path(
        "client-info/<int:reservation_request_id>/<str:id_request>/",
        views_ajax.reservation_client_information,
        name="reservation_client_information",
    ),
]
