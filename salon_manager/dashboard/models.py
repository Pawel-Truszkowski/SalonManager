from django.db import models


class Contact(models.Model):
    first_name = models.CharField(
        max_length=100
    )  # TODO dodanie helptext jak są potrzebne
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} - {self.subject}"
