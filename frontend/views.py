# views.py (réorganisé)

from email.message import EmailMessage
from functools import wraps
import calendar
import random
import string
from venv import logger
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail, BadHeaderError
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

# Modèles & forms
from backend.objets.models import (
    Objet, Declaration, Restitution, Commissariat,
    EtatObjet, StatutRestitution
)
from backend.objets.forms import DeclarationForm, RestitutionForm
from backend.users.models import Message, Utilisateur, Notification
from backend.users.forms import (
    AdministrateurForm, CommissariatForm, ContactForm, PolicierForm,
    AdministrateurCreationForm, UtilisateurCreationForm
)
from frontend import models


# =============================
#       DÉCORATEURS RÔLES
# =============================
def policier_required(view_func):
    """Accès réservé aux policiers."""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if not (hasattr(request.user, "role") and request.user.role == "policier"):
            messages.error(request, "⚠️ Accès réservé aux policiers.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Accès réservé aux administrateurs."""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if not (hasattr(request.user, "role") and request.user.role == "admin"):
            messages.error(request, "⛔ Accès réservé aux administrateurs.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


# =============================
#       PAGES PUBLIQUES
# =============================




def home(request):
    # 🔹 Objets avec statut PERDU ou RECLAME
    objets_perdus_reclames = Objet.objects.filter(etat__in=[EtatObjet.PERDU, EtatObjet.RECLAME]).order_by('-id')[:6]

    # 🔹 Objets trouvés récents
    objets_trouves = Objet.objects.filter(etat=EtatObjet.TROUVE).order_by('-id')[:6]

    # 🔸 Construction des slides dynamiques pour les objets perdus/reclamés
    slides_perdus_reclames = [
        {
            'url': obj.image.url if obj.image else None,
            'titre': obj.nom,
            'description': (obj.description[:120] + "...") if obj.description else "",
            'etat': obj.get_etat_display(),
            'etat_type': 'perdu' if obj.etat == EtatObjet.PERDU else 'reclame'
        }
        for obj in objets_perdus_reclames
    ]

    # 🔸 Construction des slides dynamiques pour les objets trouvés
    slides_trouves = [
        {
            'url': obj.image.url if obj.image else None,
            'titre': obj.nom,
            'description': (obj.description[:120] + "...") if obj.description else "",
            'etat': obj.get_etat_display(),
            'etat_type': 'trouve'
        }
        for obj in objets_trouves
    ]

    # 🔹 Fusionner les listes pour le carrousel
    all_slides = slides_perdus_reclames + slides_trouves

    # 🔹 Slides par défaut si aucun objet réel
    default_slides = [
        {'url': '/static/frontend/images/head2.jpg', 'titre': 'Aucun objet', 'description': 'Slide par défaut', 'etat_type': 'default'},
        {'url': '/static/frontend/images/head1.jpg', 'titre': 'Aucun objet', 'description': 'Slide par défaut', 'etat_type': 'default'},
        {'url': '/static/frontend/images/head3.jpg', 'titre': 'Aucun objet', 'description': 'Slide par défaut', 'etat_type': 'default'},
    ]

    # 🔹 Si pas de slide réel, utiliser les slides par défaut
    if not all_slides:
        all_slides = default_slides

    # 🔹 Timeline restitution par la police
    steps = [
        {'icon': 'bi bi-clipboard-check', 'title': '⿡ Vérification de la déclaration', 'desc': "Le policier consulte la fiche de l’objet et valide l’identité du déclarant."},
        {'icon': 'bi bi-person-badge', 'title': '⿢ Identification du propriétaire', 'desc': "Une vérification d’identité est effectuée à l’aide d’une pièce officielle."},
        {'icon': 'bi bi-box-seam', 'title': '⿣ Restitution de l’objet', 'desc': "Le policier remet l’objet au propriétaire et enregistre la restitution."},
        {'icon': 'bi bi-file-earmark-text', 'title': '⿤ Génération d’une preuve', 'desc': "Une attestation PDF est générée et remise au citoyen comme preuve."},
    ]

    context = {
        'all_slides': all_slides,
        'steps': steps,
    }

    return render(request, "frontend/home.html", context)






# =========================
# 📩 Formulaire contact citoyen
# =========================
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            if request.user.is_authenticated:
                message.expediteur = request.user
            message.save()

            # Crée une notification pour l’admin
            admin = Utilisateur.objects.filter(role='admin').first()
            if admin:
                Notification.objects.create(
                    user=admin,
                    message=f"Nouveau message de {message.nom} ({message.email})"
                )

            messages.success(request, "✅ Votre message a bien été envoyé. Merci de nous avoir contactés.")
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'frontend/contact.html', {'form': form})


# =========================
# 📬 Liste des messages pour l’admin
# =========================
def liste_messages(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    messages_citoyens = Message.objects.all()
    return render(request, 'frontend/admin/liste_messages.html', {'messages_citoyens': messages_citoyens})

# =========================
# ✉️ Répondre à un message
# =========================
def repondre_message(request, message_id):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    message_obj = get_object_or_404(Message, id=message_id)

    if request.method == 'POST':
        reponse = request.POST.get('reponse')
        message_obj.reponse = reponse
        message_obj.date_reponse = timezone.now()
        message_obj.traite = True
        message_obj.save()

        # Envoi de l’email au citoyen
        send_mail(
            subject=f"Réponse à votre message - Plateforme Objets Perdus",
            message=f"Bonjour {message_obj.nom},\n\nVoici la réponse de l'administrateur :\n\n{reponse}\n\nMerci pour votre message.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[message_obj.email],
            fail_silently=False,
        )

        messages.success(request, f"Réponse envoyée à {message_obj.nom}.")
        return redirect('liste_messages')

    return render(request, 'frontend/admin/repondre_message.html', {'message_obj': message_obj})




@login_required

def objets_perdus(request):
    query = request.GET.get('q', '').strip()

    declarations = (
        Declaration.objects
        .select_related('objet', 'citoyen')
        .prefetch_related('reclame_par', 'trouve_par')
        .filter(
            Q(etat_initial=EtatObjet.PERDU) & 
            Q(objet__etat__in=[EtatObjet.PERDU, EtatObjet.RECLAME])
        )
        .order_by('-date_declaration')
    )

    if query:
        declarations = declarations.filter(objet__nom__icontains=query)

    # Préparer les données pour le template
    for dec in declarations:
        dec.declarant = dec.citoyen
        dec.details_objet = dec.objet
        dec.est_reclame_par_user = request.user.is_authenticated and request.user in dec.reclame_par.all()

    return render(request, "frontend/objets/objets_perdus.html", {
        "declarations": declarations,
        "query": query,
    })

@login_required
def objets_trouves(request):
    query = request.GET.get("q", "").strip()
    
    # 🔹 Filtrage : état initial = TROUVE ET (objet trouvé ou réclamé)
    declarations = Declaration.objects.filter(
        Q(etat_initial=EtatObjet.TROUVE) &
        Q(objet__etat__in=[EtatObjet.TROUVE, EtatObjet.RECLAME])
    ).select_related('citoyen', 'objet').order_by('-date_declaration')
    
    if query:
        declarations = declarations.filter(
            Q(objet__nom__icontains=query) |
            Q(description__icontains=query) |
            Q(lieu__icontains=query)
        )
    
    context = {
        "declarations": declarations.distinct(),
        "query": query,
        "EtatObjet": EtatObjet,
    }
    
    return render(request, "frontend/objets/objets_trouves.html", context)



def objet_detail(request, pk):
    objet = get_object_or_404(Objet, pk=pk)
    return render(request, "frontend/objets/objet_detail.html", {"objet": objet})


# suppression générique d'objet (utilisé par UI/admin selon droits dans templates/URLs)
@login_required
def supprimer_objet(request, objet_id):
    objet = get_object_or_404(Objet, id=objet_id)
    if request.method == "POST":
        objet.delete()
        messages.success(request, "Objet supprimé avec succès.")
    return redirect('liste_objets_declares')


# =============================
#       DASHBOARD POLICIER
# =============================

@policier_required


def dashboard_policier(request):
    today = timezone.now()
    current_year = today.year

    # --- Labels des 6 derniers mois ---
    months_labels = []
    last_6_months = []
    for i in range(5, -1, -1):  # 5 mois avant -> 0
        month = today - relativedelta(months=i)
        months_labels.append(month.strftime("%b"))  # "Jan", "Fév", ...
        last_6_months.append((month.year, month.month))

    # --- Statistiques globales ---
    nb_objets_perdus_trouves = Declaration.objects.filter(
        etat_initial=EtatObjet.PERDU,
        objet__etat=EtatObjet.RECLAME
    ).count()

    nb_objets_trouves_reclames = Declaration.objects.filter(
        etat_initial=EtatObjet.TROUVE,
        objet__etat=EtatObjet.RECLAME
    ).count()

    nb_objets_trouves_attente = Declaration.objects.filter(
        objet__etat=EtatObjet.EN_ATTENTE
    ).count()

    nb_restitutions = Declaration.objects.filter(
        objet__etat=EtatObjet.RESTITUE
    ).count()

    stats_cards = [
        {"label": "Objets perdus & trouvés", "count": nb_objets_perdus_trouves, "icon": "📌", "url": reverse("objets_perdus_trouves")},
        {"label": "Objets trouvés & réclamés", "count": nb_objets_trouves_reclames, "icon": "📌", "url": reverse("objets_trouves_reclames")},
        {"label": "Objets retrouvés (en attente)", "count": nb_objets_trouves_attente, "icon": "📦", "url": reverse("objets_trouves_attente")},
        {"label": "Historique", "count": nb_restitutions, "icon": "📂", "url": reverse("historique_restitutions")},
    ]

    # --- Données graphiques 6 derniers mois ---
    def data_by_last_6_months(queryset):
        data = []
        for y, m in last_6_months:
            count = queryset.filter(date_declaration__year=y, date_declaration__month=m).count()
            data.append(count)
        return data

    data_perdus_trouves = data_by_last_6_months(
        Declaration.objects.filter(etat_initial=EtatObjet.PERDU, objet__etat=EtatObjet.RECLAME)
    )
    data_trouves_reclames = data_by_last_6_months(
        Declaration.objects.filter(etat_initial=EtatObjet.TROUVE, objet__etat=EtatObjet.RECLAME)
    )

    context = {
        "stats_cards": stats_cards,
        "chart_labels": months_labels,
        "chart_perdus": data_perdus_trouves,
        "chart_trouves": data_trouves_reclames,
        "current_year": current_year,
    }

    return render(request, "frontend/policier/dashboard_policier.html", context)


@policier_required
def liste_objets_declares(request):
    objets = Objet.objects.all()
    return render(request, "frontend/policier/liste_objets_declares.html", {"objets": objets})


@policier_required
def maj_objet(request, pk):
    objet = get_object_or_404(Objet, pk=pk)
    if request.method == "POST":
        objet.etat = request.POST.get("etat")
        objet.save()
        messages.success(request, "État de l'objet mis à jour ✅")
        return redirect("liste_objets_declares")
    return render(request, "frontend/policier/maj_objet.html", {"objet": objet})




def policier_ou_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['policier', 'admin']:
            return view_func(request, *args, **kwargs)
        return redirect('login')  # ou page d'erreur "accès interdit"
    return _wrapped_view



@policier_required
def supprimer_restitution(request, restitution_id):
    restitution = get_object_or_404(Restitution, id=restitution_id)
    if restitution.policier != request.user:
        messages.error(request, "Vous n’êtes pas autorisé à supprimer cette restitution.")
    else:
        restitution.delete()
        messages.success(request, "La restitution a été supprimée avec succès.")
    return redirect("historique_restitutions")


@policier_required
def objets_restitues(request):
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat'
    ).order_by('-date_restitution')
    return render(request, "frontend/objets/objets_restitues.html", {"restitutions": restitutions})




def objets_reclames(request):
    declarations = (
        Declaration.objects
        .select_related("objet", "citoyen")  # seulement FK
        .prefetch_related("reclame_par", "trouve_par")  # M2M
        .order_by("-date_declaration")
    )

    restitutions = Restitution.objects.filter(restitue_par__isnull=True)
    restit_dict = {(r.objet.id, r.citoyen.id): r for r in restitutions}

    for dec in declarations:
        # Déterminer le réclamant / trouveur principal
        if dec.etat_initial == EtatObjet.PERDU:
            dec.principal = dec.citoyen  # Réclamant
            dec.restitution_planifiee = restit_dict.get((dec.objet.id, dec.citoyen.id))
        elif dec.etat_initial == EtatObjet.TROUVE:
            dec.principal = dec.citoyen  # Déclarant / trouveur
            dec.restitution_planifiee = None

    return render(request, "frontend/objets/objets_reclames.html", {"declarations": declarations})

@login_required
@policier_ou_admin_required
def historique_restitutions(request):
    # Récupère toutes les restitutions d'objets restitués
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'restitue_par', 'commissariat'
    ).filter(
        objet__etat=EtatObjet.RESTITUE
    ).order_by('-date_restitution', '-heure_restitution')

    for r in restitutions:
        r.proprietaire = r.citoyen

        # Récupère la déclaration correspondant à l'état initial
        declaration_initiale = r.objet.declarations.order_by('date_declaration').first()
        if declaration_initiale:
            r.etat_initial = declaration_initiale.etat_initial

            # Détermine le(s) citoyen(s) qui ont trouvé l'objet
            trouveurs = set()
            if declaration_initiale.etat_initial == EtatObjet.TROUVE:
                # Si l'objet était trouvé initialement, le déclarant est le trouveur
                if declaration_initiale.citoyen:
                    trouveurs.add(declaration_initiale.citoyen)
            else:
                # Sinon, récupère tous ceux listés dans trouve_par
                for user in declaration_initiale.trouve_par.all():
                    trouveurs.add(user)
            r.trouveurs = list(trouveurs)
        else:
            r.etat_initial = 'N/A'
            r.trouveurs = []

    return render(request, "frontend/policier/historique_restitutions.html", {
        "restitutions": restitutions
    })

def objets_reclames(request):
    """
    Vue qui affiche les objets réclamés pour le policier.
    Chaque objet a au moins un réclamant et un trouveur.
    """
    # On récupère toutes les déclarations dont l'objet a été réclamé
    declarations = Declaration.objects.filter(reclame_par__isnull=False).distinct()

    # Préparer chaque déclaration pour la template
    for dec in declarations:
        # On garantit qu'il y a au moins un réclamant
        if dec.reclame_par.exists():
            dec.reclamant_principal = dec.reclame_par.first()
        else:
            dec.reclamant_principal = None  # juste au cas où

        # On garantit qu'il y a au moins un trouveur
        if dec.trouve_par.exists():
            dec.trouveur_principal = dec.trouve_par.first()
        else:
            dec.trouveur_principal = None

    return render(request, "frontend/objets/objets_reclames.html", {
        "declarations": declarations
    })
from django.shortcuts import render
from django.db.models import Q
from backend.objets.models import Declaration, EtatObjet






from django.shortcuts import render
from backend.objets.models import Declaration, EtatObjet

from django.shortcuts import render
from backend.objets.models import Declaration, EtatObjet

from django.shortcuts import render
from backend.objets.models import Declaration, EtatObjet



def objets_trouves_reclames(request):
    """
    Affiche les objets dont :
    - l'état initial est TROUVE
    - l'objet est actuellement RECLAME
    - au moins un réclamant
    """
    # 🔹 Requête avec préchargement des relations
    declarations = (
        Declaration.objects
        .filter(
            etat_initial=EtatObjet.TROUVE,
            objet__etat=EtatObjet.RECLAME
        )
        .annotate(nb_reclamants=Count('reclame_par'))
        .filter(nb_reclamants__gt=0)
        .select_related('citoyen', 'objet')  # trouveur
        .prefetch_related('reclame_par')     # réclamants
        .distinct()
    )

    # 🔹 Attributs dynamiques pour le template
    for dec in declarations:
        dec.trouveur_principal = dec.citoyen
        dec.reclamants_list = list(dec.reclame_par.all())

    # 🔹 Passage au template
    return render(request, "frontend/objets/objets_trouves_reclames.html", {
        "declarations": declarations
    })


def objets_perdus_trouves(request):
    """
    Affiche les objets perdus dont :
    - l'état initial est 'PERDU'
    - l'état actuel de l'objet est 'RECLAME'
    - le réclamant principal est le citoyen qui les a déclarés
    """

    query = request.GET.get('q', '')

    # 🔹 Récupération des déclarations
    declarations = Declaration.objects.filter(
        etat_initial=EtatObjet.PERDU,
        objet__etat=EtatObjet.RECLAME
    ).distinct()

    # 🔹 Filtrage par recherche
    if query:
        declarations = declarations.filter(
            Q(objet__nom__icontains=query) |
            Q(description__icontains=query) |
            Q(citoyen__username__icontains=query)
        )

    # 🔹 Préfetch pour optimiser l'accès aux relations
    declarations = declarations.select_related('citoyen', 'objet').prefetch_related('trouve_par', 'reclame_par')

    # 🔹 Ajouter attributs dynamiques pour le template
    for dec in declarations:
        dec.reclamant_principal = dec.citoyen  # le déclarant est le réclamant principal
        dec.trouveurs_list = list(dec.trouve_par.all())  # tous les trouveurs associés

    context = {
        'declarations': declarations,
        'query': query
    }

    return render(request, 'frontend/objets/objets_perdus_trouves.html', context)


@login_required
@policier_required
def objets_trouves_attente(request):
    """
    Affiche les objets trouvés planifiés pour restitution,
    dont l'état actuel est EN_ATTENTE.
    """

    restitutions = (
        Restitution.objects
        .select_related('objet', 'citoyen', 'commissariat')
        .prefetch_related(
            Prefetch(
                'objet__declarations',
                queryset=Declaration.objects.prefetch_related('trouve_par', 'reclame_par'),
                to_attr='declarations_prefetch'
            )
        )
        .filter(
            statut=StatutRestitution.PLANIFIEE,
            objet__etat=EtatObjet.EN_ATTENTE
        )
    )

    return render(request, "frontend/objets/objets_trouves_attente.html", {
        "restitutions": restitutions
    })




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from backend.objets.models import Declaration, Restitution, EtatObjet, StatutRestitution
from backend.users.models import Commissariat

def planifier_restitution(request, objet_id, type_objet="declaration"):
    """
    Planifie la restitution d’un objet et notifie le réclamant et le trouveur.
    Ne fonctionne que pour les objets ayant une déclaration.
    """
    # 🔹 Récupération de la déclaration
    declaration = get_object_or_404(Declaration, id=objet_id)

    if not declaration.objet:
        messages.error(request, "Cet objet n'est pas lié à une déclaration valide.")
        return redirect("objets_trouves_attente")

    # 🔹 Vérification de l'état initial
    if declaration.etat_initial not in [EtatObjet.PERDU, EtatObjet.TROUVE]:
        messages.error(request, "L'état initial de la déclaration est invalide.")
        return redirect("objets_trouves_attente")

    # 🔹 Options pour le formulaire
    trouveurs_options = declaration.trouve_par.all() or []
    reclamants_options = declaration.reclame_par.all() or []
    commissariats = Commissariat.objects.all()

    if request.method == "POST":
        # 🔹 Récupérer date, heure et commissariat
        date_restitution = request.POST.get('date_restitution')
        heure_restitution = request.POST.get('heure_restitution')
        commissariat_id = request.POST.get('commissariat')

        if not (date_restitution and heure_restitution and commissariat_id):
            messages.error(request, "Veuillez remplir la date, l'heure et le commissariat.")
            return redirect(request.path)

        # 🔹 Déterminer qui est le trouveur et le réclamant
        if declaration.etat_initial == EtatObjet.PERDU:
            trouveur_id = request.POST.get('trouveur')
            reclamant_id = declaration.citoyen.id
        else:  # Etat initial TROUVE
            trouveur_id = declaration.citoyen.id
            reclamant_id = request.POST.get('reclamant')

        if not (trouveur_id and reclamant_id):
            messages.error(request, "Veuillez sélectionner le trouveur et le réclamant.")
            return redirect(request.path)

        # 🔹 Récupérer le commissariat
        commissariat = get_object_or_404(Commissariat, id=commissariat_id)

        # 🔹 Création ou récupération de la restitution
        restitution, created = Restitution.objects.get_or_create(
            objet=declaration.objet,
            citoyen_id=reclamant_id,
            defaults={
                "policier": request.user,
                "commissariat": commissariat,
                "date_restitution": date_restitution,
                "heure_restitution": heure_restitution,
                "statut": StatutRestitution.PLANIFIEE,
            },
        )

        # 🔹 Mettre l'objet en attente uniquement si il est actuellement RECLAME
        if declaration.objet.etat == EtatObjet.RECLAME:
            declaration.objet.etat = EtatObjet.EN_ATTENTE
            declaration.objet.save()

        # 🔹 Préparer les destinataires pour notification
        recipients = []
        trouveur = declaration.trouve_par.filter(id=trouveur_id).first()
        reclamant = declaration.citoyen if declaration.etat_initial == EtatObjet.PERDU else \
                    declaration.reclame_par.filter(id=reclamant_id).first()

        if trouveur and trouveur.email:
            recipients.append(trouveur.email)
        if reclamant and reclamant.email:
            recipients.append(reclamant.email)

        recipients = list(set(recipients))  # Supprimer les doublons

        # 🔹 Envoyer le mail de notification
        if recipients:
            try:
                send_mail(
                    subject=f"[Restitution planifiée] {declaration.objet.nom}",
                    message=f"""
Bonjour,

La restitution de l'objet '{declaration.objet.nom}' a été planifiée.

Commissariat : {commissariat.nom if commissariat else 'Non défini'}
Date : {date_restitution}
Heure : {heure_restitution}

Merci de vous présenter avec vos pièces justificatives.
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi du mail: {e}")

        messages.success(request, f"Restitution de '{declaration.objet.nom}' planifiée avec succès ✅")
        return redirect("objets_trouves_attente")

    # 🔹 Contexte pour le template
    context = {
        "declaration": declaration,
        "trouveurs_options": trouveurs_options,
        "reclamants_options": reclamants_options,
        "commissariats": commissariats,
        "today": timezone.now(),
        "now": timezone.now(),
    }
    return render(request, "frontend/policier/planifier_restitution.html", context)

def marquer_restitue(request, restitution_id):
    # 🔹 Récupérer la restitution
    restitution = get_object_or_404(
        Restitution.objects.select_related('objet', 'citoyen', 'policier'),
        id=restitution_id
    )

    # 🔹 Marquer comme effectuée
    restitution.statut = 'effectuee'
    restitution.save()  # met aussi l'objet à RESTITUE si save() est surchargé

    # 🔹 Génération du PDF
    try:
        html_string = render_to_string(
            'frontend/policier/preuve_restitution_pdf.html',
            {'restitution': restitution}
        )
        pdf_file = HTML(string=html_string).write_pdf()
    except Exception as e:
        logger.error(f"Erreur génération PDF pour restitution {restitution.id}: {e}")
        pdf_file = None

    # 🔹 Préparer les destinataires
    recipients = set()
    if restitution.citoyen and restitution.citoyen.email:
        recipients.add(restitution.citoyen.email)

    for declaration in restitution.objet.declarations.all():
        for user in declaration.trouve_par.all():
            if user.email:
                recipients.add(user.email)

    # 🔹 Envoyer le mail avec pièce jointe PDF
    if recipients:
        try:
            email_body_html = render_to_string(
                'frontend/policier/email_restitution.html',  # template HTML facultatif
                {'restitution': restitution}
            )
            email = EmailMessage(
                subject=f"Restitution de l'objet '{restitution.objet.nom}' effectuée ✅",
                body=f"Bonjour,\n\nLa restitution de l'objet '{restitution.objet.nom}' a été effectuée avec succès.\nVeuillez trouver la preuve en pièce jointe.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=list(recipients),
            )
            if pdf_file:
                email.attach(f"preuve_{restitution.objet.nom}.pdf", pdf_file, 'application/pdf')
            email.send(fail_silently=False)
            logger.info(f"Mail de restitution envoyé à {recipients}")
        except Exception as e:
            logger.error(f"Erreur envoi mail restitution {restitution.id}: {e}")

    # 🔹 Redirection vers la page des objets en attente
    return redirect('objets_trouves_attente')



@policier_required
def annuler_restitution(request, pk):
    """
    Annule une restitution et remet l'état initial basé sur la déclaration s'il existe.
    (Était précédemment sans décorateur)
    """
    restitution = get_object_or_404(Restitution, id=pk)
    objet = restitution.objet

    declaration = Declaration.objects.filter(objet=objet).first()

    if declaration:
        # Si votre modèle Declaration a un champ 'etat_initial', utilisez-le.
        # Ici on remet l'état à la valeur indiquée dans la déclaration si présente,
        # sinon on met PERDU (comportement conservateur).
        if hasattr(declaration, 'etat_initial') and declaration.etat_initial:
            objet.etat = declaration.etat_initial
        else:
            objet.etat = EtatObjet.PERDU
        objet.save()
        restitution.delete()
        messages.success(
            request,
            f"La restitution de l'objet '{objet.nom}' a été annulée. L'état a été remis à '{objet.etat}'."
        )
    else:
        messages.error(request, "Impossible de déterminer l'état initial de l'objet.")

    return redirect('objets_trouves_attente')
# frontend/views.py

import base64
from io import BytesIO
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import qrcode




def preuve_restitution_pdf(request, pk):
    restitution = get_object_or_404(Restitution, pk=pk)

    # 🔹 Déclaration de l'objet trouvé (pour le trouveur)
    declaration_trouve = restitution.objet.declarations.filter(
        etat_initial=EtatObjet.TROUVE
    ).first()
    trouveur_principal = declaration_trouve.trouve_par.first() if declaration_trouve else None

    # 🔹 Déclaration de l'objet perdu (pour le réclamant)
    declaration_perdu = restitution.objet.declarations.filter(
        etat_initial=EtatObjet.PERDU
    ).first()
    reclamant_principal = declaration_perdu.reclame_par.first() if declaration_perdu else None

    # 🔹 Policier ayant planifié
    policier_planificateur = restitution.restitue_par or restitution.policier

    # 🔹 QR Code
    qr_data = f"http://ton-site.com/verifier-restitution/{restitution.id}/"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

    context = {
        'restitution': restitution,
        'reclamant_principal': reclamant_principal,
        'trouveur_principal': trouveur_principal,
        'policier_planificateur': policier_planificateur,
        'now': timezone.now(),
        'qr_code': qr_code_base64,
    }

    html_string = render_to_string('frontend/policier/preuve_restitution_pdf.html', context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="preuve_restitution_{restitution.id}.pdf"'
    return response


# =============================
#       DASHBOARD ADMIN
# =============================

@login_required(login_url='login')
def dashboard_admin(request):
    """
    Tableau de bord Administrateur :
    Affiche les statistiques globales du système ainsi que les messages citoyens récents.
    """

    # Statistiques des utilisateurs
    nb_commissariats = Commissariat.objects.count()
    nb_utilisateurs = Utilisateur.objects.filter(role='admin').count()
    nb_policiers = Utilisateur.objects.filter(role='policier').count()
    nb_citoyens = Utilisateur.objects.filter(role='citoyen').count()

    # Statistiques sur les objets
    nb_objets_perdus = Objet.objects.filter(etat=EtatObjet.PERDU).count()
    nb_objets_trouves = Objet.objects.filter(etat=EtatObjet.TROUVE).count()
    nb_objets_reclames = Objet.objects.filter(etat=EtatObjet.RECLAME).count()
    nb_objets_en_attente = Objet.objects.filter(etat=EtatObjet.EN_ATTENTE).count()
    nb_objets_restitues = Objet.objects.filter(etat=EtatObjet.RESTITUE).count()

    # Restitutions
    nb_restitutions = Restitution.objects.count()

    # Notifications récentes (5 dernières)
    notifications = Notification.objects.order_by('-date')[:5]

    # Messages citoyens récents (5 derniers)
    messages_recus = Message.objects.order_by('-date_envoi')[:5]

    # Graphique évolution (par mois ou par date d'ajout)
    # Ici on prend juste les 12 derniers objets ajoutés pour exemple
    derniers_objets = Objet.objects.order_by('-id')[:12]  # id croissant ≈ date création

    chart_labels = [f"{obj.nom}" for obj in derniers_objets]
    chart_perdus = [1 if obj.etat == EtatObjet.PERDU else 0 for obj in derniers_objets]
    chart_trouves = [1 if obj.etat == EtatObjet.TROUVE else 0 for obj in derniers_objets]

    context = {
        'nb_commissariats': nb_commissariats,
        'nb_utilisateurs': nb_utilisateurs,
        'nb_policiers': nb_policiers,
        'nb_citoyens': nb_citoyens,
        'nb_objets_perdus': nb_objets_perdus,
        'nb_objets_trouves': nb_objets_trouves,
        'nb_objets_reclames': nb_objets_reclames,
        'nb_objets_en_attente': nb_objets_en_attente,
        'nb_objets_restitues': nb_objets_restitues,
        'nb_restitutions': nb_restitutions,
        'notifications': notifications,
        'messages_recus': messages_recus,
        # Pour le graphique style policier
        'chart_labels': chart_labels[::-1],  # inverser pour affichage chronologique
        'chart_perdus': chart_perdus[::-1],
        'chart_trouves': chart_trouves[::-1],
    }

    return render(request, "frontend/admin/dashboard_admin.html", context)




@admin_required
def gerer_commissariats(request):
    commissariats = Commissariat.objects.all()
    return render(request, "frontend/admin/gerer_commissariats.html", {"commissariats": commissariats})

def gerer_utilisateurs(request):
    administrateurs = Utilisateur.objects.filter(role='admin')
    context = {
        'administrateurs': administrateurs  
    }
    return render(request, "frontend/admin/gerer_utilisateurs.html", context)



@admin_required
def creer_administrateur(request):
    if request.method == "POST":
        form = AdministrateurCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Administrateur créé et mot de passe envoyé par email.")
            return redirect('gerer_utilisateurs')
    else:
        form = AdministrateurCreationForm()
    return render(request, "frontend/admin/creer_administrateur.html", {"form": form})


@admin_required
def modifier_administrateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk, role='admin')
    if request.method == 'POST':
        form = AdministrateurForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Administrateur modifié avec succès.")
            return redirect('gerer_utilisateurs')
    else:
        form = AdministrateurForm(instance=utilisateur)
    return render(request, "frontend/admin/modifier_administrateur.html", {'form': form, 'utilisateur': utilisateur})


@admin_required
def supprimer_administrateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk, role='admin')
    utilisateur.delete()
    messages.success(request, "Administrateur supprimé avec succès.")
    return redirect('gerer_utilisateurs')


@admin_required
def gerer_policiers(request):
    policiers = Utilisateur.objects.filter(role='policier')
    return render(request, "frontend/admin/gerer_policiers.html", {'policiers': policiers})


@admin_required
def modifier_policier(request, pk):
    policier = get_object_or_404(Utilisateur, pk=pk, role='policier')
    if request.method == 'POST':
        form = PolicierForm(request.POST, instance=policier)
        if form.is_valid():
            form.save()
            messages.success(request, "Policier modifié avec succès.")
            return redirect('gerer_policiers')
    else:
        form = PolicierForm(instance=policier)
    return render(request, "frontend/admin/modifier_policier.html", {'form': form, 'policier': policier})


@admin_required
def supprimer_policier(request, pk):
    policier = get_object_or_404(Utilisateur, pk=pk, role='policier')
    policier.delete()
    messages.success(request, "Policier supprimé avec succès.")
    return redirect('gerer_policiers')


@admin_required
def voir_stats(request):
    # Comptages globaux
    nb_objets = Objet.objects.count()
    nb_restitutions = Restitution.objects.count()
    nb_citoyens = Utilisateur.objects.filter(role='citoyen').count()
    nb_admins = Utilisateur.objects.filter(role='admin', is_active=True).count()  # admins actifs
    nb_policiers = Utilisateur.objects.filter(role='policier').count()
    
    # Exemples d'évolution sur 7 jours (tu peux remplacer par données réelles)
    evolution_objets = [5, 8, 6, 12, 15, 18, nb_objets]
    evolution_restitutions = [2, 3, 4, 6, 5, 7, nb_restitutions]
    evolution_citoyens = [1, 2, 3, 5, 6, 8, nb_citoyens]
    evolution_admins = [1, 1, 1, 2, 2, 3, nb_admins]
    evolution_policiers = [1, 1, 2, 2, 3, 4, nb_policiers]

    context = {
        "nb_objets": nb_objets,
        "nb_objets_declare": nb_objets,  # pour clarifier le libellé
        "nb_restitutions": nb_restitutions,
        "nb_citoyens": nb_citoyens,
        "nb_admins": nb_admins,
        "nb_policiers": nb_policiers,
        "evolution_objets": evolution_objets,
        "evolution_restitutions": evolution_restitutions,
        "evolution_citoyens": evolution_citoyens,
        "evolution_admins": evolution_admins,
        "evolution_policiers": evolution_policiers,
    }
    return render(request, "frontend/admin/voir_stats.html", context)


@admin_required
def ajouter_commissariat(request):
    form = CommissariatForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "✅ Commissariat ajouté avec succès.")
        return redirect('gerer_commissariats')
    return render(request, 'frontend/admin/ajouter_commissariat.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string





admin_required
def creer_policier(request):
    # Précharger tous les commissariats pour le formulaire
    form = PolicierForm(request.POST or None)
    form.fields["commissariat"].queryset = Commissariat.objects.all()

    if request.method == "POST":
        if form.is_valid():
            # Génération d’un mot de passe sécurisé
            password = get_random_string(10)

            policier = form.save(commit=False)
            policier.set_password(password)
            policier.save()

            # Envoi d’un email avec les identifiants
            send_mail(
                subject="Création de votre compte Policier",
                message=(
                    f"Bonjour {policier.first_name},\n\n"
                    f"Votre compte a été créé avec succès.\n\n"
                    f"👤 Identifiant : {policier.username}\n"
                    f"🔐 Mot de passe : {password}\n\n"
                    f"Merci de le modifier dès votre première connexion."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[policier.email],
                fail_silently=False,
            )

            messages.success(request, "✅ Policier créé et mot de passe envoyé par email.")
            return redirect("liste_policiers")  # redirige vers la liste après création
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs dans le formulaire.")
    
    return render(request, "frontend/admin/creer_policier.html", {"form": form})


def is_admin(user):
    return user.is_authenticated and getattr(user, "role", None) == 'admin'


@login_required
@user_passes_test(is_admin)
def liste_citoyens(request):
    query = request.GET.get('q', '').strip()
    citoyens = Utilisateur.objects.filter(role='citoyen')
    if query:
        citoyens = citoyens.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    return render(request, 'frontend/admin/liste_citoyens.html', {'citoyens': citoyens})


@login_required
@user_passes_test(is_admin)
def bannir_citoyen(request, pk):
    citoyen = get_object_or_404(Utilisateur, id=pk, role='citoyen')
    citoyen.est_banni = True
    citoyen.save()
    return redirect('liste_citoyens')


@login_required
@user_passes_test(is_admin)
def debannir_citoyen(request, pk):
    citoyen = get_object_or_404(Utilisateur, id=pk, role='citoyen')
    citoyen.est_banni = False
    citoyen.save()
    return redirect('liste_citoyens')


# =============================
#       ACTIONS CITOYEN
# =============================

@login_required
def je_le_trouve(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)
    objet = declaration.objet

    # Vérification si l'utilisateur a déjà signalé l'objet
    if request.user in declaration.trouve_par.all():
        messages.warning(request, "⚠️ Vous avez déjà signalé cet objet.")
        return redirect("objets_perdus")

    try:
        with transaction.atomic():
            # Ajouter l'utilisateur à la liste des citoyens ayant trouvé l'objet
            declaration.trouve_par.add(request.user)

            # Si l'objet était perdu, passer à RECLAME
            if objet.etat == EtatObjet.PERDU:
                objet.etat = EtatObjet.RECLAME
                objet.save()

                # Ajouter le premier trouveur comme réclamant
                if not declaration.reclame_par.exists():
                    declaration.reclame_par.add(request.user)

    except Exception as e:
        messages.error(request, f"⚠️ Une erreur est survenue : {e}")
        return redirect("objets_perdus")

    # Notification par email au déclarant
    if declaration.citoyen and declaration.citoyen.email:
        objet_url = request.build_absolute_uri(reverse('objet_detail', args=[objet.id]))
        try:
            send_mail(
                subject=f"[Objet Réclamé] Votre objet '{objet.nom}' a été retrouvé",
                message=(
                    f"Bonjour {declaration.citoyen.username},\n\n"
                    f"L'objet que vous avez déclaré perdu a été retrouvé et signalé comme tel par {request.user.username}.\n\n"
                    f"Détails : {objet_url}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=True
            )
        except (BadHeaderError, ConnectionError, OSError):
            messages.warning(request, "⚠️ Impossible d'envoyer l'email au déclarant.")

    messages.success(request, f"✅ Vous avez signalé que vous avez trouvé l'objet '{objet.nom}'.")
    return redirect("objets_perdus")








@login_required
def ca_m_appartient(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    # Vérifications de base
    if declaration.citoyen == request.user:
        messages.warning(request, "⚠️ Vous ne pouvez pas réclamer votre propre objet.")
        return redirect("objets_trouves")

    if declaration.reclame_par.filter(id=request.user.id).exists():
        messages.warning(request, "⚠️ Vous avez déjà réclamé cet objet.")
        return redirect("objets_trouves")

    if declaration.objet.etat not in {EtatObjet.TROUVE, EtatObjet.RECLAME}:
        messages.error(request, "⚠️ Cet objet n'est pas disponible pour réclamation.")
        return redirect("objets_trouves")

    try:
        with transaction.atomic():
            declaration.reclame_par.add(request.user)
            if declaration.objet.etat == EtatObjet.TROUVE:
                declaration.objet.etat = EtatObjet.RECLAME
                declaration.objet.save()
    except Exception as e:
        messages.error(request, f"⚠️ Une erreur est survenue : {e}")
        return redirect("objets_trouves")

    # Envoi d'email
    if declaration.citoyen and declaration.citoyen.email:
        try:
            objet_url = request.build_absolute_uri(reverse('objet_detail', args=[declaration.objet.id]))
            send_mail(
                subject=f"[Objet Trouvé] Votre objet '{declaration.objet.nom}' a été réclamé !",
                message=(
                    f"Bonjour {declaration.citoyen.username},\n\n"
                    f"L'objet que vous avez déclaré perdu a été réclamé par {request.user.username}.\n\n"
                    f"Détails : {objet_url}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=True
            )
        except Exception as e:
            # Log si tu veux garder une trace
            print(f"Erreur d'envoi email: {e}")

    messages.success(request, f"✅ Vous avez réclamé l'objet '{declaration.objet.nom}'.")
    return redirect("objets_trouves")


# =============================
#       DASHBOARD CITOYEN
# =============================
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from backend.objets.models import Declaration, Restitution, EtatObjet, StatutRestitution

@login_required
def dashboard_citoyen(request):
    user = request.user

    # Comptage des objets perdus et trouvés par l'utilisateur
    nb_objets_perdus = Declaration.objects.filter(
        citoyen=user,
        etat_initial=EtatObjet.PERDU
    ).count()

    nb_objets_trouves = Declaration.objects.filter(
        citoyen=user,
        etat_initial=EtatObjet.TROUVE
    ).count()

    # Objets restitués
    nb_objets_restitues = Restitution.objects.filter(
        citoyen=user,
        statut=StatutRestitution.EFFECTUEE
    ).count()

    # 5 dernières notifications (déclarations)
    notifications = Declaration.objects.filter(
        citoyen=user
    ).order_by('-date_declaration')[:5]

    context = {
        'user': user,
        'nb_objets_perdus': nb_objets_perdus,
        'nb_objets_trouves': nb_objets_trouves,
        'nb_objets_restitues': nb_objets_restitues,
        'notifications': notifications,
    }
    return render(request, "frontend/citoyen/dashboard_citoyen.html", context)




@login_required
def mes_objets_trouves(request):
    """
    Affiche tous les objets que le citoyen a déclarés comme trouvés,
    avec état initial et état actuel égaux à TROUVE.
    """
    query = request.GET.get('q', '')

    # Filtrer les déclarations du citoyen où l'objet est trouvé
    declarations = Declaration.objects.filter(
        citoyen=request.user,
        etat_initial=EtatObjet.TROUVE,
        objet__etat=EtatObjet.TROUVE
    ).order_by('-date_declaration')

    if query:
        declarations = declarations.filter(objet__nom__icontains=query)

    context = {
        'declarations': declarations,
        'query': query,
    }
    return render(request, 'frontend/citoyen/mes_objets_trouves.html', context)


@login_required
def mes_objets_perdus(request):
    """
    Affiche tous les objets que le citoyen a déclarés comme perdus,
    avec état initial et état actuel égaux à PERDU.
    Possibilité de recherche via paramètre 'q'.
    """
    query = request.GET.get('q', '')

    # Filtrer les déclarations du citoyen où l'objet est perdu
    declarations = Declaration.objects.filter(
        citoyen=request.user,
        etat_initial=EtatObjet.PERDU,
        objet__etat=EtatObjet.PERDU
    ).order_by('-date_declaration')

    if query:
        declarations = declarations.filter(objet__nom__icontains=query)

    context = {
        'declarations': declarations,
        'query': query,
    }
    return render(request, 'frontend/citoyen/mes_objets_perdus.html', context)


@login_required
def modifier_objet_trouve(request, objet_id):
    declaration = get_object_or_404(Declaration, citoyen=request.user, objet_id=objet_id)

    if request.method == "POST":
        form = DeclarationForm(request.POST, request.FILES, instance=declaration)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Objet mis à jour avec succès.")
            return redirect('mes_objets_trouves')
    else:
        form = DeclarationForm(instance=declaration)

    return render(request, "frontend/citoyen/modifier_objet_trouve.html", {"form": form})


@login_required
def supprimer_objet_trouve(request, objet_id):
    declaration = get_object_or_404(Declaration, citoyen=request.user, objet_id=objet_id)
    # Allow POST or GET (template button). Consider changing to POST-only for safety.
    if request.method in ('POST', 'GET'):
        declaration.delete()
        messages.success(request, "✅ Objet supprimé avec succès.")
    return redirect('mes_objets_trouves')




@login_required
def historique_objets_restitues(request):
    """
    Affiche l'historique des objets restitués pour le citoyen connecté.
    """
    # On récupère toutes les restitutions où l'objet est restitué et appartenant à l'utilisateur
    restitutions = Restitution.objects.filter(
        citoyen=request.user,
        objet__etat=EtatObjet.RESTITUE
    ).order_by('-date_restitution', '-heure_restitution')

    # Préparer les données pour le template
    # On peut ajouter des propriétés pour faciliter l'affichage
    for r in restitutions:
        # utilisateur(s) ayant trouvé l'objet
        r.trouveurs = r.objet.declarations.filter(type_declaration='trouve').values_list('citoyen', flat=True)
        # propriétaire
        r.proprietaire = r.citoyen
        # état initial
        if r.objet.declarations.exists():
            r.etat_initial = r.objet.declarations.first().etat_initial
        else:
            r.etat_initial = 'N/A'

    context = {
        'restitutions': restitutions
    }
    return render(request, 'frontend/citoyen/historique_objets.html', context)


@login_required
def reclamer_objet(request, restitution_id):
    restitution = get_object_or_404(Restitution, id=restitution_id)

    if restitution.citoyen != request.user:
        messages.error(request, "⚠️ Vous n’êtes pas autorisé à réclamer cet objet.")
        return redirect("objets_a_reclamer")

    if restitution.objet.etat != EtatObjet.RESTITUE:
        messages.warning(request, "⚠️ Cet objet n'est pas encore restitué.")
        return redirect("objets_a_reclamer")

    restitution.objet.etat = EtatObjet.RECLAME
    restitution.objet.save()
    messages.success(request, f"✅ Vous avez réclamé l'objet '{restitution.objet.nom}'.")

    destinataires = []
    if restitution.policier and restitution.policier.email:
        destinataires.append(restitution.policier.email)
    if restitution.restitue_par and restitution.restitue_par.email:
        destinataires.append(restitution.restitue_par.email)

    if destinataires:
        send_mail(
            subject=f"[Objet Réclamé] {restitution.objet.nom}",
            message=(
                f"Le citoyen {request.user.username} a réclamé l'objet '{restitution.objet.nom}'.\n"
                f"Date de restitution: {restitution.date_restitution}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinataires,
            fail_silently=True
        )

    return redirect("objets_a_reclamer")


# =============================
#       Gestion déclarations (citoyen)
# =============================
@login_required

def modifier_declaration(request, declaration_id):
    """Modifier une déclaration par le citoyen."""
    declaration = get_object_or_404(Declaration, id=declaration_id, citoyen=request.user)

    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES, instance=declaration)
        if form.is_valid():
            form.save(commit=True)  # Django remplacera automatiquement l'image si uploadée
            messages.success(request, "✅ Objet mis à jour avec succès.")
            return redirect('objets_perdus')  # ou la page souhaitée
        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm(instance=declaration)

    return render(request, "frontend/citoyen/modifier_declaration.html", {"form": form})


@login_required
def supprimer_declaration(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id, citoyen=request.user)
    if request.method == 'POST':
        declaration.objet.delete()
        declaration.delete()
        messages.success(request, "✅ Objet supprimé avec succès.")
        return redirect('objets_perdus')
    return render(request, "frontend/citoyen/confirmer_suppression.html", {"declaration": declaration})
