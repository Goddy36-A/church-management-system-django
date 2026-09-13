from django.urls import path
from . import structure_views as views

app_name = "structure"

urlpatterns = [
    path("ministries", views.ministries_index, name="ministries_index"),
    path("ministries/new", views.ministry_create, name="ministry_create"),
    path("ministries/<int:ministry_id>", views.ministry_view, name="ministry_view"),
    path("ministries/<int:ministry_id>/archive", views.ministry_archive, name="ministry_archive"),

    path("departments", views.departments_index, name="departments_index"),
    path("departments/new", views.department_create, name="department_create"),
    path("departments/<int:department_id>", views.department_view, name="department_view"),

    path("groups", views.groups_index, name="groups_index"),
    path("groups/new", views.group_create, name="group_create"),
    path("groups/<int:group_id>", views.group_view, name="group_view"),
    path("groups/<int:group_id>/add-member", views.group_add_member, name="group_add_member"),
    path("groups/<int:group_id>/remove-member/<int:member_id>", views.group_remove_member, name="group_remove_member"),
]
