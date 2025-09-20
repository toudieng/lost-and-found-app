from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import random, string
from datetime import datetime
from django.utils import timezone

from backend.objets.models import Objet, Declaration, Restitution, Commissariat
from backend.users.forms import CommissariatForm, PolicierForm,AdministrateurCreationForm
from backend.objets.forms import RestitutionForm
from backend.users.models import Utilisateur, Notification
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

# ======================================================
#                    PAGES PUBLIQUES
# ======================================================

def home(request):
    return render(request, "frontend/home.html")

def contact(request):
    return render(request, "frontend/contact.html")

@login_required(login_url='login')
def objets_perdus(request):
    declarations = Declaration.objects.filter(objet__etat="perdu")
    return render(request, "frontend/objets/objets_perdus.html", {"declarations": declarations})


@login_required(login_url='login')
def objets_trouves(request):
    declarations = Declaration.objects.filter(
        objet__etat="retrouvé",
        reclame_par__isnull=True 
    ).order_by('-date_declaration')
    return render(request, "frontend/objets/objets_trouves.html", {"declarations": declarations})


def objet_detail(request, pk):
    objet = get_object_or_404(Objet, pk=pk)
    return render(request, "frontend/objets/objet_detail.html", {"objet": objet})

# ======================================================
#                  DASHBOARD POLICIER
# ======================================================

@login_required(login_url='login')

def dashboard_policier(request):
    user = request.user

    nb_objets_retrouves = Objet.objects.filter(etat='retrouvé').count()
    nb_objets_a_restituer = Objet.objects.filter(etat='à restituer').count()
    nb_restitutions = Restitution.objects.count()

    notifications = user.notifications.order_by('-date')[:5]  # 5 dernières notifications

    return render(request, "frontend/policier/dashboard_policier.html", {
        "nb_objets_retrouves": nb_objets_retrouves,
        "nb_objets_a_restituer": nb_objets_a_restituer,
        "nb_restitutions": nb_restitutions,
        "notifications": notifications,
        "year": timezone.now().year,
    })

def liste_objets_declares(request):
    objets = Objet.objects.all()
    return render(request, "frontend/policier/liste_objets_declares.html", {"objets": objets})

def maj_objet(request, pk):
    objet = get_object_or_404(Objet, pk=pk)
    if request.method == "POST":
        etat = request.POST.get("etat")
        objet.etat = etat
        objet.save()
        return redirect("liste_objets_declares")
    return render(request, "frontend/policier/maj_objet.html", {"objet": objet})

@login_required
def historique_restitutions(request):
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat', 'restitué_par'
    ).filter(objet__etat="restitué").order_by('-date_restitution', '-heure_restitution')

    return render(request, "frontend/policier/historique_restitutions.html", {"restitutions": restitutions})

@login_required
def supprimer_restitution(request, restitution_id):
    restitution = get_object_or_404(Restitution, id=restitution_id)
    if restitution.policier != request.user:
        messages.error(request, "Vous n’êtes pas autorisé à supprimer cette restitution.")
        return redirect("historique_restitutions")
    restitution.delete()
    messages.success(request, "La restitution a été supprimée avec succès.")
    return redirect("historique_restitutions")

@login_required
def objets_restitues(request):
    if request.user.role != "policier":
        messages.error(request, "⚠️ Accès réservé aux policiers.")
        return redirect("home")

    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat'
    ).order_by('-date_restitution')

    return render(request, "frontend/objets/objets_restitues.html", {"restitutions": restitutions})
@login_required
def objets_reclames(request):
    if request.user.role != "policier":
        messages.error(request, "⚠️ Accès réservé aux policiers.")
        return redirect("home")

    # Objets réclamés par les citoyens (Déclarations avec un objet trouvé mais non encore restitué)
    declarations = Declaration.objects.filter(
        objet__etat="retrouvé",
        reclame_par__isnull=False
    ).order_by('-date_declaration')

    # Vérifier les restitutions existantes pour désactiver le bouton si déjà planifié
    restitutions = Restitution.objects.filter(
        restitué_par__isnull=True
    )
    restitutions_dict = {r.objet.id: r for r in restitutions}

    return render(request, "frontend/objets/objets_reclames.html", {
        "declarations": declarations,
        "restitutions_dict": restitutions_dict,
    })

@login_required
def objets_retrouves_attente(request):
    if request.user.role != "policier":
        messages.error(request, "⚠️ Accès réservé aux policiers.")
        return redirect("home")

    restitutions = Restitution.objects.filter(
        restitué_par__isnull=True
    ).order_by('-date_restitution', '-heure_restitution')

    return render(request, "frontend/objets/objets_retrouves_attente.html", {
        "restitutions": restitutions
    })

@login_required
def planifier_restitution(request, objet_id, type_objet="declaration"):
    if request.user.role != "policier":
        messages.error(request, "⚠️ Accès réservé aux policiers.")
        return redirect("home")

    declaration = None

    if type_objet == "declaration":
        declaration = get_object_or_404(Declaration, id=objet_id)
        restitution, created = Restitution.objects.get_or_create(
            objet=declaration.objet,
            citoyen=declaration.reclame_par,
            defaults={"policier": request.user}
        )
    elif type_objet == "restitution":
        restitution = get_object_or_404(Restitution, id=objet_id)
    else:
        messages.error(request, "Type d'objet inconnu pour la restitution.")
        return redirect("objets_reclames")

    commissariats = Commissariat.objects.all()

    initial_data = {
        "date_restitution": restitution.date_restitution or None,
        "heure_restitution": restitution.heure_restitution or None,
        "commissariat": restitution.commissariat
    }

    if request.method == "POST":
        form = RestitutionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            restitution.policier = request.user
            restitution.date_restitution = cd["date_restitution"]
            restitution.heure_restitution = cd["heure_restitution"]
            restitution.commissariat = cd["commissariat"]
            restitution.save()

            destinataires = []
            if restitution.citoyen and restitution.citoyen.email:
                destinataires.append(restitution.citoyen.email)
            if request.user.email:
                destinataires.append(request.user.email)

            if destinataires:
                send_mail(
                    subject=f"[Restitution planifiée] {restitution.objet.nom}",
                    message=(
                        f"La restitution de l'objet '{restitution.objet.nom}' a été planifiée.\n"
                        f"📍 Commissariat : {restitution.commissariat.nom if restitution.commissariat else 'Non assigné'}\n"
                        f"📅 Date : {restitution.date_restitution}\n"
                        f"⏰ Heure : {restitution.heure_restitution}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=destinataires,
                    fail_silently=True
                )

            messages.success(
                request,
                f"La restitution de '{restitution.objet.nom}' a été planifiée ✅ et les notifications ont été envoyées."
            )
            return redirect("objets_reclames")
    else:
        form = RestitutionForm(initial=initial_data)

    return render(request, "frontend/policier/planifier_restitution.html", {
        "restitution": restitution,
        "declaration": declaration,  
        "form": form,
        "commissariats": commissariats,
        "type_objet": type_objet
    })


@login_required
def marquer_restitue(request, restitution_id):
    restitution = get_object_or_404(Restitution, id=restitution_id)

    if restitution.policier != request.user:
        messages.error(request, "Vous n’êtes pas autorisé à valider cette restitution.")
        return redirect("objets_reclames")

    objet = restitution.objet
    objet.etat = "restitué"
    objet.save()

    restitution.restitué_par = request.user

    try:
        declaration = Declaration.objects.get(objet=objet, citoyen=restitution.citoyen)
        declaration.trouve_par = request.user
        declaration.save()
    except Declaration.DoesNotExist:
        pass

    restitution.save()
    messages.success(request, f"L'objet '{objet.nom}' a été marqué comme restitué ✅.")
    return redirect("objets_reclames")

# ======================================================
#                 DASHBOARD ADMINISTRATEUR
# ======================================================


@login_required(login_url='login')
def dashboard_admin(request):
    # Compter les éléments dans la base de données
    nb_commissariats = Commissariat.objects.count()
    nb_utilisateurs = Utilisateur.objects.count()
    nb_objets = Objet.objects.count()

    context = {
        'nb_commissariats': nb_commissariats,
        'nb_utilisateurs': nb_utilisateurs,
        'nb_objets': nb_objets,
    }

    return render(request, "frontend/admin/dashboard_admin.html", context)

def gerer_commissariats(request):
    commissariats = Commissariat.objects.all()
    return render(request, "frontend/admin/gerer_commissariats.html", {"commissariats": commissariats})

def gerer_utilisateurs(request):
    return render(request, "frontend/admin/gerer_utilisateurs.html")

# Vérifie que seul un admin peut créer un autre admin
def is_admin(user):
    return user.is_authenticated and user.role == "admin"

@user_passes_test(is_admin)
def creer_administrateur(request):
    if request.method == "POST":
        form = AdministrateurCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Administrateur créé et mot de passe envoyé par email.")
            return redirect('dashboard_admin')  # page de redirection après création
    else:
        form = AdministrateurCreationForm()
    return render(request, "frontend/admin/creer_admin.html", {"form": form})


@login_required(login_url='login')
def voir_stats(request):
    nb_objets = Objet.objects.count()
    nb_restitutions = Restitution.objects.count()
    context = {
        "nb_objets": nb_objets,
        "nb_restitutions": nb_restitutions
    }
    return render(request, "frontend/admin/voir_stats.html", context)


@login_required(login_url='login')
def ajouter_commissariat(request):
    if request.user.role != 'admin':
        messages.error(request, "⛔ Vous n'avez pas l'autorisation d'ajouter un commissariat.")
        return redirect('home')

    form = CommissariatForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "✅ Commissariat ajouté avec succès.")
        return redirect('gerer_commissariats')
    elif request.method == 'POST':
        messages.error(request, "❌ Erreur lors de l'ajout du commissariat.")

    return render(request, 'frontend/admin/ajouter_commissariat.html', {'form': form})

def supprimer_objet(request, objet_id):
    objet = get_object_or_404(Objet, id=objet_id)
    if request.method == "POST":
        objet.delete()
        messages.success(request, "Objet supprimé avec succès.")
    return redirect('liste_objets_declares')

def creer_policier(request):
    form = PolicierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        policier = form.save(commit=False)
        policier.set_password(password)
        policier.save()

        send_mail(
            "Création de votre compte Policier",
            f"Bonjour {policier.first_name},\n\nVotre compte a été créé.\n"
            f"Identifiant : {policier.username}\nMot de passe : {password}\n\n"
            "Merci de vous connecter et de changer ce mot de passe.",
            settings.DEFAULT_FROM_EMAIL,
            [policier.email],
            fail_silently=False,
        )

        messages.success(request, "Policier créé et mot de passe envoyé par email ✅")
        return redirect("gerer_utilisateurs")

    return render(request, "frontend/admin/creer_policier.html", {"form": form})

# ======================================================
#                    ACTIONS CITOYEN
# ======================================================

@login_required
def je_le_trouve(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    if declaration.objet.etat == "perdu":
        declaration.objet.etat = "retrouvé"
        declaration.trouve_par = request.user
        declaration.objet.save()
        declaration.save()

        Restitution.objects.create(
            objet=declaration.objet,
            citoyen=declaration.citoyen
        )

        if declaration.citoyen and declaration.citoyen.email:
            send_mail(
                subject=f"[Objet Retrouvé] Votre objet {declaration.objet.nom} a été trouvé",
                message=(f"Bonjour {declaration.citoyen.username},\n\n"
                         "L'objet que vous avez déclaré perdu a été trouvé. "
                         "Un policier planifiera prochainement la restitution."),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=True
            )

        messages.success(request, "✅ L’objet a été marqué comme retrouvé et une restitution sera planifiée.")
    else:
        messages.warning(request, "⚠️ Cet objet est déjà retrouvé ou restitué.")

    return redirect("objets_reclames")

@login_required
def ca_m_appartient(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    if declaration.objet.etat == "retrouvé" and declaration.reclame_par is None:
        declaration.reclame_par = request.user
        declaration.save()

        if declaration.citoyen and declaration.citoyen.email:
            send_mail(
                subject=f"[Objet Trouvé] Votre objet '{declaration.objet.nom}' a été réclamé !",
                message=(f"Bonjour {declaration.citoyen.username},\n\n"
                         f"L'objet que vous avez trouvé a été réclamé par {request.user.username} ({request.user.email}).\n"
                         f"ID de la déclaration : {declaration.id}\n"
                         f"Consultez les détails ici : http://127.0.0.1:8000/objets/{declaration.id}/\n\n"
                         "Merci !"),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=False,
            )

        messages.success(request, f"Vous avez réclamé l'objet '{declaration.objet.nom}'.")
    else:
        messages.error(request, "Cet objet a déjà été réclamé ou n'est pas trouvé.")

    return redirect("objets_trouves")
