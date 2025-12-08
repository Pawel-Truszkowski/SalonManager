from django.contrib import admin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "subject", "created_at")
    search_fields = ("first_name", "last_name", "email", "subject")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
