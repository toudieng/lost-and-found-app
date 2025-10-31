from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from backend.objets.models import Objet
from .forms import UtilisateurCreationForm, ProfilForm
from .models import Notification

# -------------------- AUTHENTIFICATION --------------------

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            # Redirection selon le rôle
            role = getattr(user, 'role', 'citoyen')  # rôle par défaut
            if role == 'admin':
                return redirect('dashboard_admin')
            elif role == 'policier':
                return redirect('dashboard_policier')
            else:
                return redirect('dashboard_citoyen')
        else:
            messages.error(request, "Adresse e-mail ou mot de passe incorrect.")
    
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')


def register_view(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'citoyen'  # rôle par défaut
            user.save()
            messages.success(request, "✅ Compte citoyen créé avec succès ! Vous pouvez maintenant vous connecter.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UtilisateurCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

# -------------------- DASHBOARDS --------------------

@login_required
def admin_dashboard(request):
    if getattr(request.user, "role", None) != "admin":
        messages.error(request, "Accès refusé : réservé aux administrateurs.")
        return redirect("dashboard_citoyen")
    
    context = {
        "total_objets": Objet.objects.count(),
        "objets_perdus": Objet.objects.filter(est_perdu=True).count(),
        "objets_trouves": Objet.objects.filter(est_perdu=False).count(),
    }
    return render(request, "frontend/admin_dashboard.html", context)


@login_required
def dashboard_citoyen(request):
    return render(request, "frontend/citoyen/dashboard.html")


@login_required
def dashboard_policier(request):
    return render(request, "frontend/policier/dashboard.html")

# -------------------- PROFILS --------------------

@login_required
def profil_view(request, template, form_redirect=None):
    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profil mis à jour avec succès.")
            if form_redirect:
                return redirect(form_redirect)
    else:
        form = ProfilForm(instance=user)
    return render(request, template, {"form": form, "user": user})


@login_required
def profil_admin(request):
    return profil_view(request, "frontend/admin/profil.html")


@login_required
def modifier_profil_admin(request):
    return profil_view(request, "frontend/admin/modifier_profil.html", form_redirect="profil_admin")


@login_required
def profil_police(request):
    return profil_view(request, "frontend/policier/profil.html")




@login_required
def modifier_profil_police(request):
    # Ajouter un message d'information
    messages.info(request, "Vous pouvez modifier votre profil ci-dessous.")

    # Appel de la vue profil avec template
    return profil_view(request, "frontend/policier/modifier_profil.html")


@login_required
def profil_citoyen(request):
    return profil_view(request, "frontend/citoyen/profil_citoyen.html")


from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required(login_url='login')  # Redirige vers login si non connecté
def modifier_profil_citoyen(request):
    # Message d'information à l'ouverture du formulaire
    messages.info(request, f"Bienvenue {request.user.username}, vous pouvez modifier votre profil.")
    
    return profil_view(
        request, 
        "frontend/citoyen/modifier_profil_citoyen.html", 
        form_redirect="dashboard_citoyen"
    )

# -------------------- NOTIFICATIONS --------------------

@login_required
def creer_notification(request, message="Un nouvel objet à restituer a été ajouté."):
    Notification.objects.create(user=request.user, message=message)
    messages.success(request, "Notification créée.")
    return redirect("home")
@login_required
def some_view(request):
    Notification.objects.create(
        user=request.user,
        message="Un nouvel objet à restituer a été ajouté."
    )
    messages.success(request, "Notification créée.")
    return redirect("home")
