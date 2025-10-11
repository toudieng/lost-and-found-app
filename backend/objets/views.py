from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DeclarationForm
from .models import EtatObjet, Declaration, Objet

@login_required(login_url='login')
def declarer_objet(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            # Créer l'objet associé
            objet = Objet.objects.create(
                nom=form.cleaned_data['nom_objet'],
                description=form.cleaned_data.get('description', ''),
                etat=form.cleaned_data['etat'],
                image=form.cleaned_data.get('image', None)
            )

            # Créer la déclaration liée à l'utilisateur connecté
            declaration = Declaration.objects.create(
                objet=objet,
                citoyen=request.user,  # lier le citoyen (user)
                lieu=form.cleaned_data['lieu']
            )

            messages.success(request, "✅ Votre déclaration a été enregistrée avec succès.")

            # Redirection selon le type
            if objet.etat == EtatObjet.PERDU:
                return redirect('mes_objets_perdus')
            else:
                return redirect('mes_objets_trouves')
        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
