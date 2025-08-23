from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import UtilisateurCreationForm
from django.contrib import messages

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


def register_view(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès ! Vous pouvez vous connecter.")
            return redirect('login')
    else:
        form = UtilisateurCreationForm()
    return render(request, 'users/register.html', {'form': form})
