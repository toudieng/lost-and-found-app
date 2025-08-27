from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DeclarationForm
from .models import Objet, Declaration


@login_required(login_url='login') 
def declarer_objet(request):
    """
    Vue permettant à un citoyen de déclarer un objet (perdu ou trouvé).
    """
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)
        if form.is_valid():
            # Récupérer ou créer l'objet selon le nom
            nom_objet = form.cleaned_data['nom_objet'].strip().lower()  
            objet_instance, created = Objet.objects.get_or_create(nom=nom_objet)

            # Créer la déclaration associée
            declaration = form.save(commit=False)
            declaration.objet = objet_instance
            declaration.citoyen = request.user  
            declaration.save()

            messages.success(request, "✅ Votre déclaration a été enregistrée avec succès.")
            return redirect('liste_objets')  
        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
