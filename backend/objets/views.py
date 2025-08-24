from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DeclarationForm
from .models import Objet


def declarer_objet(request):
    if request.method == "POST":
        form = DeclarationForm(request.POST)
        if form.is_valid():
            declaration = form.save(commit=False)
            declaration.citoyen = request.user 
            declaration.save()
            return redirect('mes_declarations')  
    else:
        form = DeclarationForm()

    return render(request, "objets/declaration_form.html", {"form": form})

def liste_objets(request):
    objets = Objet.objects.all()
    return render(request, "frontend/liste_objets.html", {"objets": objets})
