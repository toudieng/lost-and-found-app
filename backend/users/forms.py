from django import forms # pyright: ignore[reportMissingModuleSource]
from django.contrib.auth.forms import UserCreationForm # pyright: ignore[reportMissingModuleSource]
from .models import Utilisateur, Commissariat

# Formulaire pour créer un utilisateur citoyen
class UtilisateurCreationForm(UserCreationForm):
    telephone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control input-xs'})
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'telephone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control input-xs'}),
            'email': forms.EmailInput(attrs={'class': 'form-control input-xs'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control input-xs'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control input-xs'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "citoyen"
        if commit:
            user.save()
        return user

# Formulaire pour ajouter un commissariat
class CommissariatForm(forms.ModelForm):
    class Meta:
        model = Commissariat
        fields = ['nom', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du commissariat'
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse du commissariat'
            }),
        }

# Formulaire pour créer un policier
class PolicierForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["email", "first_name", "last_name", "telephone", "commissariat"]
        widgets = {
            "email": forms.EmailInput(attrs={'class': 'form-control input-xs'}),
            "first_name": forms.TextInput(attrs={'class': 'form-control input-xs'}),
            "last_name": forms.TextInput(attrs={'class': 'form-control input-xs'}),
            "telephone": forms.TextInput(attrs={'class': 'form-control input-xs'}),
            "commissariat": forms.Select(attrs={'class': 'form-control input-xs'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "policier"
        if commit:
            user.save()
        return user
from django import forms
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from .models import Utilisateur

class AdministrateurCreationForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['email', 'first_name', 'last_name', 'telephone']  # ajout des noms

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'

        # Génération automatique d'un username valide (prenom.nom ou email)
        base_username = f"{self.cleaned_data['first_name']}.{self.cleaned_data['last_name']}".lower()
        username = ''.join(c for c in base_username if c.isalnum() or c in ('@','.','+','-','_'))
        user.username = username[:150]  # limite Django

        # Mot de passe aléatoire
        password = get_random_string(10)
        user.set_password(password)

        if commit:
            user.save()
            # Envoi du mot de passe par email
            send_mail(
                subject="Vos identifiants administrateur",
                message=f"Bonjour {user.first_name} {user.last_name},\n\n"
                        f"Votre compte administrateur a été créé.\n"
                        f"Email: {user.email}\nMot de passe: {password}\n\nMerci.",
                from_email="noreply@lostfound.com",
                recipient_list=[user.email],
                fail_silently=False,
            )
        return user

from django.core.validators import RegexValidator

class ProfilForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message="Seulement lettres, chiffres et caractères @/./+/-/_ sont autorisés."
            )
        ],
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Nom d'utilisateur",
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Adresse email"
        })
    )

    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Téléphone"
        })
    )

    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-control"
        })
    )

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "telephone", "photo"]
from django import forms
from .models import Utilisateur

class AdministrateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }
