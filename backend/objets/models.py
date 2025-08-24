from django.db import models
from django.conf import settings
from backend.users.models import Commissariat

class Objet(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    etat = models.CharField(max_length=50, default="Non restitué")

    def __str__(self):
        return self.nom


class Declaration(models.Model):
    citoyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        null=True  
    )
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        null=True  
    )
    date_declaration = models.DateTimeField(auto_now_add=True)
    est_perdu = models.BooleanField(default=True)
    lieu = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # description optionnelle
    image = models.ImageField(upload_to='declarations/', blank=True, null=True)  # image optionnelle

    def __str__(self):
        return f"Déclaration de {self.citoyen} - {self.objet}"


class Restitution(models.Model):
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        null=True  
    )
    citoyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        null=True
    )
    policier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="policier_restitutions",
        limit_choices_to={'role': 'policier'},
        null=True
    )
    commissariat = models.ForeignKey(
        Commissariat,
        on_delete=models.CASCADE,
        null=True
    )
    date_restitution = models.DateField(auto_now_add=True)
    heure_restitution = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"Restitution {self.objet} à {self.citoyen}"
