from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import UtilisateurCreationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from backend.objets.models import Objet
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UtilisateurCreationForm

def register_view(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Forcer le rôle "citoyen"
            user.role = "citoyen"
            user.save()
            
            messages.success(request, "Compte citoyen créé avec succès ! Vous pouvez vous connecter.")
            return redirect('login')
    else:
        form = UtilisateurCreationForm()

    return render(request, 'users/register.html', {'form': form})



@staff_member_required  # accessible seulement par les admins
def admin_dashboard(request):
    total_objets = Objet.objects.count()
    objets_perdus = Objet.objects.filter(est_perdu=True).count()
    objets_trouves = Objet.objects.filter(est_perdu=False).count()

    context = {
        "total_objets": total_objets,
        "objets_perdus": objets_perdus,
        "objets_trouves": objets_trouves,
    }
    return render(request, "frontend/admin_dashboard.html", context)
