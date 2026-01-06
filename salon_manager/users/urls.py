from django.urls import path
from users import views as user_views

urlpatterns = [
    path("register/", user_views.RegisterView.as_view(), name="register"),
    path("profile/", user_views.ProfileView.as_view(), name="profile"),
    # Employee Management
    path("employees/", user_views.EmployeeListView.as_view(), name="employee_list"),
    path(
        "employees/create/",
        user_views.EmployeeCreateView.as_view(),
        name="employee_create",
    ),
    path(
        "employees/<int:pk>/edit/",
        user_views.EmployeeUpdateView.as_view(),
        name="employee_update",
    ),
    path(
        "employees/<int:pk>/delete/",
        user_views.EmployeeDeleteView.as_view(),
        name="employee_delete",
    ),
]
