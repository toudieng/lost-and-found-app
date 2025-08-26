from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DeclarationForm
from .models import Objet, Declaration


@login_required(login_url='login') 
def declarer_objet(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            # Récupérer le nom de l'objet saisi
            nom_objet = form.cleaned_data['nom_objet'].strip()

            # Vérifier si l'objet existe déjà sinon le créer
            objet_instance, created = Objet.objects.get_or_create(nom=nom_objet)

            # Créer la déclaration mais ne pas la sauvegarder immédiatement
            declaration = form.save(commit=False)
            declaration.objet = objet_instance
            declaration.citoyen = request.user  # associer à l’utilisateur connecté
            declaration.save()

            messages.success(request, "Votre déclaration a été enregistrée avec succès ✅.")
            return redirect('liste_objets')  # tu peux mettre 'home' ou une page dédiée
        else:
            messages.error(request, "Une erreur est survenue. Vérifiez le formulaire.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
