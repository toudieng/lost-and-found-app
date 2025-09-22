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
    return render(request, "frontend/home.html")

def contact(request):
    return render(request, "frontend/contact.html")

@login_required(login_url='login')
def objets_perdus(request):
    declarations = Declaration.objects.filter(objet__etat=EtatObjet.PERDU)
    return render(request, "frontend/objets/objets_perdus.html", {"declarations": declarations})

@login_required(login_url='login')
def objets_trouves(request):
    declarations = Declaration.objects.filter(
        objet__etat=EtatObjet.RETROUVE,  # ← ici
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
@policier_required
def dashboard_policier(request):
    user = request.user
    now = timezone.now()

    nb_objets_trouves = Declaration.objects.filter(objet__etat=EtatObjet.RETROUVE).count()
    nb_objets_a_restituer = Declaration.objects.filter(objet__etat=EtatObjet.EN_ATTENTE).count()
    nb_restitutions = Restitution.objects.count()
    notifications = user.notifications.order_by('-date')[:5]

    months_labels = [calendar.month_name[i] for i in range(1, 13)]
    data_trouves = [0]*12
    data_restitues = [0]*12

    objets_trouves_month = (
        Declaration.objects
        .filter(objet__etat=EtatObjet.RETROUVE, date_declaration__year=now.year)
        .annotate(month=TruncMonth('date_declaration'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    for ot in objets_trouves_month:
        data_trouves[ot['month'].month - 1] = ot['count']

    restitutions_month = (
        Restitution.objects
        .filter(date_restitution__year=now.year)
        .annotate(month=TruncMonth('date_restitution'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    for r in restitutions_month:
        data_restitues[r['month'].month - 1] = r['count']

    context = {
        "nb_objets_retrouves": nb_objets_trouves,
        "nb_objets_a_restituer": nb_objets_a_restituer,
        "nb_restitutions": nb_restitutions,
        "notifications": notifications,
        "labels_trouves": months_labels,
        "data_trouves": data_trouves,
        "labels_restitues": months_labels,
        "data_restitues": data_restitues,
        "year": now.year,
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

@policier_required
def historique_restitutions(request):
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat', 'restitue_par'
    ).filter(objet__etat=EtatObjet.RESTITUE).order_by('-date_restitution', '-heure_restitution')

    for r in restitutions:
        r.declaration_citoyen = r.objet.declaration_set.filter(citoyen=r.citoyen).first()

    return render(request, "frontend/policier/historique_restitutions.html", {"restitutions": restitutions})

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
    declarations = Declaration.objects.filter(
        objet__etat=EtatObjet.RECLAME,
        reclame_par__isnull=False
    ).prefetch_related('reclame_par').order_by('-date_declaration')
    restitutions = Restitution.objects.filter(restitue_par__isnull=True)
    restitutions_dict = {r.objet.id: r for r in restitutions}
    return render(request, "frontend/objets/objets_reclames.html", {
        "declarations": declarations,
        "restitutions_dict": restitutions_dict,
    })


@policier_required
def objets_trouves_attente(request):
    # On récupère les restitutions dont l'objet est en attente et non encore restitué
    restitutions = (
        Restitution.objects.select_related("objet", "citoyen", "policier", "commissariat")
        .filter(objet__etat=EtatObjet.EN_ATTENTE, restitue_par__isnull=True)
        .order_by('-date_restitution', '-heure_restitution')
    )

    return render(
        request,
        "frontend/objets/objets_trouves_attente.html",
        {"restitutions": restitutions}
    )

@policier_required
def planifier_restitution(request, objet_id, type_objet="declaration"):
    declaration = None
    if type_objet == "declaration":
        declaration = get_object_or_404(Declaration, id=objet_id)
        restitution, created = Restitution.objects.get_or_create(
            objet=declaration.objet,
            citoyen=declaration.reclame_par,
            defaults={"policier": request.user}
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

        destinataires = [email for email in [restitution.citoyen.email if restitution.citoyen else None, request.user.email] if email]
        if destinataires:
            send_mail(
                subject=f"[Restitution planifiée] {restitution.objet.nom}",
                message=f"La restitution de '{restitution.objet.nom}' a été planifiée.\n📍 Commissariat: {restitution.commissariat.nom if restitution.commissariat else 'Non assigné'}\n📅 Date: {restitution.date_restitution}\n⏰ Heure: {restitution.heure_restitution}",
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
            restitution.restitue_par = request.user
            restitution.save()

            declarations = Declaration.objects.filter(objet=objet)
            for declaration in declarations:
                declaration.save()
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
        objet.etat = EtatObjet.RECLAME
        objet.save()
        declaration.trouve_par.add(request.user)
        declaration.save()

        if declaration.citoyen and declaration.citoyen.email:
            send_mail(
                subject=f"[Objet Réclamé] Votre objet {objet.nom} a été signalé comme retrouvé",
                message=f"Bonjour {declaration.citoyen.username},\n\nL'objet '{objet.nom}' a été signalé comme réclamé par un citoyen.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=True
            )
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
    if declaration.objet.etat == EtatObjet.RETROUVE and declaration.reclame_par is None:  # ← ici
        declaration.reclame_par = request.user
        declaration.objet.etat = EtatObjet.RECLAME
        declaration.objet.save()
        declaration.save()

        if declaration.citoyen and declaration.citoyen.email:
            objet_url = request.build_absolute_uri(reverse('objet_detail', args=[declaration.objet.id]))
            send_mail(
                subject=f"[Objet Trouvé] Votre objet '{declaration.objet.nom}' a été réclamé !",
                message=f"Bonjour {declaration.citoyen.username},\nL'objet a été réclamé par {request.user.username}.\nDétails: {objet_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=False
            )
        messages.success(request, f"✅ Vous avez réclamé l'objet '{declaration.objet.nom}'.")
    else:
        messages.error(request, "⚠️ Cet objet a déjà été réclamé ou n'est pas retrouvé.")
    return redirect("objets_trouves")
