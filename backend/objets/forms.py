from django import forms
from backend.users.models import Commissariat
from .models import Declaration, Objet, EtatObjet



from django import forms
from django.utils import timezone
from .models import Declaration, Objet, EtatObjet


from django import forms
from django.utils import timezone
from .models import Declaration, Objet, EtatObjet

class DeclarationForm(forms.ModelForm):
    nom_objet = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom de l'objet"
        }),
        label="Nom de l'objet",
        required=True
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Description (facultative)'
        }),
        label="Description"
    )

    image = forms.ImageField(
        required=False,
        label="Photo (facultative)"
    )

    etat = forms.ChoiceField(
        choices=[
            (EtatObjet.PERDU, "Objet perdu"),
            (EtatObjet.TROUVE, "Objet trouvé")
        ],
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

        # Pré-remplissage des champs à partir de l'objet associé si existant
        objet = getattr(self.instance, 'objet', None)
        if objet:
            self.fields['nom_objet'].initial = objet.nom or ''
            self.fields['description'].initial = objet.description or ''
            self.fields['etat'].initial = objet.etat or ''

    def save(self, citoyen=None, commit=True):
        """
        Sauvegarde la déclaration avec création ou mise à jour de l'objet lié.
        """
        declaration = super().save(commit=False)

        # Lier le citoyen déclarant si fourni
        if citoyen:
            declaration.citoyen = citoyen

        # Récupérer les données nettoyées
        nom_objet = self.cleaned_data.get('nom_objet')
        description = self.cleaned_data.get('description')
        image = self.cleaned_data.get('image')
        etat = self.cleaned_data.get('etat')

        # Mise à jour ou création de l'objet associé
        if declaration.objet:
            objet = declaration.objet
            objet.nom = nom_objet
            objet.description = description
            objet.etat = etat
            if image:
                objet.image = image
            objet.save()
        else:
            objet = Objet.objects.create(
                nom=nom_objet,
                description=description,
                etat=etat,
                image=image
            )
            declaration.objet = objet

        declaration.date_declaration = timezone.now()

        if commit:
            declaration.save()

        return declaration



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
