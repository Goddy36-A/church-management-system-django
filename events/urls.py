from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.index, name="index"),
    path("new", views.create, name="create"),
    path("<int:event_id>", views.view, name="view"),
    path("<int:event_id>/register", views.register, name="register"),
    path("<int:event_id>/attendance", views.attendance, name="attendance"),
    path("<int:event_id>/archive", views.archive, name="archive"),
]
