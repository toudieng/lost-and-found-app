from django.urls import path
from backend.objets.views import declarer_objet
from . import views

urlpatterns = [
    # --- Public ---
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("objets/perdus/", views.objets_perdus, name="objets_perdus"),
    path("objets/trouves/", views.objets_trouves, name="objets_trouves"),
    path("objets/<int:pk>/", views.objet_detail, name="objet_detail"),
    path("declarer/", declarer_objet, name="declarer_objet"),
    path('je-le-trouve/<int:declaration_id>/', views.je_le_trouve, name='je_le_trouve'),
    path('ca-m-appartient/<int:declaration_id>/', views.ca_m_appartient, name='ca_m_appartient'),
    # --- Policier ---
    path("dashboard/policier/", views.dashboard_policier, name="dashboard_policier"),
    path("dashboard/policier/objets/", views.liste_objets_declares, name="liste_objets_declares"),
    path("dashboard/policier/objets/<int:pk>/maj/", views.maj_objet, name="maj_objet"),
    path("dashboard/policier/restitutions/", views.historique_restitutions, name="historique_restitutions"),
    path("dashboard/policier/planifier/", views.planifier_restitution, name="planifier_restitution"),
    path('objets/supprimer/<int:objet_id>/', views.supprimer_objet, name='supprimer_objet'),
    path('objets/reclames/', views.objets_reclames, name='objets_reclames'),
    path('objets/restitution/<int:declaration_id>/', views.programmer_restitution, name='programmer_restitution'),
    # --- Administrateur ---
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/admin/commissariats/", views.gerer_commissariats, name="gerer_commissariats"),
    path("dashboard/admin/utilisateurs/", views.gerer_utilisateurs, name="gerer_utilisateurs"),
    path("dashboard/admin/stats/", views.voir_stats, name="voir_stats"),
     path('dashboard/admin/commissariats/ajouter_commissariat/', views.ajouter_commissariat, name='ajouter_commissariat'),
     path("creer_policier/", views.creer_policier, name="creer_policier"),
]
