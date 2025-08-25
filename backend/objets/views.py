from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DeclarationForm
from .models import Objet, Declaration

@login_required(login_url='login') 
def declarer_objet(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            # Récupérer le nom de l'objet depuis le champ texte
            nom_objet = form.cleaned_data['objet'].strip()

            # Récupérer ou créer l'objet correspondant
            objet_instance, created = Objet.objects.get_or_create(nom=nom_objet)

            # Créer la déclaration sans l'enregistrer encore
            declaration = form.save(commit=False)
            declaration.objet = objet_instance  # assigner l'instance
            declaration.citoyen = request.user
            declaration.save()

            return redirect('home')
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
