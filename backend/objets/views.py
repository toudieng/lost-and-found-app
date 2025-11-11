from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import DeclarationForm
from .models import EtatObjet


@login_required(login_url='login')
def declarer_objet(request):
    """
    Vue permettant à un citoyen de déclarer un objet perdu ou trouvé.
    """
    if request.method == 'POST':
        form = DeclarationForm(request.POST, request.FILES)

        if form.is_valid():
            # Sauvegarde la déclaration avec le citoyen connecté
            declaration = form.save(citoyen=request.user)

            # Message de confirmation
            if declaration.etat_initial == EtatObjet.PERDU:
                messages.success(request, "✅ Votre déclaration d'objet perdu a été enregistrée avec succès.")
                return redirect('mes_objets_perdus')
            else:
                messages.success(request, "✅ Votre déclaration d'objet trouvé a été enregistrée avec succès.")
                return redirect('declarer_objet')

        else:
            messages.error(request, "⚠️ Erreur : vérifiez les informations saisies.")
    else:
        form = DeclarationForm()

    context = {
        'form': form,
        'current_year': timezone.now().year,
    }

    return render(request, 'frontend/declarer_objet.html', context)
