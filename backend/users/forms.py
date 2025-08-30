from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Commissariat

# Formulaire pour créer un utilisateur

class UtilisateurCreationForm(UserCreationForm):
    telephone = forms.CharField(required=False)


    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'telephone', 'password1', 'password2']

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


#  Formulaire spécifique pour créer un policier
class PolicierForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["email", "first_name", "last_name", "telephone", "commissariat"]
    

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "policier"  
        if commit:
            user.save()
        return user
