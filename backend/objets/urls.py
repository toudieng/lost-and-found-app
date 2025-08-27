from django.urls import path
from .import views

urlpatterns = [
    path("declarer/", views.declarer_objet, name="declarer_objet"),
]
