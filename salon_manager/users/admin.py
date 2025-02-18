from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Employee, Profile


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "email",
        "username",
        "phone_number",
        "is_customer",
        "is_employee",
        "is_staff",
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional info:",
            {"fields": ("phone_number", "is_customer", "is_employee")},
        ),
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "work_start", "work_end")
    search_fields = ("user__username", "user__email")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "image")


admin.site.register(CustomUser, CustomUserAdmin)
