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
            nom_objet = form.cleaned_data['nom_objet'].strip()
            etat = form.cleaned_data['etat']  # "perdu" ou "retrouvé"

            # On crée toujours un nouvel objet, même si le nom existe déjà
            objet_instance = Objet.objects.create(
                nom=nom_objet,
                etat=etat
            )

            # Création de la déclaration
            declaration = form.save(commit=False)
            declaration.objet = objet_instance
            declaration.citoyen = request.user
            declaration.save()

            messages.success(request, "✅ Votre déclaration a été enregistrée avec succès.")

            # Redirection selon le type de l'objet
            if etat == "perdu":
                return redirect('objets_perdus')
            else:
                return redirect('objets_trouves')
        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
