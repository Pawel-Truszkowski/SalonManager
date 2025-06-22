"""
URL configuration for salon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from users import views as user_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("services/", include("services.urls")),
    path("reservations/", include("reservations.urls")),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="users/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("register/", user_views.register, name="register"),
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="users/password_change_form.html"
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("profile/", user_views.profile, name="profile"),
    # Employee Management
    path("employees/", user_views.EmployeeListView.as_view(), name="employee_list"),
    path(
        "employees/add/",
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += debug_toolbar_urls()

urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
