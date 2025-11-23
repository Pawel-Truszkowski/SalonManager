from django.urls import path

from . import api, views, views_reservation  # TODO importy konkretne

# TODO app_name = "reservations"  # reservations:sucess
urlpatterns = [
    path(
        "reservation-success/",
        views.ReservationSuccessView.as_view(),
        name="reservation_success",  # success
    ),
    path(
        "your-reservations/",  # my/
        views.UserReservationsListView.as_view(),
        name="user_reservations_list",
    ),
    path(
        "reservation-cancel/<int:pk>/",  # reservations/cancel
        views.CancelUserReservationView.as_view(),
        name="reservation_cancel",
    ),
    # New Reservations
    path(
        "request/<int:service_id>/",
        views_reservation.reservation_request,
        name="reservation_request",
    ),
    path(
        "client-info/<int:reservation_request_id>/<str:id_request>/",  # request/.../client-info/
        views_reservation.reservation_client_information,
        name="reservation_client_information",
    ),
    # Ajax for New Reservations
    path(
        "available_slots/",  # ajax/...
        api.get_available_slots,
        name="get_available_slots",
    ),
    path(
        "request_next_available_slot/<int:service_id>/",
        api.get_next_available_date,
        name="get_next_available_date",
    ),
    path(
        "request_staff_info/",
        api.get_non_working_days,
        name="get_non_working_days",
    ),
    # WorkDay Management URLs
    path(
        "workdays/", views.WorkDayListView.as_view(), name="workday_list"
    ),  # workdays/
    path(
        "workdays/add/", views.WorkDayCreateView.as_view(), name="workday_create"
    ),  # workdays/create
    path(
        "workdays/<int:pk>/update/",  # edit
        views.WorkDayUpdateView.as_view(),
        name="workday_update",
    ),
    path(
        "workdays/<int:pk>/delete/",  # delete
        views.WorkDayDeleteView.as_view(),
        name="workday_delete",
    ),
    # API endpoints for FullCalendar
    path("api/workdays/", api.workday_api, name="workday_api"),  # api/calendar/workdays
    path(
        "workdays/<int:pk>/update-date/",
        api.update_workday_date,
        name="update_workday_date",
    ),
    path(
        "api/reservations/", api.reservations_api, name="reservations_api"
    ),  # api/calendar/reservations
    # Reservation Management URLs
    path(
        "manage-reservations/",  #
        views.ManageReservationsListView.as_view(),
        name="manage_reservations_list",
    ),
    path(
        "manage-reservations/add",  # manage-reservations/create
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
    path(
        "reservations/cancel/<str:token>/",
        views.CancelReservationByUserView.as_view(),
        name="cancel_reservation",
    ),
]
