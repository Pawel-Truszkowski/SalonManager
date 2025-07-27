from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "OWNER"

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().handle_no_permission()
