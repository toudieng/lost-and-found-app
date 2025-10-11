from django.urls import path, include
from backend.objets.views import declarer_objet
from . import views

urlpatterns = [
    # --- Pages publiques ---
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),

    # --- Objets généraux ---
    path("objets/perdus/", views.objets_perdus, name="objets_perdus"),
    path("objets/trouves/", views.objets_trouves, name="objets_trouves"),
    path("objets/<int:pk>/", views.objet_detail, name="objet_detail"),
    path("declarer/", declarer_objet, name="declarer_objet"),
    path("je-le-trouve/<int:declaration_id>/", views.je_le_trouve, name="je_le_trouve"),
    path("ca-m-appartient/<int:declaration_id>/", views.ca_m_appartient, name="ca_m_appartient"),

    # --- Citoyen ---
    path("dashboard/citoyen/", views.dashboard_citoyen, name="dashboard_citoyen"),

    # Objets perdus (citoyen)
    path("mes-objets-perdus/", views.mes_objets_perdus, name="mes_objets_perdus"),
    path("objets_perdus/modifier/<int:declaration_id>/", views.modifier_declaration, name="modifier_declaration"),
    path("objets_perdus/supprimer/<int:declaration_id>/", views.supprimer_declaration, name="supprimer_declaration"),

    # Objets trouvés (citoyen)
    path("mes-objets-trouves/", views.mes_objets_trouves, name="mes_objets_trouves"),
    path("objet-trouve/<int:objet_id>/modifier/", views.modifier_objet_trouve, name="modifier_objet_trouve"),
    path("objet-trouve/<int:objet_id>/supprimer/", views.supprimer_objet_trouve, name="supprimer_objet_trouve"),

    # Historique et réclamations
    path("reclamer/<int:restitution_id>/", views.reclamer_objet, name="reclamer_objet"),
    path("historique-objets/", views.historique_objets_restitues, name="historique_objets_restitues"),

    # --- Policier ---
    path("dashboard/policier/", views.dashboard_policier, name="dashboard_policier"),
    path("dashboard/policier/objets/", views.liste_objets_declares, name="liste_objets_declares"),
    path("dashboard/policier/objets/<int:pk>/maj/", views.maj_objet, name="maj_objet"),
    path("dashboard/policier/objets/restitues/", views.objets_restitues, name="objets_restitues"),
    path("dashboard/policier/restitutions/", views.historique_restitutions, name="historique_restitutions"),
    path("dashboard/policier/planifier/<int:objet_id>/<str:type_objet>/", views.planifier_restitution, name="planifier_restitution"),
    path("marquer/<int:restitution_id>/", views.marquer_restitue, name="marquer_restitue"),
    path("restitution/<int:pk>/annuler/", views.annuler_restitution, name="annuler_restitution"),
    path("supprimer/<int:restitution_id>/", views.supprimer_restitution, name="supprimer_restitution"),

    # Objets retrouvés en attente
    path("objets/retrouves-attente/", views.objets_trouves_attente, name="objets_trouves_attente"),
    path("objets/supprimer/<int:objet_id>/", views.supprimer_objet, name="supprimer_objet"),
    path("objets/reclames/", views.objets_reclames, name="objets_reclames"),

    # --- Administrateur ---
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),

    # Gestion commissariats
    path("dashboard/admin/commissariats/", views.gerer_commissariats, name="gerer_commissariats"),
    path("dashboard/admin/commissariats/ajouter_commissariat/", views.ajouter_commissariat, name="ajouter_commissariat"),

    # Gestion utilisateurs (admins et citoyens)
    path("dashboard/admin/utilisateurs/", views.gerer_utilisateurs, name="gerer_utilisateurs"),
    path("dashboard/admin/utilisateurs/creer_administrateur/", views.creer_administrateur, name="creer_administrateur"),
    path("dashboard/admin/utilisateur/modifier/<int:pk>/", views.modifier_administrateur, name="modifier_administrateur"),
    path("dashboard/admin/utilisateur/supprimer/<int:pk>/", views.supprimer_administrateur, name="supprimer_administrateur"),

    # Gestion citoyens
    path("citoyens/", views.liste_citoyens, name="liste_citoyens"),
    path("bannir/citoyens/<int:pk>/bannir/", views.bannir_citoyen, name="bannir_citoyen"),
    path("debannir/citoyens/<int:pk>/debannir/", views.debannir_citoyen, name="debannir_citoyen"),

    # Gestion policiers
    path("dashboard/admin/policiers/", views.gerer_policiers, name="gerer_policiers"),
    path("dashboard/admin/policier/creer/", views.creer_policier, name="creer_policier"),
    path("dashboard/admin/policier/modifier/<int:pk>/", views.modifier_policier, name="modifier_policier"),
    path("dashboard/admin/policier/supprimer/<int:pk>/", views.supprimer_policier, name="supprimer_policier"),
     path('preuve-restitution/<int:pk>/', views.preuve_restitution_pdf, name='preuve_restitution_pdf'),

    # Statistiques
    path("dashboard/admin/stats/", views.voir_stats, name="voir_stats"),
]
