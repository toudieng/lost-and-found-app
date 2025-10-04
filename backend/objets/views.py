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
            declaration = form.save(citoyen=request.user)
            
            # Sauvegarde l'image dans la déclaration uniquement
            if request.FILES.get('image'):
                declaration.image = request.FILES['image']
                declaration.save()

            messages.success(request, "✅ Votre déclaration a été enregistrée avec succès.")
            if declaration.objet.etat == EtatObjet.PERDU:
                return redirect('declarer_objet')
            else:
                return redirect('declarer_objet')
        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    return render(request, 'frontend/declarer_objet.html', {'form': form})
