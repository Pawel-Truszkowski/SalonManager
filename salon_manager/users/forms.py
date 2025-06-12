from django import forms
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.modelfields import PhoneNumberField

from .models import CustomUser, Employee, Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    phone_number = PhoneNumberField(blank=True)

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password1",
            "password2",
        ]


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = "__all__"


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image"]


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["name", "services"]
