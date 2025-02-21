from django.shortcuts import render


# Create your views here.
def home(request):
    return render(request, "dashboard/index.html")


def offer(request):
    return render(request, "dashboard/offer.html")


def services(request):
    return render(request, "dashboard/services.html")


def about(request):
    return render(request, "dashboard/about.html")


def booking(request):
    return render(request, "dashboard/booking.html")


def contact(request):
    return render(request, "dashboard/contact.html")
