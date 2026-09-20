from django.urls import path
from . import efficiency_views as views

app_name = "efficiency"

urlpatterns = [
    path("", views.index, name="index"),
    path("metrics/new", views.add_metric, name="add_metric"),
]
