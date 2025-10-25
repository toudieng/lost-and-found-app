from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from backend.users.models import Commissariat

# --- ENUMS ---
class EtatObjet(models.TextChoices):
    PERDU = "perdu", "Perdu"
    TROUVE = "trouvé", "Trouvé"
    RECLAME = "reclamé", "Réclamé"
    EN_ATTENTE = "en_attente", "En attente"
    RESTITUE = "restitue", "Restitué"

class StatutRestitution(models.TextChoices):
    PLANIFIEE = "planifiee", "Planifiée"
    EFFECTUEE = "effectuee", "Effectuée"

# --- OBJET ---
class Objet(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom de l'objet")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    etat = models.CharField(
        max_length=20,
        choices=EtatObjet.choices,
        default=EtatObjet.PERDU,
        verbose_name="État"
    )
    image = models.ImageField(
        upload_to='objets/',
        blank=True,
        null=True,
        verbose_name="Image de l'objet"
    )
    code_unique = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Code unique"
    )

    def save(self, *args, **kwargs):
        if not self.code_unique:
            self.code_unique = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.get_etat_display()})"

# --- DECLARATION ---


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
    related_name='declarations_trouvees',  # ✅ ajout ici
    verbose_name="Objet déclaré"
)


    date_declaration = models.DateTimeField(default=timezone.now, verbose_name="Date de déclaration")
    lieu = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lieu")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='declarations/', blank=True, null=True, verbose_name="Image")

    # --- Relations avec les citoyens ---
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

    # --- État initial de la déclaration ---
    etat_initial = models.CharField(
        max_length=20,
        choices=EtatObjet.choices,
        verbose_name="État initial"
    )

    # --- Nouveau champ pour clarifier le type de déclaration ---
    TYPE_CHOICES = [
        ('perdu', 'Objet perdu'),
        ('trouve', 'Objet trouvé'),
    ]
    type_declaration = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Type de déclaration"
    )

    def __str__(self):
        return f"Déclaration - {self.objet.nom if self.objet else 'Objet inconnu'}"

    def premier_reclamant(self):
        """Retourne le premier réclamant ou None si aucun"""
        return self.reclame_par.first() if self.reclame_par.exists() else None

    def save(self, *args, **kwargs):
        """Assure la cohérence entre le type de déclaration et l'état initial"""
        if not self.etat_initial:
            if self.type_declaration == 'perdu':
                self.etat_initial = EtatObjet.PERDU
                if self.objet:
                    self.objet.etat = EtatObjet.PERDU
            elif self.type_declaration == 'trouve':
                self.etat_initial = EtatObjet.TROUVE
                if self.objet:
                    self.objet.etat = EtatObjet.TROUVE

        if self.objet:
            self.objet.save()

        super().save(*args, **kwargs)

# --- RESTITUTION ---
class Restitution(models.Model):
    objet = models.ForeignKey(
        Objet,
        on_delete=models.CASCADE,
        null=True,
        related_name="restitutions",
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
        verbose_name="Policier planificateur"
    )
    restitue_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'policier'},
        related_name="restitutions_effectuees",
        verbose_name="Restitué par"
    )
    commissariat = models.ForeignKey(
        Commissariat,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Commissariat"
    )
    date_restitution = models.DateField(default=timezone.now, verbose_name="Date de restitution")
    heure_restitution = models.TimeField(default=timezone.now, verbose_name="Heure de restitution")
    statut = models.CharField(
        max_length=20,
        choices=StatutRestitution.choices,
        default=StatutRestitution.PLANIFIEE,
        verbose_name="Statut"
    )

    def save(self, *args, **kwargs):
        """Met à jour l'état de l'objet si restitution effectuée"""
        super().save(*args, **kwargs)
        if self.objet and self.statut == StatutRestitution.EFFECTUEE:
            self.objet.etat = EtatObjet.RESTITUE
            self.objet.save()

    def __str__(self):
        return f"Restitution de {self.objet.nom if self.objet else 'Objet inconnu'} à {self.citoyen.username if self.citoyen else 'Inconnu'}"

    class Meta:
        verbose_name = "Restitution"
        verbose_name_plural = "Restitutions"
        ordering = ['-date_restitution', '-heure_restitution']
