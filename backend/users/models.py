from django.db import models
from django.contrib.auth.models import AbstractUser


class Utilisateur(AbstractUser):
    # On rend 'email' unique et utilisé comme identifiant
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('policier', 'Policier'),
        ('citoyen', 'Citoyen'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='policier')
    commissariat = models.ForeignKey(
        'Commissariat',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='policiers'
    )

    # On définit 'email' comme identifiant principal
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"] 

    def __str__(self):
        return f"{self.email} ({self.role})"


class Commissariat(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)

    def __str__(self):
        return self.nom
