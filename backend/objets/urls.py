from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_objets, name='liste_objets'),
]
