from django.contrib import admin

from .models import CustomUser, Employee, Profile

admin.site.register(CustomUser)
admin.site.register(Employee)
admin.site.register(Profile)
