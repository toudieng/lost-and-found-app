from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from backend.objets.models import Objet
from .forms import UtilisateurCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfilForm
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authentification par email
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            
            # Redirection selon le rôle
            if hasattr(user, "role"):
                if user.role == "admin":
                    return redirect("dashboard_admin")
                elif user.role == "policier":
                    return redirect("dashboard_policier")
                else:  # citoyen
                    return redirect("home")
            else:
                return redirect("home")
        else:
            messages.error(request, "Adresse e-mail ou mot de passe incorrect.")

    return render(request, 'users/login.html')
    

def logout_view(request):
    logout(request)
    return redirect('home')


def register_view(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Forcer le rôle "citoyen" par défaut
            user.role = "citoyen"
            user.save()

            messages.success(request, "Compte citoyen créé avec succès ! Vous pouvez vous connecter.")
            return redirect('login')
    else:
        form = UtilisateurCreationForm()

    return render(request, 'users/register.html', {'form': form})


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
def profil_admin(request):
    return render(request, "frontend/admin/profil.html", {"user": request.user})

@login_required
def modifier_profil_admin(request):
    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect("profil_admin")
    else:
        form = ProfilForm(instance=user)

    return render(request, "frontend/admin/modifier_profil.html", {"form": form})

@login_required
def profil_police(request):
    return render(request, "frontend/policier/profil.html")


@login_required
def modifier_profil_police(request):
    from.forms import ProfilForm  

    user = request.user
    if request.method == "POST":
        form = ProfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profil_police')
    else:
        form = ProfilForm(instance=user)

    return render(request, "frontend/policier/modifier_profil.html", {"form": form})
from .models import Notification

def some_view(request):
    Notification.objects.create(
        user=request.user,
        message="Un nouvel objet à restituer a été ajouté."
    )
