from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
import calendar, random, string

from backend.objets.models import Objet, Declaration, Restitution, Commissariat, EtatObjet
from backend.objets.forms import RestitutionForm
from backend.users.models import Utilisateur, Notification
from backend.users.forms import CommissariatForm, PolicierForm, AdministrateurCreationForm

# =============================
#       DÉCORATEURS RÔLES
# =============================
def policier_required(view_func):
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if request.user.role != "policier":
            messages.error(request, "⚠️ Accès réservé aux policiers.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if request.user.role != "admin":
            messages.error(request, "⛔ Accès réservé aux administrateurs.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper

# =============================
#       PAGES PUBLIQUES
# =============================

def home(request):
    slides = [
        {'url': 'frontend/images/head1.jpg', 'titre': 'Bienvenue', 'description': 'Découvrez les objets perdus'},
        {'url': 'frontend/images/head2.jpg', 'titre': '', 'description': ''},
        {'url': 'frontend/images/head3.jpg', 'titre': '', 'description': ''},
        {'url': 'frontend/images/head4.jpg', 'titre': '', 'description': ''},
        {'url': 'frontend/images/head5.jpg', 'titre': '', 'description': ''},
    ]
    return render(request, "frontend/home.html", {'slides': slides})

def contact(request):
    return render(request, "frontend/contact.html")

@login_required(login_url='login')
def objets_perdus(request):
    declarations = Declaration.objects.filter(objet__etat=EtatObjet.PERDU)
    return render(request, "frontend/objets/objets_perdus.html", {"declarations": declarations})

@login_required(login_url='login')
def objets_trouves(request):
    declarations = Declaration.objects.filter(
        objet__etat=EtatObjet.TROUVE,  # ← ici
        reclame_par__isnull=True
    ).order_by('-date_declaration')
    return render(request, "frontend/objets/objets_trouves.html", {"declarations": declarations})

def objet_detail(request, pk):
    objet = get_object_or_404(Objet, pk=pk)
    return render(request, "frontend/objets/objet_detail.html", {"objet": objet})

def supprimer_objet(request, objet_id):
    objet = get_object_or_404(Objet, id=objet_id)
    if request.method == "POST":
        objet.delete()
        messages.success(request, "Objet supprimé avec succès.")
    return redirect('liste_objets_declares')

# =============================
#       DASHBOARD POLICIER
# =============================
from django.db.models import Count
from django.utils.timezone import now
from datetime import timedelta
import calendar

@login_required
def dashboard_policier(request):
    # 📦 Statistiques globales
    nb_objets_trouves = Restitution.objects.filter(objet__etat='en_attente').count()
    nb_objets_a_restituer = Declaration.objects.filter(objet__etat='reclame').count()
    nb_restitutions = Restitution.objects.filter(objet__etat='restitue').count()

    # 📊 Statistiques par mois pour les 6 derniers mois
    today = now().date()
    labels_trouves, data_trouves = [], []
    labels_restitues, data_restitues = [], []

    for i in range(5, -1, -1):  # 5 mois en arrière + ce mois
        month = (today - timedelta(days=i*30)).month
        year = (today - timedelta(days=i*30)).year
        month_name = calendar.month_name[month]

        # Objets retrouvés → basé sur la date de création de la restitution
        nb_trouves = Restitution.objects.filter(
            date_restitution__year=year,
            date_restitution__month=month,
            objet__etat='en_attente'
        ).count()
        labels_trouves.append(month_name)
        data_trouves.append(nb_trouves)

        # Objets restitués
        nb_restitues = Restitution.objects.filter(
            date_restitution__year=year,
            date_restitution__month=month,
            objet__etat='restitue'
        ).count()
        labels_restitues.append(month_name)
        data_restitues.append(nb_restitues)

    # 🔔 Notifications récentes (derniers 5)
    notifications = Notification.objects.filter(user=request.user).order_by('-date')[:5]

    context = {
        'nb_objets_trouves': nb_objets_trouves,
        'nb_objets_a_restituer': nb_objets_a_restituer,
        'nb_restitutions': nb_restitutions,
        'labels_trouves': labels_trouves,
        'data_trouves': data_trouves,
        'labels_restitues': labels_restitues,
        'data_restitues': data_restitues,
        'notifications': notifications,
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
    # On récupère toutes les restitutions des objets déjà restitués
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat', 'restitue_par'
    ).filter(objet__etat=EtatObjet.RESTITUE).order_by('-date_restitution', '-heure_restitution')

    # On prépare les attributs pour le template
    for r in restitutions:
        # Le propriétaire = celui qui a réclamé
        r.proprietaire = r.citoyen

        # Tous les utilisateurs qui ont trouvé cet objet
        declarations_trouvees = Declaration.objects.filter(objet=r.objet, trouve_par__isnull=False).prefetch_related('trouve_par')
        trouveurs = set()  # éviter les doublons
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
@login_required
def objets_reclames(request):
    """
    Liste des objets réclamés par des citoyens.
    - Un objet doit avoir l'état 'RECLAME'
    - Il doit être lié à un citoyen via 'reclame_par'
    """
    declarations = (
        Declaration.objects.filter(
            objet__etat=EtatObjet.RECLAME,   # uniquement les objets marqués comme réclamés
            reclame_par__isnull=False        # avec un citoyen qui les a réclamés
        )
        .select_related("objet", "reclame_par")   # optimisations FK
        .prefetch_related("trouve_par")           # optimisations M2M
        .order_by("-date_declaration")
    )

    # Restitutions non encore effectuées (planifiées ou en attente)
    restitutions = (
        Restitution.objects
        .filter(restitue_par__isnull=True)
        .select_related("objet")
    )

    # Dictionnaire {objet_id: restitution} pour savoir si une restitution existe déjà
    restitutions_dict = {r.objet.id: r for r in restitutions}

    return render(
        request,
        "frontend/objets/objets_reclames.html",
        {
            "declarations": declarations,
            "restitutions_dict": restitutions_dict,
        },
    )

from django.db.models import Prefetch


@login_required
def objets_trouves_attente(request):
    # Récupérer les restitutions en attente
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat', 'restitue_par'
    ).filter(
        statut='planifiee',
        objet__etat=EtatObjet.EN_ATTENTE
    )

    # Précharger les déclarations et les utilisateurs qui ont trouvé l'objet
    declarations_prefetch = Prefetch(
        'objet__declaration_set',
        queryset=Declaration.objects.prefetch_related('trouve_par'),
        to_attr='declarations_trouvees'  # attribut temporaire pour simplifier le template
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

        # Pré-remplir restitue_par si un seul trouveur
        trouveurs = declaration.trouve_par.all()
        trouveur_unique = trouveurs.first() if trouveurs.count() == 1 else None

        restitution, created = Restitution.objects.get_or_create(
            objet=declaration.objet,
            citoyen=declaration.reclame_par,
            defaults={
                "policier": request.user,
                "restitue_par": trouveur_unique  # <= auto si unique trouveur
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

        # Notifications par mail
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

    # Vérification de l'autorisation
    if restitution.policier != request.user:
        messages.error(request, "Vous n’êtes pas autorisé à valider cette restitution.")
        return redirect("objets_trouves_attente")

    objet = restitution.objet
    try:
        with transaction.atomic():
            # Mettre à jour l'état de l'objet
            objet.etat = EtatObjet.RESTITUE
            objet.save()

            # Déterminer qui a trouvé l'objet
            if objet.declaration_set.exists():
                # On prend le premier utilisateur qui a trouvé l'objet
                trouveur = objet.declaration_set.first().trouve_par.first()
                restitution.restitue_par = trouveur if trouveur else None
            else:
                restitution.restitue_par = None

            restitution.save()

            # Optionnel : mettre à jour toutes les déclarations liées
            Declaration.objects.filter(objet=objet).update()  # juste pour déclencher save si needed

        messages.success(request, f"L'objet '{objet.nom}' a été marqué comme restitué ✅")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {str(e)}")

    return redirect("objets_trouves_attente")


# =============================
#       DASHBOARD ADMIN
# =============================
@admin_required
def dashboard_admin(request):
    context = {
        'nb_commissariats': Commissariat.objects.count(),
        'nb_utilisateurs': Utilisateur.objects.count(),
        'nb_objets': Objet.objects.count(),
    }
    return render(request, "frontend/admin/dashboard_admin.html", context)

@admin_required
def gerer_commissariats(request):
    commissariats = Commissariat.objects.all()
    return render(request, "frontend/admin/gerer_commissariats.html", {"commissariats": commissariats})

@admin_required
def gerer_utilisateurs(request):
    return render(request, "frontend/admin/gerer_utilisateurs.html")

@user_passes_test(lambda u: u.is_authenticated and u.role=="admin")
def creer_administrateur(request):
    if request.method == "POST":
        form = AdministrateurCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Administrateur créé et mot de passe envoyé par email.")
            return redirect('dashboard_admin')
    else:
        form = AdministrateurCreationForm()
    return render(request, "frontend/admin/creer_admin.html", {"form": form})

@admin_required
def voir_stats(request):
    context = {
        "nb_objets": Objet.objects.count(),
        "nb_restitutions": Restitution.objects.count()
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
        return redirect("gerer_utilisateurs")
    return render(request, "frontend/admin/creer_policier.html", {"form": form})

# =============================
#       ACTIONS CITOYEN
# =============================
@login_required
def je_le_trouve(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)
    objet = declaration.objet

    if objet.etat == EtatObjet.PERDU:
        # Transition PERDU → RECLAME (l'objet a été trouvé par un citoyen)
        objet.etat = EtatObjet.RECLAME
        objet.save()

        # Celui qui clique est le trouveur
        declaration.trouve_par.add(request.user)

        # Le réclamant reste le citoyen qui a déclaré la perte
        if not declaration.reclame_par:
            declaration.reclame_par = declaration.citoyen
        declaration.save()

        # Notification au citoyen propriétaire
        if declaration.citoyen and declaration.citoyen.email:
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
        messages.success(request, "✅ L’objet a été marqué comme réclamé.")

    elif objet.etat == EtatObjet.RECLAME:
        # Déjà réclamé, on vérifie si l’utilisateur a déjà signalé
        if request.user not in declaration.trouve_par.all():
            declaration.trouve_par.add(request.user)
            messages.info(request, "ℹ️ Votre signalement a été ajouté.")
        else:
            messages.warning(request, "⚠️ Vous avez déjà signalé cet objet.")

    else:
        messages.warning(request, "⚠️ Cet objet a déjà été restitué.")
    
    return redirect("objets_perdus")



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.urls import reverse
from backend.objets.models import Declaration, EtatObjet
from django.conf import settings

@login_required
def ca_m_appartient(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    # Vérifier que l'objet est bien dans l'état TROUVÉ
    if declaration.objet.etat == EtatObjet.TROUVE and declaration.reclame_par is None:
        # Le citoyen actuel devient celui qui réclame l’objet
        declaration.reclame_par = request.user
        declaration.objet.etat = EtatObjet.RECLAME
        declaration.objet.save()
        declaration.save()

        # Notifier par email le citoyen qui avait perdu l’objet
        if declaration.citoyen and declaration.citoyen.email:
            objet_url = request.build_absolute_uri(
                reverse('objet_detail', args=[declaration.objet.id])
            )
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
                # Empêche le plantage si le serveur mail n'est pas disponible
                messages.warning(request, f"⚠️ Impossible d'envoyer l'email : {e}")

        messages.success(request, f"✅ Vous avez réclamé l'objet '{declaration.objet.nom}'.")
    else:
        messages.error(request, "⚠️ Cet objet a déjà été réclamé ou n'est pas encore marqué comme trouvé.")

    return redirect("objets_trouves")



# =============================
#       Dashboard Citoyen
# =============================
@login_required
def dashboard_citoyen(request):
    user = request.user

    # Objets perdus déclarés par ce citoyen
    nb_objets_perdus = Declaration.objects.filter(citoyen=user).count()

    # Objets trouvés par ce citoyen
    nb_objets_trouvees = Declaration.objects.filter(trouve_par=user).count()

    # Objets restitués au citoyen
    nb_objets_restitues = Restitution.objects.filter(
        citoyen=user,
        statut='effectuee'
    ).count()

    # Notifications récentes (dernières déclarations)
    notifications = Declaration.objects.filter(citoyen=user).order_by('-date_declaration')[:5]

    context = {
        'nb_objets_perdus': nb_objets_perdus,
        'nb_objets_trouves': nb_objets_trouvees,
        'nb_objets_restitues': nb_objets_restitues,
        'notifications': notifications,
    }

    return render(request, "frontend/citoyen/dashboard_citoyen.html", context)


# =============================
#       Objets perdus par le citoyen
# =============================
@login_required
def mes_objets_perdus(request):
    objets = Declaration.objects.filter(
        citoyen=request.user,
        objet__etat=EtatObjet.PERDU
    ).order_by('-date_declaration')
    return render(request, "frontend/citoyen/mes_objets_perdus.html", {
        "objets": objets
    })


# =============================
#       Objets trouvés par le citoyen
# =============================
@login_required
def mes_objets_trouves(request):
    # Filtre les déclarations où le citoyen a trouvé l'objet
    declarations_trouvees = Declaration.objects.filter(
        trouve_par=request.user,
        objet__etat__in=[EtatObjet.EN_ATTENTE, EtatObjet.RECLAME]
    ).order_by('-id')

    objets_trouves = [dec.objet for dec in declarations_trouvees if dec.objet]

    return render(request, "frontend/citoyen/mes_objets_trouves.html", {
        "objets_trouves": objets_trouves
    })


# =============================
#       Objets à réclamer
# =============================
@login_required
def objets_a_reclamer(request):
    restitutions = Restitution.objects.filter(
        citoyen=request.user,
        objet__etat__in=[EtatObjet.RESTITUE, EtatObjet.EN_ATTENTE],
        restitue_par__isnull=False
    ).order_by('-date_restitution')

    return render(request, "frontend/citoyen/objets_a_reclamer.html", {
        "restitutions": restitutions
    })


# =============================
#       Planifier / réclamer un objet
# =============================
@login_required
def reclamer_objet(request, restitution_id):
    restitution = get_object_or_404(Restitution, id=restitution_id)

    # Vérifie que l'objet est destiné à l'utilisateur
    if restitution.citoyen != request.user:
        messages.error(request, "⚠️ Vous n’êtes pas autorisé à réclamer cet objet.")
        return redirect("objets_a_reclamer")

    if restitution.objet.etat != EtatObjet.RESTITUE:
        messages.warning(request, "⚠️ Cet objet n'est pas encore restitué.")
        return redirect("objets_a_reclamer")

    # Marquer l'objet comme réclamé
    restitution.objet.etat = EtatObjet.RECLAME
    restitution.objet.save()
    messages.success(request, f"✅ Vous avez réclamé l'objet '{restitution.objet.nom}'.")

    # Envoi mail au policier et/ou trouveur
    destinataires = [email for email in [
        restitution.policier.email if restitution.policier else None,
        restitution.restitue_par.email if restitution.restitue_par else None
    ] if email]

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


