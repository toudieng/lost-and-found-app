from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from backend.users.models import Commissariat

# =========================#
# ⚙ ENUMS
# =========================
class EtatObjet(models.TextChoices):
    PERDU = "perdu", "Perdu"
    TROUVE = "trouve", "Trouvé"
    RECLAME = "reclame", "Réclamé"
    EN_ATTENTE = "en_attente", "En attente"
    RESTITUE = "restitue", "Restitué"


class StatutRestitution(models.TextChoices):
    PLANIFIEE = "planifiee", "Planifiée"
    EFFECTUEE = "effectuee", "Effectuée"


# =========================#
# 🎒 OBJET
# =========================
class Objet(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de l'objet")
    description = models.TextField(blank=True, null=True)
    etat = models.CharField(
        max_length=20,
        choices=EtatObjet.choices,
        default=EtatObjet.PERDU
    )
    image = models.ImageField(upload_to='objets/', blank=True, null=True)
    code_unique = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code_unique:
            # Génère un identifiant unique court
            self.code_unique = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.get_etat_display()})"


# =========================
# 📄 DECLARATION
# =========================
class Declaration(models.Model):
    TYPE_CHOICES = [
        ('perdu', 'Objet perdu'),
        ('trouve', 'Objet trouvé'),
    ]

    citoyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        null=True,
        verbose_name="Citoyen déclarant"
    )
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        null=True,
        related_name='declarations'
    )
    date_declaration = models.DateTimeField(default=timezone.now)
    lieu = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='declarations/', blank=True, null=True)

    trouve_par = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='objets_trouves',
        limit_choices_to={'role': 'citoyen'},
        verbose_name="Trouvé par"
    )
    reclame_par = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='objets_reclames',
        limit_choices_to={'role': 'citoyen'},
        verbose_name="Réclamé par"
    )

    etat_initial = models.CharField(max_length=20, choices=EtatObjet.choices)
    type_declaration = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.objet.nom if self.objet else 'Objet inconnu'} ({self.get_type_declaration_display()})"


# =========================
# 🔁 RESTITUTION
# =========================
class Restitution(models.Model):
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        related_name="restitutions",
        null=True
    )
    citoyen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        null=True,
        related_name="citoyen_restitutions"
    )
    policier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="policier_restitutions",
        limit_choices_to={'role': 'policier'},
        null=True
    )
    restitue_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="restitutions_effectuees",
        limit_choices_to={'role': 'policier'},
        null=True,
        blank=True
    )
    commissariat = models.ForeignKey(
        Commissariat,
        on_delete=models.CASCADE,
        null=True
    )
    date_restitution = models.DateField(default=timezone.now)
    heure_restitution = models.TimeField(default=timezone.now)
    statut = models.CharField(
        max_length=20,
        choices=StatutRestitution.choices,
        default=StatutRestitution.PLANIFIEE
    )

    class Meta:
        verbose_name = "Restitution"
        verbose_name_plural = "Restitutions"
        ordering = ['-date_restitution', '-heure_restitution']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Met à jour l'état de l'objet si la restitution est effectuée
        if self.objet and self.statut == StatutRestitution.EFFECTUEE:
            self.objet.etat = EtatObjet.RESTITUE
            self.objet.save()

    def __str__(self):
        return f"Restitution de {self.objet.nom if self.objet else 'Objet'}"
