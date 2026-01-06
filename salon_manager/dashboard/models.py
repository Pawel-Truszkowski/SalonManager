from django.db import models


class Contact(models.Model):
    first_name = models.CharField(
        max_length=100,
        help_text="Enter the contact's first name (max 100 characters).",
    )
    last_name = models.CharField(
        max_length=100,
        help_text="Enter the contact's last name (max 100 characters).",
    )
    email = models.EmailField(
        help_text="Enter a valid email address where we can reply."
    )
    subject = models.CharField(
        max_length=255,
        help_text="Brief subject of the message (what is it about?).",
    )
    message = models.TextField(
        help_text="Detailed message or inquiry. Be as specific as possible."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was created.",
    )

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} - {self.subject}"
