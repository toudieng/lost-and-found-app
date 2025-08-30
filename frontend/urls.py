from django.urls import path
from backend.objets.views import declarer_objet
from . import views

urlpatterns = [
    # --- Public ---
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("objets/", views.liste_objets, name="liste_objets"),
    path("objets/<int:pk>/", views.objet_detail, name="objet_detail"),
    path("declarer/", declarer_objet, name="declarer_objet"),

    # --- Policier ---
    path("dashboard/policier/", views.dashboard_policier, name="dashboard_policier"),
    path("dashboard/policier/objets/", views.liste_objets_declares, name="liste_objets_declares"),
    path("dashboard/policier/objets/<int:pk>/maj/", views.maj_objet, name="maj_objet"),
    path("dashboard/policier/restitutions/", views.historique_restitutions, name="historique_restitutions"),
    path("dashboard/policier/planifier/", views.planifier_restitution, name="planifier_restitution"),
    path('objets/supprimer/<int:objet_id>/', views.supprimer_objet, name='supprimer_objet'),
    # --- Administrateur ---
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/admin/commissariats/", views.gerer_commissariats, name="gerer_commissariats"),
    path("dashboard/admin/utilisateurs/", views.gerer_utilisateurs, name="gerer_utilisateurs"),
    path("dashboard/admin/stats/", views.voir_stats, name="voir_stats"),
     path('dashboard/admin/commissariats/ajouter_commissariat/', views.ajouter_commissariat, name='ajouter_commissariat'),
]
