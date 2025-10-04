from django.db import models
from django.contrib.auth.models import AbstractUser


class Utilisateur(AbstractUser):
    # Identifiant principal
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('policier', 'Policier'),
        ('citoyen', 'Citoyen'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='policier')
    est_banni = models.BooleanField(default=False)

    commissariat = models.ForeignKey(
        'Commissariat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='policiers'
    )

    # 📸 Champ photo de profil
    photo = models.ImageField(
        upload_to="photos_profil/",
        blank=True,
        null=True,
        default="photos_profil/default-avatar.png"
    )

    # On définit 'email' comme identifiant principal
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.email}) - {self.role}"


class Commissariat(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)

    def __str__(self):
        return self.nom

from django.conf import settings 

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # fait référence à 'Utilisateur'
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)  # si la notification a été lue

    def __str__(self):
        return f"Notification pour {self.user.username} : {self.message[:30]}"
