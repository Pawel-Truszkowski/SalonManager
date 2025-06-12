from django.urls import path

from . import views, views_ajax

urlpatterns = [
    path(
        "your-reservations/",
        views.UserReservationsListView.as_view(),
        name="your_reservation_list",
    ),
    path(
        "reservation-cancel/<int:pk>/",
        views.CancelUserReservationView.as_view(),
        name="cancel_reservation",
    ),
    path(
        "reservation-success/",
        views.ReservationSuccessView.as_view(),
        name="reservation_success",
    ),
    # New Reservations
    path(
        "<int:service_id>/",
        views_ajax.reservation_request,
        name="reservation_request",
    ),
    path(
        "request-submit/",
        views_ajax.reservation_request_submit,
        name="reservation_request_submit",
    ),
    path(
        "client-info/<int:reservation_request_id>/<str:id_request>/",
        views_ajax.reservation_client_information,
        name="reservation_client_information",
    ),
    # Ajax for New Reservations
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
    # WorkDay Management URLs
    path("workdays/", views.WorkDayListView.as_view(), name="workday_list"),
    path("workdays/add/", views.WorkDayCreateView.as_view(), name="workday_create"),
    path(
        "workdays/<int:pk>/update/",
        views.WorkDayUpdateView.as_view(),
        name="workday_update",
    ),
    path(
        "workdays/<int:pk>/delete/",
        views.WorkDayDeleteView.as_view(),
        name="workday_delete",
    ),
    # API endpoints for FullCalendar
    path("api/workdays/", views.workday_api, name="workday_api"),
    path(
        "workdays/<int:pk>/update-date/",
        views.update_workday_date,
        name="update_workday_date",
    ),
    # Reservation Management URLs
    path(
        "manage-reservations/",
        views.ManageReservationsListView.as_view(),
        name="manage_reservations_list",
    ),
    path(
        "manage-reservations/add",
        views.ReservationCreateView.as_view(),
        name="reservation_create",
    ),
    path(
        "reservations/<int:pk>/edit/",
        views.ReservationUpdateView.as_view(),
        name="reservation_edit",
    ),
    path(
        "manage-reservations/<int:pk>/delete/",
        views.ReservationDeleteView.as_view(),
        name="reservation_delete",
    ),
    path(
        "reservations/<int:pk>/confirm/",
        views.ConfirmReservationView.as_view(),
        name="reservation_confirm",
    ),
    path("api/reservations/", views.reservations_api, name="reservations_api"),
]
