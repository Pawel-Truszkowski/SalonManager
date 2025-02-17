from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("offer/", views.offer, name="offer"),
    path("services/", views.services, name="services"),
    path("about/", views.about, name="about"),
    path("booking/", views.booking, name="booking"),
    path("contact/", views.contact, name="contact"),
]
