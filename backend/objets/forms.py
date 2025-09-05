from django import forms
from .models import Declaration, Objet


class DeclarationForm(forms.ModelForm):
    # Champ texte pour saisir le nom de l'objet (lié au modèle Objet)
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

    # Nouveau champ pour remplacer est_perdu
    etat = forms.ChoiceField(
        choices=[("perdu", "Objet perdu"), ("retrouvé", "Objet trouvé")],
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
                    'placeholder': "Lieu où l’objet a été perdu/trouvé"
                }
            ),
        }

    def save(self, commit=True, citoyen=None):
        """
        On surcharge save() :
        - crée un Objet à partir de nom_objet
        - l'associe à la Déclaration
        - enregistre le citoyen si fourni
        """
        objet = Objet.objects.create(
            nom=self.cleaned_data['nom_objet'],
            description=self.cleaned_data.get('description', ''),
            etat=self.cleaned_data['etat']  # utilise maintenant le champ etat
        )

        declaration = super().save(commit=False)
        declaration.objet = objet  # lien avec l’objet créé
        if citoyen:  # si on passe l’utilisateur connecté
            declaration.citoyen = citoyen
        if commit:
            objet.save()
            declaration.save()
        return declaration
