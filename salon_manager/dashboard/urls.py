from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("offer/", views.offer, name="offer"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]
