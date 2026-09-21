from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.index, name="index"),
    path("users", views.users, name="users"),
    path("users/new", views.create_user, name="create_user"),
    path("users/<int:user_id>/toggle-active", views.toggle_active, name="toggle_active"),
    path("users/<int:user_id>/reset-password", views.reset_password, name="reset_password"),
    path("audit-logs", views.audit_logs, name="audit_logs"),
    path("settings", views.settings_view, name="settings"),
]
