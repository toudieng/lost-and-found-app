from django.urls import path

from backend.objets import views


urlpatterns = [
   path('', views.liste_objets, name='liste_objets')

]
