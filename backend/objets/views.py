from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DeclarationForm
from .models import Objet


def declarer_objet(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            objet_nom = form.cleaned_data['objet']  # le nom de l'objet saisi
            # Vérifier si l'objet existe déjà ou le créer
            objet, created = Objet.objects.get_or_create(nom=objet_nom)
            
            declaration = form.save(commit=False)
            declaration.objet = objet
            declaration.citoyen = request.user
            declaration.save()
            return redirect('home')
    else:
        form = DeclarationForm()
    return render(request, 'frontend/declarer_objet.html', {'form': form})

def liste_objets(request):
    objets = Objet.objects.all()
    return render(request, "frontend/liste_objets.html", {"objets": objets})
