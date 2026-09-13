from django.urls import path
from . import views

app_name = "members"

urlpatterns = [
    path("", views.index, name="index"),
    path("new", views.create, name="create"),
    path("archived", views.archived, name="archived"),
    path("export.csv", views.export_csv, name="export_csv"),
    path("<int:member_id>", views.view, name="view"),
    path("<int:member_id>/edit", views.edit, name="edit"),
    path("<int:member_id>/archive", views.archive, name="archive"),
    path("<int:member_id>/restore", views.restore, name="restore"),
]
