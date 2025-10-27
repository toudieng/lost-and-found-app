from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from backend.objets.models import Objet
from .forms import UtilisateurCreationForm, ProfilForm
from .models import Notification
# -------------------- AUTHENTIFICATION --------------------
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UtilisateurCreationForm  # ton formulaire personnalisé

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            # Redirection selon le rôle
            role = getattr(user, 'role', 'citoyen')  # rôle par défaut si non défini
            if role == 'admin':
                return redirect('dashboard_admin')
            elif role == 'policier':
                return redirect('dashboard_policier')
            else:
                return redirect('home')
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
            # Affichage des erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UtilisateurCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

# -------------------- DASHBOARDS --------------------

@login_required
def admin_dashboard(request):
    if not hasattr(request.user, "role") or request.user.role != "admin":
        messages.error(request, "Accès refusé : réservé aux administrateurs.")
        return redirect("home")
    total_objets = Objet.objects.count()
    objets_perdus = Objet.objects.filter(est_perdu=True).count()
    objets_trouves = Objet.objects.filter(est_perdu=False).count()
    context = {
        "total_objets": total_objets,
        "objets_perdus": objets_perdus,
        "objets_trouves": objets_trouves,
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
def profil_admin(request):
    return render(request, "frontend/admin/profil.html", {"user": request.user})

@login_required
def modifier_profil_admin(request):
    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profil mis à jour avec succès.")
            return redirect("profil_admin")
    else:
        form = ProfilForm(instance=user)
    return render(request, "frontend/admin/modifier_profil.html", {"form": form})

@login_required
def profil_police(request):
    return render(request, "frontend/policier/profil.html", {"user": request.user})

@login_required
def modifier_profil_police(request):
    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profil mis à jour avec succès.")
            return redirect("profil_police")
    else:
        form = ProfilForm(instance=user)
    return render(request, "frontend/policier/modifier_profil.html", {"form": form})

@login_required
def profil_citoyen(request):
    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Votre profil a été mis à jour.")
            return redirect('profil_citoyen')
    else:
        form = ProfilForm(instance=user)
    return render(request, 'frontend/citoyen/profil_citoyen.html', {'form': form})

@login_required
def modifier_profil_citoyen(request):
    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profil mis à jour avec succès.")
            return redirect("dashboard_citoyen")
    else:
        form = ProfilForm(instance=user)
    return render(request, "frontend/citoyen/modifier_profil_citoyen.html", {"form": form})

# -------------------- NOTIFICATIONS --------------------

@login_required
def some_view(request):
    Notification.objects.create(
        user=request.user,
        message="Un nouvel objet à restituer a été ajouté."
    )
    messages.success(request, "Notification créée.")
    return redirect("home")
