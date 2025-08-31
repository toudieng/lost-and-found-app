from django.db import models
from django.conf import settings
from backend.users.models import Commissariat


class Objet(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de l'objet")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    etat = models.CharField(
        max_length=50,
        choices=[("perdu", "Perdu"), ("retrouvé", "Retrouvé"), ("restitué", "Restitué")],
        default="perdu",
        verbose_name="État"
    )
    # Optionnel : identifiant unique
    code_unique = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Code unique")

    def __str__(self):
        return self.nom



class Declaration(models.Model):
    citoyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        null=True,
        verbose_name="Citoyen"
    )
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Objet déclaré"
    )
    date_declaration = models.DateTimeField(auto_now_add=True, verbose_name="Date de déclaration")
    est_perdu = models.BooleanField(default=True, verbose_name="Est-ce un objet perdu ?")
    lieu = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lieu")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='declarations/', blank=True, null=True, verbose_name="Image")

    # Suivi de l'interaction pour notifications
    trouve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='objets_trouves',
        verbose_name="Trouvé par"
    )
    reclame_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='objets_reclames',
        verbose_name="Réclamé par"
    )

    def __str__(self):
        statut = "Perdu" if self.est_perdu else "Trouvé"
        return f"{statut} - {self.objet.nom if self.objet else 'Objet inconnu'}"


class Restitution(models.Model):
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Objet restitué"
    )
    citoyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        null=True,
        related_name="citoyen_restitutions",
        verbose_name="Citoyen"
    )
    policier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="policier_restitutions",
        limit_choices_to={'role': 'policier'},
        null=True,
        verbose_name="Policier"
    )
    commissariat = models.ForeignKey(
        Commissariat,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Commissariat"
    )
    date_restitution = models.DateField(auto_now_add=True, verbose_name="Date de restitution")
    heure_restitution = models.TimeField(auto_now_add=True, verbose_name="Heure de restitution")

    def __str__(self):
        return f"Restitution de {self.objet} à {self.citoyen}"
