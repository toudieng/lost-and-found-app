from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def liste_objets(request):
    return HttpResponse("Voici la liste des objets trouvés !")
