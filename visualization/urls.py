from django.urls import path
from . import views

urlpatterns = [
    path("visualization/", views.index, name = "index"),
]