from django.shortcuts import render


# Create your views here.
def home(request):
    return render(request, "dashboard/index.html")


def offer(request):
    return render(request, "dashboard/offer.html")


def about(request):
    return render(request, "dashboard/about.html")


def contact(request):
    return render(request, "dashboard/contact.html")
