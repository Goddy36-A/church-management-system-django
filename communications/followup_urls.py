from django.urls import path
from . import views

app_name = "followups"

urlpatterns = [
    path("", views.followups_index, name="index"),
    path("new", views.followups_create, name="create"),
    path("<int:followup_id>/update", views.followups_update_status, name="update_status"),
]
