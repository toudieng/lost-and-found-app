from django import forms
from .models import Declaration

class DeclarationForm(forms.ModelForm):
    objet = forms.CharField(
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

    class Meta:
        model = Declaration
        fields = ['objet', 'description', 'image', 'est_perdu', 'lieu']
        widgets = {
            'lieu': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': "Lieu où l’objet a été perdu/trouvé"
                }
            ),
            'est_perdu': forms.RadioSelect(
                choices=[(True, 'Objet perdu'), (False, 'Objet trouvé')]
            ),
        }
