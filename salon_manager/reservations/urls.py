from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.reservation, name="reservation_create"),
]
