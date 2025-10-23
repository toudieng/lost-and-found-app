# views.py (réorganisé)

from functools import wraps
import calendar
import random
import string
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
    # 🔹 Objets perdus récents
    objets_perdus = Objet.objects.filter(etat=EtatObjet.PERDU).order_by('-id')[:6]

    # 🔹 Objets trouvés récents
    objets_trouves = Objet.objects.filter(etat=EtatObjet.TROUVE).order_by('-id')[:6]

    # 🔸 Construction des slides dynamiques avec type d'état
    slides_perdus = [
        {
            'url': obj.image.url if obj.image else '/static/frontend/images/default.jpg',
            'titre': obj.nom,
            'description': (obj.description[:120] + "...") if obj.description else "",
            'etat': obj.get_etat_display(),  # affiche "Perdu"
            'etat_type': 'perdu'
        }
        for obj in objets_perdus
    ]

    slides_trouves = [
        {
            'url': obj.image.url if obj.image else '/static/frontend/images/default.jpg',
            'titre': obj.nom,
            'description': (obj.description[:120] + "...") if obj.description else "",
            'etat': obj.get_etat_display(),  # affiche "Trouvé"
            'etat_type': 'trouve'
        }
        for obj in objets_trouves
    ]

    # 🔹 Fusionner les deux listes pour un seul carrousel
    all_slides = slides_perdus + slides_trouves

    return render(request, "frontend/home.html", {
        'all_slides': all_slides
    })






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
    """Liste publique d'objets déclarés perdus, avec recherche simple."""
    declarations = Declaration.objects.filter(objet__etat=EtatObjet.PERDU)
    query = request.GET.get('q', '').strip()
    if query:
        declarations = declarations.filter(objet__nom__icontains=query)
    return render(request, "frontend/objets/objets_perdus.html", {
        "declarations": declarations,
        "query": query
    })


@login_required
def objets_trouves(request):
    query = request.GET.get("q", "").strip()
    declarations = Declaration.objects.filter(objet__etat=EtatObjet.TROUVE).order_by('-date_declaration')
    if query:
        declarations = declarations.filter(objet__nom__icontains=query)
    return render(request, "frontend/objets/objets_trouves.html", {
        "declarations": declarations,
        "query": query
    })


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
    # Statistiques
    nb_objets_trouves = Declaration.objects.filter(etat_initial=EtatObjet.TROUVE).count()
    nb_objets_a_restituer = Declaration.objects.filter(etat_initial=EtatObjet.RECLAME).count()
    nb_restitutions = Restitution.objects.filter(statut=StatutRestitution.EFFECTUEE).count()

    # Notifications récentes (exemple : 5 dernières déclarations non traitées)
    notifications = Declaration.objects.filter(etat_initial__in=[EtatObjet.TROUVE, EtatObjet.RECLAME]).order_by('-date_declaration')[:5]

    context = {
        'nb_objets_trouves': nb_objets_trouves,
        'nb_objets_a_restituer': nb_objets_a_restituer,
        'nb_restitutions': nb_restitutions,
        'notifications': notifications,
        'current_year': timezone.now().year,
    }
    return render(request, 'frontend/policier/dashboard_policier.html', context)

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


@policier_required
def historique_restitutions(request):
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat', 'restitue_par'
    ).filter(objet__etat=EtatObjet.RESTITUE).order_by('-date_restitution', '-heure_restitution')

    # Préparer attributs pour template : propriétaire & liste de trouveurs
    for r in restitutions:
        r.proprietaire = r.citoyen
        declarations_trouvees = Declaration.objects.filter(objet=r.objet, trouve_par__isnull=False).prefetch_related('trouve_par')
        trouveurs = set()
        for d in declarations_trouvees:
            for u in d.trouve_par.all():
                trouveurs.add(u)
        r.trouveurs = list(trouveurs)

    return render(request, "frontend/policier/historique_restitutions.html", {
        "restitutions": restitutions
    })


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


@policier_required
def objets_reclames(request):
    """
    Liste des objets réclamés par des citoyens.
    """
    declarations = (
        Declaration.objects
        .filter(objet__etat=EtatObjet.RECLAME, reclame_par__isnull=False)
        .select_related("objet", "reclame_par", "citoyen")
        .prefetch_related("trouve_par")
        .order_by("-date_declaration")
    )

    for dec in declarations:
        dec.trouveur = dec.citoyen if dec.objet.etat == EtatObjet.TROUVE else None

    restitutions = Restitution.objects.filter(restitue_par__isnull=True).select_related("objet")
    restitutions_dict = {r.objet.id: r for r in restitutions}

    return render(
        request,
        "frontend/objets/objets_reclames.html",
        {
            "declarations": declarations,
            "restitutions_dict": restitutions_dict,
        },
    )


@policier_required
def objets_trouves_attente(request):
    """
    Restitutions en attente (statut planifié) et préchargement des déclarations/trouveurs.
    """
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat', 'restitue_par'
    ).filter(
        statut='planifiee',
        objet__etat=EtatObjet.EN_ATTENTE
    )

    declarations_prefetch = Prefetch(
        'objet__declaration_set',
        queryset=Declaration.objects.prefetch_related('trouve_par'),
        to_attr='declarations_trouvees'
    )

    restitutions = restitutions.prefetch_related(declarations_prefetch)
    return render(request, "frontend/objets/objets_trouves_attente.html", {
        "restitutions": restitutions
    })


@policier_required
def planifier_restitution(request, objet_id, type_objet="declaration"):
    declaration = None
    if type_objet == "declaration":
        declaration = get_object_or_404(Declaration, id=objet_id)
        trouveurs = declaration.trouve_par.all()
        trouveur_unique = trouveurs.first() if trouveurs.count() == 1 else None

        restitution, created = Restitution.objects.get_or_create(
            objet=declaration.objet,
            citoyen=declaration.reclame_par,
            defaults={
                "policier": request.user,
                "restitue_par": trouveur_unique
            }
        )
        if created:
            declaration.objet.etat = EtatObjet.EN_ATTENTE
            declaration.objet.save()

    elif type_objet == "restitution":
        restitution = get_object_or_404(Restitution, id=objet_id)
    else:
        messages.error(request, "Type d'objet inconnu pour la restitution.")
        return redirect("objets_reclames")

    commissariats = Commissariat.objects.all()
    form = RestitutionForm(request.POST or None, initial={
        "date_restitution": restitution.date_restitution,
        "heure_restitution": restitution.heure_restitution,
        "commissariat": restitution.commissariat
    })

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        restitution.policier = request.user
        restitution.date_restitution = cd["date_restitution"]
        restitution.heure_restitution = cd["heure_restitution"]
        restitution.commissariat = cd["commissariat"]
        restitution.save()

        destinataires = [
            email for email in [
                restitution.citoyen.email if restitution.citoyen else None,
                restitution.restitue_par.email if restitution.restitue_par else None,
                request.user.email
            ] if email
        ]
        if destinataires:
            send_mail(
                subject=f"[Restitution planifiée] {restitution.objet.nom}",
                message=(
                    f"La restitution de '{restitution.objet.nom}' a été planifiée.\n"
                    f"📍 Commissariat: {restitution.commissariat.nom if restitution.commissariat else 'Non assigné'}\n"
                    f"📅 Date: {restitution.date_restitution}\n"
                    f"⏰ Heure: {restitution.heure_restitution}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinataires,
                fail_silently=False
            )

        messages.success(request, f"La restitution de '{restitution.objet.nom}' a été planifiée ✅")
        return redirect("objets_reclames")

    return render(request, "frontend/policier/planifier_restitution.html", {
        "restitution": restitution,
        "declaration": declaration,
        "form": form,
        "commissariats": commissariats,
        "type_objet": type_objet
    })


@policier_required
def marquer_restitue(request, restitution_id):
    restitution = get_object_or_404(Restitution, id=restitution_id)

    if restitution.policier != request.user:
        messages.error(request, "Vous n’êtes pas autorisé à valider cette restitution.")
        return redirect("objets_trouves_attente")

    objet = restitution.objet
    try:
        with transaction.atomic():
            objet.etat = EtatObjet.RESTITUE
            objet.save()

            # Tenter de déterminer le trouveur (si présent)
            if objet.declaration_set.exists():
                first_decl = objet.declaration_set.first()
                trouveur = first_decl.trouve_par.first() if first_decl else None
                restitution.restitue_par = trouveur if trouveur else None
            else:
                restitution.restitue_par = None

            restitution.save()
            # mettre à jour déclarations si besoin (placeholder)
            Declaration.objects.filter(objet=objet).update()
        messages.success(request, f"L'objet '{objet.nom}' a été marqué comme restitué ✅")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {str(e)}")

    return redirect("objets_trouves_attente")


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
    # Récupérer la restitution
    restitution = get_object_or_404(Restitution, pk=pk)

    # Générer QR Code (par exemple : url de vérification)
    qr_data = f"http://ton-site.com/verifier-restitution/{restitution.id}/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir l'image en base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Préparer le contexte pour le template
    context = {
        'restitution': restitution,
        'now': timezone.now(),
        'qr_code': qr_code_base64,
    }

    # Générer le HTML du PDF
    html_string = render_to_string('frontend/policier/preuve_restitution_pdf.html', context)

    # Générer le PDF
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    # Retourner le PDF dans la réponse HTTP
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

    # Contexte pour le template
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
        'messages_recus': messages_recus,  # Ajout des messages citoyens
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


@admin_required
def creer_policier(request):
    form = PolicierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        policier = form.save(commit=False)
        policier.set_password(password)
        policier.save()

        send_mail(
            "Création de votre compte Policier",
            f"Bonjour {policier.first_name},\n\nVotre compte a été créé.\nIdentifiant: {policier.username}\nMot de passe: {password}",
            settings.DEFAULT_FROM_EMAIL,
            [policier.email],
            fail_silently=False,
        )
        messages.success(request, "Policier créé et mot de passe envoyé par email ✅")
        return redirect("creer_policier")
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

    if objet.etat == EtatObjet.PERDU:
        objet.etat = EtatObjet.RECLAME
        objet.save()
        declaration.trouve_par.add(request.user)
        if not declaration.reclame_par:
            declaration.reclame_par = declaration.citoyen
        declaration.save()

        if declaration.citoyen and declaration.citoyen.email:
            try:
                send_mail(
                    subject=f"[Objet Réclamé] Votre objet {objet.nom} a été signalé comme trouvé",
                    message=(
                        f"Bonjour {declaration.citoyen.username},\n\n"
                        f"L'objet '{objet.nom}' a été retrouvé et signalé comme tel par un citoyen."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[declaration.citoyen.email],
                    fail_silently=True
                )
            except Exception:
                # On ignore l'échec d'envoi pour ne pas casser l'action utilisateur
                pass

        messages.success(request, "✅ L’objet a été marqué comme réclamé.")

    elif objet.etat == EtatObjet.RECLAME:
        if request.user not in declaration.trouve_par.all():
            declaration.trouve_par.add(request.user)
            messages.info(request, "ℹ️ Votre signalement a été ajouté.")
        else:
            messages.warning(request, "⚠️ Vous avez déjà signalé cet objet.")
    else:
        messages.warning(request, "⚠️ Cet objet a déjà été restitué.")

    return redirect("objets_perdus")


@login_required
def ca_m_appartient(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    if declaration.objet.etat == EtatObjet.TROUVE and declaration.reclame_par is None:
        declaration.reclame_par = request.user
        declaration.objet.etat = EtatObjet.RECLAME
        declaration.objet.save()
        declaration.save()

        if declaration.citoyen and declaration.citoyen.email:
            objet_url = request.build_absolute_uri(reverse('objet_detail', args=[declaration.objet.id]))
            try:
                send_mail(
                    subject=f"[Objet Trouvé] Votre objet '{declaration.objet.nom}' a été réclamé !",
                    message=(
                        f"Bonjour {declaration.citoyen.username},\n\n"
                        f"L'objet que vous avez déclaré perdu a été retrouvé et réclamé par "
                        f"{request.user.username}.\n\n"
                        f"Détails : {objet_url}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[declaration.citoyen.email],
                    fail_silently=False,
                )
            except (BadHeaderError, ConnectionError, OSError) as e:
                messages.warning(request, f"⚠️ Impossible d'envoyer l'email : {e}")

        messages.success(request, f"✅ Vous avez réclamé l'objet '{declaration.objet.nom}'.")
    else:
        messages.error(request, "⚠️ Cet objet a déjà été réclamé ou n'est pas encore marqué comme trouvé.")

    return redirect("objets_trouves")


# =============================
#       DASHBOARD CITOYEN
# =============================

@login_required
def dashboard_citoyen(request):
    user = request.user

    nb_objets_perdus = Declaration.objects.filter(
        citoyen=user,
        objet__etat=EtatObjet.PERDU
    ).count()

    nb_objets_trouves = Declaration.objects.filter(
        trouve_par=user,
        objet__etat=EtatObjet.TROUVE
    ).count()

    nb_objets_restitues = Restitution.objects.filter(
        Q(citoyen=user) | Q(objet__declaration__citoyen=user),
        statut=''
    ).count()

    notifications = Declaration.objects.filter(
        Q(citoyen=user) | Q(trouve_par=user)
    ).order_by('-date_declaration')[:5]

    context = {
        'user': user,  # ✅ Ajouter explicitement l'utilisateur
        'nb_objets_perdus': nb_objets_perdus,
        'nb_objets_trouves': nb_objets_trouves,
        'nb_objets_restitues': nb_objets_restitues,
        'notifications': notifications,
    }
    return render(request, "frontend/citoyen/dashboard_citoyen.html", context)

@login_required
def mes_objets_perdus(request):
    objets = Declaration.objects.filter(
        citoyen=request.user,
        objet__etat=EtatObjet.PERDU
    ).select_related('objet').order_by('-date_declaration')

    return render(request, "frontend/citoyen/mes_objets_perdus.html", {"objets": objets})


@login_required
def mes_objets_trouves(request):
    q = request.GET.get('q', '').strip()
    objets_trouves = Declaration.objects.filter(
        citoyen=request.user,
        objet__etat=EtatObjet.TROUVE
    ).select_related('objet').order_by('-date_declaration')

    if q:
        objets_trouves = objets_trouves.filter(
            models.Q(objet__nom__icontains=q) |
            models.Q(objet__description__icontains=q)
        )

    return render(request, "frontend/citoyen/mes_objets_trouves.html", {
        "objets": objets_trouves
    })


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


def historique_objets_restitues(request):
    restitutions = Restitution.objects.filter(
        citoyen=request.user,
        objet__etat=EtatObjet.RESTITUE  # si ton modèle de statut est EtatObjet
    ).order_by('-date_restitution', '-heure_restitution')

    return render(request, 'frontend/citoyen/historique_objets.html', {'restitutions': restitutions})


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
