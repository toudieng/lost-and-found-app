from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Commissariat

# Formulaire pour créer un utilisateur
class UtilisateurCreationForm(UserCreationForm):
    telephone = forms.CharField(required=False)
    role = forms.ChoiceField(choices=Utilisateur.ROLE_CHOICES)

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'telephone', 'role', 'password1', 'password2']

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
