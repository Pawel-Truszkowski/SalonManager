from django.urls import path

from . import views

urlpatterns = [
    path("", views.ServiceListView.as_view(), name="services_list"),
    # Services Management URLs
    path(
        "manage-services/",
        views.ManageServicesListView.as_view(),
        name="manage_services_list",
    ),
    path(
        "manage-services/add/", views.ServiceCreateView.as_view(), name="service_create"
    ),
    path(
        "manage-services/<int:pk>/edit/",
        views.ServiceUpdateView.as_view(),
        name="service_update",
    ),
    path(
        "manage-services/<int:pk>/delete/",
        views.ServiceDeleteView.as_view(),
        name="service_delete",
    ),
]
