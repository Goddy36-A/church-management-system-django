from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.index, name="index"),
    path("membership", views.membership, name="membership"),
    path("attendance", views.attendance, name="attendance"),
    path("administrative", views.administrative, name="administrative"),
]
