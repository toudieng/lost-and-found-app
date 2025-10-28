from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from .models import Utilisateur, Commissariat, Message

# =========================
# 👤 Formulaire de création citoyen
# =========================
class UtilisateurCreationForm(UserCreationForm):
    telephone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'})
    )

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )
    password2 = forms.CharField(
        label="Confirmez le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez le mot de passe'})
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'telephone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d’utilisateur'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

# =========================
# 🏢 Formulaire de commissariat
# =========================
class CommissariatForm(forms.ModelForm):
    class Meta:
        model = Commissariat
        fields = ['nom', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du commissariat'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse du commissariat'}),
        }

# =========================
# 👮 Formulaire de création de policier
# =========================
class PolicierForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["email", "first_name", "last_name", "telephone", "commissariat"]
        widgets = {
            "email": forms.EmailInput(attrs={'class': 'form-control'}),
            "first_name": forms.TextInput(attrs={'class': 'form-control'}),
            "last_name": forms.TextInput(attrs={'class': 'form-control'}),
            "telephone": forms.TextInput(attrs={'class': 'form-control'}),
            "commissariat": forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "policier"
        if commit:
            user.save()
        return user

# =========================
# 🧑‍💼 Formulaire de création d’administrateur
# =========================
class AdministrateurCreationForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['email', 'first_name', 'last_name', 'telephone']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'

        # Génération automatique du username
        base_username = f"{self.cleaned_data['first_name']}.{self.cleaned_data['last_name']}".lower()
        username = ''.join(c for c in base_username if c.isalnum() or c in ('@', '.', '+', '-', '_'))
        user.username = username[:150]

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

# =========================
# 👤 Formulaire de profil utilisateur
# =========================
class ProfilForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message="Seulement lettres, chiffres et caractères @/./+/-/_ sont autorisés."
        )],
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom d'utilisateur"})
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Adresse email"})
    )

    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Téléphone"})
    )

    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "telephone", "photo"]

# =========================
# 🧾 Formulaire administrateur (modification)
# =========================
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

# =========================
# 📨 Formulaire de contact
# =========================
class ContactForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['nom', 'email', 'contenu']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre adresse e-mail'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Votre message...', 'rows': 4}),
        }
        labels = {'contenu': 'Message'}
