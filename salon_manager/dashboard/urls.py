from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    # Employee URLs
    path("employees/", views.EmployeeListView.as_view(), name="employee_list"),
    path("employees/add/", views.EmployeeCreateView.as_view(), name="employee_create"),
    path(
        "employees/<int:pk>/edit/",
        views.EmployeeUpdateView.as_view(),
        name="employee_update",
    ),
    path(
        "employees/<int:pk>/delete/",
        views.EmployeeDeleteView.as_view(),
        name="employee_delete",
    ),
    # WorkDay URLs
    path("workdays/", views.WorkDayListView.as_view(), name="workday_list"),
    path("workdays/add/", views.WorkDayCreateView.as_view(), name="workday_create"),
    path(
        "workdays/<int:pk>/update/",
        views.WorkDayUpdateView.as_view(),
        name="workday_update",
    ),
    path(
        "workdays/<int:pk>/delete/",
        views.WorkDayDeleteView.as_view(),
        name="workday_delete",
    ),
    # API endpoints for FullCalendar
    path("api/workdays/", views.workday_api, name="workday_api"),
    path(
        "workdays/<int:pk>/update-date/",
        views.update_workday_date,
        name="update_workday_date",
    ),
]
