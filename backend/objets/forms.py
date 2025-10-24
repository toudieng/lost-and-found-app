from django import forms
from django.utils import timezone
from .models import Declaration, Objet, EtatObjet
from backend.objets.models import Commissariat, Restitution




class DeclarationForm(forms.ModelForm):
    nom_objet = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'objet"}),
        label="Nom de l'objet",
        required=True
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows':3, 'placeholder': 'Description (facultative)'}),
        label="Description"
    )
    image = forms.ImageField(required=False, label="Photo (facultative)")

    # Champ pour l'état initial choisi par le déclarant
    etat_initial = forms.ChoiceField(
        choices=[(EtatObjet.PERDU, "Objet perdu"), (EtatObjet.TROUVE, "Objet trouvé")],
        widget=forms.RadioSelect(attrs={'class':'form-check-input'}),
        label="Type de déclaration",
        required=True
    )

    class Meta:
        model = Declaration
        fields = ['nom_objet', 'lieu', 'etat_initial', 'description', 'image']
        widgets = {
            'lieu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lieu où l’objet a été perdu ou trouvé'}),
        }

    def save(self, citoyen=None, commit=True):
        declaration = super().save(commit=False)

        if citoyen:
            declaration.citoyen = citoyen

        # Création ou mise à jour de l'objet lié
        nom_objet = self.cleaned_data.get('nom_objet')
        description = self.cleaned_data.get('description')
        image = self.cleaned_data.get('image')
        etat_initial = self.cleaned_data.get('etat_initial')

        if declaration.objet:
            objet = declaration.objet
            objet.nom = nom_objet
            objet.description = description
            objet.etat = etat_initial
            if image:
                objet.image = image
            objet.save()
        else:
            objet = Objet.objects.create(
                nom=nom_objet,
                description=description,
                etat=etat_initial,
                image=image
            )
            declaration.objet = objet

        declaration.etat_initial = etat_initial
        declaration.date_declaration = timezone.now()

        if commit:
            declaration.save()

        return declaration

class RestitutionForm(forms.ModelForm):
    class Meta:
        model = Restitution
        fields = ['citoyen', 'date_restitution', 'heure_restitution', 'commissariat']
        widgets = {
            'citoyen': forms.Select(attrs={'class': 'form-select'}),
            'date_restitution': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_restitution': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'commissariat': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'citoyen': 'Réclamant',
            'date_restitution': 'Date de restitution',
            'heure_restitution': 'Heure de restitution',
            'commissariat': 'Commissariat'
        }
