from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Employee, Profile


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "email",
        "username",
        "phone_number",
        "role",
        "is_staff",
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional info:",
            {"fields": ("phone_number", "role")},
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "image")


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Employee)
