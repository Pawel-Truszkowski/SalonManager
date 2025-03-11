from django.urls import path

from .views import FORMS, ReservationWizard, reservation_success

urlpatterns = [
    path("book/", ReservationWizard.as_view(FORMS), name="reservation_wizard"),
    path("booking-success/", reservation_success, name="reservation_success"),
]
