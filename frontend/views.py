from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import random, string
from backend.objets.models import Objet, Declaration, Restitution, Commissariat
from backend.users.forms import CommissariatForm, PolicierForm
from backend.objets.forms import RestitutionForm




# --- Pages publiques ---
def home(request):
    return render(request, "frontend/home.html")

def contact(request):
    return render(request, "frontend/contact.html")


@login_required(login_url='login')
def objets_perdus(request):
    # Récupère toutes les déclarations des objets perdus
    declarations = Declaration.objects.filter(objet__etat="perdu")
    return render(request, "frontend/objets/objets_perdus.html", {"declarations": declarations})

@login_required(login_url='login')
def objets_trouves(request):
    # Récupère toutes les déclarations des objets retrouvés
    declarations = Declaration.objects.filter(objet__etat="retrouvé")
    return render(request, "frontend/objets/objets_trouves.html", {"declarations": declarations})

def objet_detail(request, pk):
    objet = get_object_or_404(Objet, pk=pk)
    return render(request, "frontend/objets/objet_detail.html", {"objet": objet})


# --- Dashboard Policier ---
@login_required(login_url='login')
def dashboard_policier(request):
    return render(request, "frontend/policier/dashboard_policier.html")

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
    # On récupère toutes les restitutions, triées par date décroissante
    restitutions = Restitution.objects.select_related(
        'objet', 'citoyen', 'policier', 'commissariat'
    ).order_by('-date_restitution', '-heure_restitution')

    return render(
        request,
        "frontend/policier/historique_restitutions.html",
        {"restitutions": restitutions}
    )


from datetime import datetime


@login_required

def objets_reclames(request):
    if not request.user.role == "policier":
        messages.error(request, "⚠️ Accès réservé aux policiers.")
        return redirect("home")

    # Récupère uniquement les déclarations avec un objet et un ID valide
    declarations = Declaration.objects.filter(
        objet__isnull=False,
        id__isnull=False,
        reclame_par__isnull=False
    ).order_by('-date_declaration')

    return render(request, "frontend/objets/objets_reclames.html", {"declarations": declarations})



def objets_restitues(request):
    # Vérifie que l'utilisateur est policier
    if not request.user.role == "policier":
        messages.error(request, "⚠️ Accès réservé aux policiers.")
        return redirect("home")

    # Tous les objets déjà restitués
    restitutions = Restitution.objects.select_related('objet', 'citoyen', 'policier', 'commissariat').order_by('-date_restitution')

    return render(request, "frontend/objets/objets_restitues.html", {
        "restitutions": restitutions
    })

@login_required
def planifier_restitution(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    if request.method == "POST":
        form = RestitutionForm(request.POST)
        if form.is_valid():
            restitution = form.save(commit=False)
            restitution.objet = declaration.objet
            restitution.citoyen = declaration.reclame_par
            restitution.policier = request.user
            restitution.save()

            # Marquer l'objet comme restitué
            declaration.objet.etat = "restitué"
            declaration.objet.save()

            messages.success(request, f"La restitution de '{declaration.objet.nom}' a été planifiée !")
            return redirect("objets_reclames")
    else:
        form = RestitutionForm()

    return render(request, "frontend/policier/planifier_restitution.html", {"declaration": declaration, "form": form})


# --- Dashboard Administrateur ---

@login_required(login_url='login')
def dashboard_admin(request):
    return render(request, "frontend/admin/dashboard_admin.html")

def gerer_commissariats(request):
    commissariats = Commissariat.objects.all()
    return render(request, "frontend/admin/gerer_commissariats.html", {"commissariats": commissariats})

def gerer_utilisateurs(request):
    return render(request, "frontend/admin/gerer_utilisateurs.html")

def voir_stats(request):
    nb_objets = Objet.objects.count()
    nb_restitutions = Restitution.objects.count()
    return render(request, "frontend/admin/voir_stats.html", {
        "nb_objets": nb_objets,
        "nb_restitutions": nb_restitutions
    })

@login_required(login_url='login')
def ajouter_commissariat(request):
    if request.user.role != 'admin':
        messages.error(request, "⛔ Vous n'avez pas l'autorisation d'ajouter un commissariat.")
        return redirect('home')

    if request.method == 'POST':
        form = CommissariatForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Commissariat ajouté avec succès.")
            return redirect('gerer_commissariats')
        else:
            messages.error(request, "❌ Erreur lors de l'ajout du commissariat.")
    else:
        form = CommissariatForm()

    return render(request, 'frontend/ajouter_commissariat.html', {'form': form})

def supprimer_objet(request, objet_id):
    objet = get_object_or_404(Objet, id=objet_id)
    if request.method == "POST":
        objet.delete()
        messages.success(request, "Objet supprimé avec succès.")
    return redirect('liste_objets_declares')

def creer_policier(request):
    if request.method == "POST":
        form = PolicierForm(request.POST)
        if form.is_valid():
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
    else:
        form = PolicierForm()
    
    return render(request, "frontend/admin/creer_policier.html", {"form": form})


# --- Actions citoyen ---

@login_required
def je_le_trouve(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    if declaration.est_perdu:
        declaration.est_perdu = False
        declaration.trouve_par = request.user  # citoyen qui a trouvé
        declaration.save()

        if declaration.citoyen and declaration.citoyen.email:
            send_mail(
                subject=f"[Objet Perdu] Votre objet {declaration.objet.nom} a été retrouvé",
                message=f"Bonjour {declaration.citoyen.username},\n\nL'objet que vous avez déclaré perdu a été trouvé. Un policier planifiera la restitution.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=True,
            )

        messages.success(request, "Merci d'avoir signalé que vous avez trouvé cet objet !")
    else:
        messages.warning(request, "Cet objet a déjà été signalé comme trouvé.")

    return redirect("objets_trouves")
@login_required
def ca_m_appartient(request, declaration_id):
    declaration = get_object_or_404(Declaration, id=declaration_id)

    # Vérifie si l'objet a été trouvé
    if declaration.objet.etat == "retrouvé":
        declaration.reclame_par = request.user
        declaration.save()  # on ne change pas objet.etat

        # Notification par email au citoyen qui a trouvé l'objet
        if declaration.citoyen and declaration.citoyen.email:
            send_mail(
                subject=f"[Objet Trouvé] Votre objet '{declaration.objet.nom}' a été réclamé !",
                message=(
                    f"Bonjour {declaration.citoyen.username},\n\n"
                    f"L'objet que vous avez déclaré comme trouvé a été réclamé par {request.user.username} ({request.user.email}).\n"
                    f"ID de la déclaration : {declaration.id}\n"
                    f"Consultez les détails ici : http://127.0.0.1:8000/objets/{declaration.id}/\n\n"
                    "Merci !"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[declaration.citoyen.email],
                fail_silently=False,
            )

        messages.success(request, f"Vous avez réclamé l'objet '{declaration.objet.nom}'.")
    else:
        messages.error(request, "Cet objet n'est pas déclaré comme trouvé.")

    return redirect("objets_trouves")
