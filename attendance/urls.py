from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.index, name="index"),
    path("new", views.create_session, name="create_session"),
    path("analytics", views.analytics, name="analytics"),
    path("<int:session_id>/record", views.record, name="record"),
    path("<int:session_id>", views.view_session, name="view_session"),
]
