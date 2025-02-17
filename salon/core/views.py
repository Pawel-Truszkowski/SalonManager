from django.shortcuts import render


# Create your views here.
def home(request):
    return render(request, "core/index.html")


def offer(request):
    return render(request, "core/offer.html")


def services(request):
    return render(request, "core/services.html")


def about(request):
    return render(request, "core/about.html")


def booking(request):
    return render(request, "core/booking.html")


def contact(request):
    return render(request, "core/contact.html")
