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
