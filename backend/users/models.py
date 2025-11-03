from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings




# =========================
# 👤 UTILISATEUR
# =========================
class Utilisateur(AbstractUser):
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('policier', 'Policier'),
        ('citoyen', 'Citoyen'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    est_banni = models.BooleanField(default=False)

    commissariat = models.ForeignKey(
        'Commissariat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='policiers'
    )

    photo = models.ImageField(
        upload_to="photos_profil/",
        blank=True,
        null=True,
        default="photos_profil/default-avatar.png"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    
    def __str__(self):
     return f"{self.username} ({self.role})"


    
# =========================
# 🏢 COMMISSARIAT
# =========================

class Commissariat(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)

    def __str__(self):
        return self.nom



# =========================
# 🔔 NOTIFICATION
# =========================
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def _str_(self):
        return f"Notif → {self.user.username}"

# =========================
# 💬 MESSAGE (Contact citoyen)
# =========================
class Message(models.Model):
    expediteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages_citoyens"
    )
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    contenu = models.TextField(verbose_name="Message")
    date_envoi = models.DateTimeField(default=timezone.now)
    reponse = models.TextField(blank=True, null=True)
    date_reponse = models.DateTimeField(blank=True, null=True)
    lu = models.BooleanField(default=False)
    traite = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_envoi']
        verbose_name = "Message citoyen"
        verbose_name_plural = "Messages citoyens"

    def _str_(self):
        return f"{self.nom} ({self.email})"

