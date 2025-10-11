from django import forms
from backend.users.models import Commissariat
from .models import Declaration, Objet, EtatObjet


class DeclarationForm(forms.ModelForm):
    nom_objet = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'objet"}),
        label="Nom de l'objet",
        required=True
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (facultative)'}),
        label="Description"
    )

    image = forms.ImageField(
        required=False,
        label="Photo (facultative)"
    )

    etat = forms.ChoiceField(
        choices=[(EtatObjet.PERDU, "Objet perdu"), (EtatObjet.TROUVE, "Objet trouvé")],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Type de déclaration",
        required=True
    )

    class Meta:
        model = Declaration
        fields = ['nom_objet', 'lieu', 'etat', 'description', 'image']
        widgets = {
            'lieu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lieu où l’objet a été perdu ou trouvé'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Vérifie que l'instance a un objet valide avant d'accéder à ses attributs
        if getattr(self.instance, 'objet', None):
            objet = self.instance.objet
            self.fields['nom_objet'].initial = objet.nom or ''
            self.fields['etat'].initial = objet.etat or ''
            self.fields['description'].initial = objet.description or ''
            if objet.image:
                self.fields['image'].initial = objet.image


class RestitutionForm(forms.Form):
    date_restitution = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date de restitution"
    )
    heure_restitution = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Heure de restitution"
    )
    commissariat = forms.ModelChoiceField(
        queryset=Commissariat.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="-- Sélectionnez un commissariat --",
        label="Commissariat"
    )
