from django.urls import path
from reservations.views import (  # TODO importy konkretne
    api,
    manage_reservations_views,
    manage_workday_views,
    reservation_views,
    user_reservations_views,
)

# TODO app_name = "reservations"  # reservations:sucess
urlpatterns = [
    path(
        "reservation-success/",
        user_reservations_views.ReservationSuccessView.as_view(),
        name="reservation_success",  # success
    ),
    path(
        "your-reservations/",  # my/
        user_reservations_views.UserReservationsListView.as_view(),
        name="user_reservations_list",
    ),
    path(
        "reservation-cancel/<int:pk>/",  # reservations/cancel
        user_reservations_views.CancelUserReservationView.as_view(),
        name="reservation_cancel",
    ),
    # New Reservations
    path(
        "request/<int:service_id>/",
        reservation_views.reservation_request,
        name="reservation_request",
    ),
    path(
        "client-info/<int:reservation_request_id>/<str:id_request>/",  # request/.../client-info/
        reservation_views.reservation_client_information,
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
        "workdays/", manage_workday_views.WorkDayListView.as_view(), name="workday_list"
    ),  # workdays/
    path(
        "workdays/create/",
        manage_workday_views.WorkDayCreateView.as_view(),
        name="workday_create",
    ),  # workdays/create
    path(
        "workdays/<int:pk>/edit/",  # edit
        manage_workday_views.WorkDayUpdateView.as_view(),
        name="workday_edit",
    ),
    path(
        "workdays/<int:pk>/delete/",  # delete
        manage_workday_views.WorkDayDeleteView.as_view(),
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
        manage_reservations_views.ManageReservationsListView.as_view(),
        name="manage_reservations_list",
    ),
    path(
        "manage-reservations/add",  # manage-reservations/create
        manage_reservations_views.ReservationCreateView.as_view(),
        name="reservation_create",
    ),
    path(
        "reservations/<int:pk>/edit/",
        manage_reservations_views.ReservationUpdateView.as_view(),
        name="reservation_edit",
    ),
    path(
        "manage-reservations/<int:pk>/delete/",
        manage_reservations_views.ReservationDeleteView.as_view(),
        name="reservation_delete",
    ),
    path(
        "reservations/<int:pk>/confirm/",
        manage_reservations_views.ConfirmReservationView.as_view(),
        name="reservation_confirm",
    ),
    path(
        "reservations/cancel/<str:token>/",
        user_reservations_views.CancelReservationByUserView.as_view(),
        name="cancel_reservation",
    ),
]
