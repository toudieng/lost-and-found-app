from django import forms
from backend.users.models import Commissariat
from .models import Declaration, Objet, EtatObjet


class DeclarationForm(forms.ModelForm):
    # Champ texte pour saisir le nom de l'objet
    nom_objet = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': "Nom de l'objet perdu ou trouvé"
            }
        ),
        label="Objet"
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'placeholder': "Description (facultative)",
                'rows': 3
            }
        ),
        label="Description"
    )

    image = forms.ImageField(
        required=False,
        label="Photo (facultative)"
    )

    # Champ pour indiquer si l’objet est perdu ou trouvé
    etat = forms.ChoiceField(
    choices=[
        (EtatObjet.PERDU, "Objet perdu"),
        (EtatObjet.RETROUVE, "Objet trouvé"),  # ✅ correction ici
    ],
    widget=forms.RadioSelect,
    label="Type de déclaration"
)


    class Meta:
        model = Declaration
        fields = ['lieu', 'etat', 'description', 'image']
        widgets = {
            'lieu': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': "Lieu où l’objet a été perdu ou trouvé"
                }
            ),
        }

    def save(self, commit=True, citoyen=None):
        """
        Surcharge de save() :
        - crée un Objet à partir de nom_objet
        - l’associe à la Déclaration
        - enregistre le citoyen si fourni
        """
        # Création de l'objet lié
        objet = Objet.objects.create(
            nom=self.cleaned_data['nom_objet'],
            description=self.cleaned_data.get('description', ''),
            etat=self.cleaned_data['etat']
        )

        # Création de la déclaration
        declaration = super().save(commit=False)
        declaration.objet = objet
        if citoyen:
            declaration.citoyen = citoyen

        if commit:
            objet.save()
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
