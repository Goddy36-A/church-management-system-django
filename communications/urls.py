from django.urls import path
from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.announcements_index, name="index"),
    path("new", views.announcements_create, name="create"),
    path("<int:announcement_id>/archive", views.announcements_archive, name="archive"),
]
