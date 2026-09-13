from django.urls import path
from . import views

app_name = "contributions"

urlpatterns = [
    path("", views.index, name="index"),
    path("new", views.create, name="create"),
    path("categories", views.categories, name="categories"),
    path("reports", views.reports, name="reports"),
]
