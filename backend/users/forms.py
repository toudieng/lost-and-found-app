from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur

class UtilisateurCreationForm(UserCreationForm):
    telephone = forms.CharField(required=False)
    role = forms.ChoiceField(choices=Utilisateur.ROLE_CHOICES)

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'telephone', 'role', 'password1', 'password2']