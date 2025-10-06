from django.urls import include, path
from backend.objets.views import declarer_objet
from . import views

urlpatterns = [
    # --- Public ---
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    #

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
     path("marquer/<int:restitution_id>/", views.marquer_restitue, name="marquer_restitue"),
     path('restitution/<int:pk>/annuler/', views.annuler_restitution, name='annuler_restitution'),
     path('dashboard/admin/policiers/', views.gerer_policiers, name='gerer_policiers'),
    path('dashboard/admin/policier/creer/', views.creer_policier, name='creer_policier'),
    path('dashboard/admin/policier/modifier/<int:pk>/', views.modifier_policier, name='modifier_policier'),
    path('dashboard/admin/policier/supprimer/<int:pk>/', views.supprimer_policier, name='supprimer_policier'),
    path(
    "dashboard/policier/planifier/<int:objet_id>/<str:type_objet>/",
    views.planifier_restitution,
    name="planifier_restitution"
),
# Objets retrouvés en attente de restitution
    path('objets/retrouves-attente/', views.objets_trouves_attente, name='objets_trouves_attente'),

 path("supprimer/<int:restitution_id>/", views.supprimer_restitution, name="supprimer_restitution"),

    path('objets/supprimer/<int:objet_id>/', views.supprimer_objet, name='supprimer_objet'),
    path("objets/reclames/", views.objets_reclames, name="objets_reclames"),
    path("dashboard/policier/objets/restitues/", views.objets_restitues, name="objets_restitues"),



    # --- Administrateur ---
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/admin/commissariats/", views.gerer_commissariats, name="gerer_commissariats"),
    path("dashboard/admin/utilisateurs/", views.gerer_utilisateurs, name="gerer_utilisateurs"),
    path("dashboard/admin/stats/", views.voir_stats, name="voir_stats"),
     path('dashboard/admin/commissariats/ajouter_commissariat/', views.ajouter_commissariat, name='ajouter_commissariat'),
     path("creer_policier/", views.creer_policier, name="creer_policier"),
      path('admin/creer/', views.creer_administrateur, name='creer_admin'),
    path('dashboard/admin/utilisateurs/creer_administrateur/', 
         views.creer_administrateur, 
         name='creer_administrateur'),
        
    path('citoyens/', views.liste_citoyens, name='liste_citoyens'),
    path('bannir/citoyens/<int:pk>/bannir/', views.bannir_citoyen, name='bannir_citoyen'),
    path('debannir/citoyens/<int:pk>/debannir/', views.debannir_citoyen, name='debannir_citoyen'),
 path('dashboard/admin/utilisateur/modifier/<int:pk>/', 
         views.modifier_administrateur, 
         name='modifier_administrateur'),

    path('dashboard/admin/utilisateur/supprimer/<int:pk>/',
         views.supprimer_administrateur,
         name='supprimer_administrateur'),



        
    # Dashboard principal
    path('dashboard/citoyen/', views.dashboard_citoyen, name='dashboard_citoyen'),

    # Objets perdus par le citoyen
    path('mes-objets-perdus/', views.mes_objets_perdus, name='mes_objets_perdus'),
    
    path('objets_perdus/modifier/<int:declaration_id>/', views.modifier_declaration, name='modifier_declaration'),
    path('objets_perdus/supprimer/<int:declaration_id>/', views.supprimer_declaration, name='supprimer_declaration'),



    # Objets trouvés par le citoyen
    path('mes-objets-trouves/', views.mes_objets_trouves, name='mes_objets_trouves'),
    path('objet-trouve/<int:objet_id>/modifier/', views.modifier_objet_trouve, name='modifier_objet_trouve'),
    path('objet-trouve/<int:objet_id>/supprimer/', views.supprimer_objet_trouve, name='supprimer_objet_trouve'),

    # Objets à réclamer (restitués ou en attente)
    path('objets-a-reclamer/', views.objets_a_reclamer, name='objets_a_reclamer'),
    

    # Planifier restitution pour un objet
    path('reclamer/<int:restitution_id>/', views.reclamer_objet, name='reclamer_objet'),
    path('historique-objets/', views.historique_objets_restitues, name='historique_objets_restitues'),
]


