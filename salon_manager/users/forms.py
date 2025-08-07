from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import SplitPhoneNumberField
from phonenumber_field.modelfields import PhoneNumberField

from .models import CustomUser, Employee, Profile

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    phone_number = SplitPhoneNumberField(required=True, region="PL")

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image"]


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["user", "name", "services"]
