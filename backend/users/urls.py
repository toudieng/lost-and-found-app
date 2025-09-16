from django.urls import path
from . import views

urlpatterns = [
    #les urls des authentifications des users
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path("profil/", views.profil_admin, name="profil_admin"),
    path("profil/modifier/", views.modifier_profil_admin, name="modifier_profil_admin"),
]

