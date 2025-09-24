from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DeclarationForm
from .models import Objet, Declaration,EtatObjet

@login_required(login_url='login')
def declarer_objet(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            nom_objet = form.cleaned_data['nom_objet'].strip()
            etat_form = form.cleaned_data['etat']  # "perdu" ou "trouve"
            description = form.cleaned_data.get('description', '')
            image = form.cleaned_data.get('image')

            # Déterminer l'état exact pour l'objet avec Enum
            if etat_form == EtatObjet.PERDU:
                etat_objet = EtatObjet.PERDU
            else:
                etat_objet = EtatObjet.TROUVE

            # Création de l'objet (sans image)
            objet_instance = Objet.objects.create(
                nom=nom_objet,
                etat=etat_objet,
                description=description
            )

            # Création de la déclaration
            declaration = form.save(commit=False)
            declaration.objet = objet_instance
            declaration.citoyen = request.user
            if image:
                declaration.image = image  # ✅ image stockée dans Declaration
            declaration.save()

            messages.success(request, "✅ Votre déclaration a été enregistrée avec succès.")

            # Redirection selon l'état
            if etat_objet == EtatObjet.PERDU:
                return redirect('objets_perdus')
            else:
                return redirect('objets_trouves')

        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
