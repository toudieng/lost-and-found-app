from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DeclarationForm
from .models import EtatObjet

@login_required(login_url='login')
def declarer_objet(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            # Sauvegarde via le formulaire, en liant le citoyen connecté
            declaration = form.save(citoyen=request.user)

            messages.success(request, "✅ Votre déclaration a été enregistrée avec succès.")

            # Redirection selon le type de déclaration
            if declaration.etat_initial == EtatObjet.PERDU:
                return redirect('mes_objets_perdus')
            else:
                return redirect('mes_objets_trouves')
        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
