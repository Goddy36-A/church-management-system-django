from django.urls import path
from . import research_views as views

app_name = "research"

urlpatterns = [
    path("", views.index, name="index"),
    path("questions/new", views.add_question, name="add_question"),
    path("respond", views.respond, name="respond"),
]
