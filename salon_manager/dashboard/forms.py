from django import forms
from reservations.models import WorkDay
from users.models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["name", "services"]


class WorkDayForm(forms.ModelForm):
    class Meta:
        model = WorkDay
        fields = ["date", "employee", "start_time", "end_time"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "employee": forms.Select(attrs={"class": "form-control"}),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
        }
