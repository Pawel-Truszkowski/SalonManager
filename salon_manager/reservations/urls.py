from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.reservation, name="reservation_create"),
    path("scucess/", views.reservation_success, name="reservation_success"),
]
