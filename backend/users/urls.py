from django.urls import path
from . import views

urlpatterns = [
    # -------------------- Authentification --------------------
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # -------------------- Dashboards --------------------
    path('dashboard/admin/', views.admin_dashboard, name='dashboard_admin'),
    path('dashboard/citoyen/', views.dashboard_citoyen, name='dashboard_citoyen'),
    path('dashboard/policier/', views.dashboard_policier, name='dashboard_policier'),

    # -------------------- Profils Administrateur --------------------
    path('dashboard/admin/profil/', views.profil_admin, name='profil_admin'),
    path('dashboard/admin/profil/modifier/', views.modifier_profil_admin, name='modifier_profil_admin'),

    # -------------------- Profils Policier --------------------
    path('dashboard/policier/profil/', views.profil_police, name='profil_police'),
    path('dashboard/policier/profil/modifier/', views.modifier_profil_police, name='modifier_profil_police'),

    # -------------------- Profils Citoyen --------------------
    path('dashboard/citoyen/profil/', views.profil_citoyen, name='profil_citoyen'),
    path('dashboard/citoyen/profil/modifier/', views.modifier_profil_citoyen, name='modifier_profil_citoyen'),

    # -------------------- Notifications --------------------
    path('notification/create/', views.some_view, name='create_notification'),
]
