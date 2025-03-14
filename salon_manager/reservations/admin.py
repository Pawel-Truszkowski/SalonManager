from django.contrib import admin

from .models import Reservation, WorkDay

admin.site.register((Reservation, WorkDay))
