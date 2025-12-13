from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from datetime import datetime

class PeliculasAño(forms.Form):
    año = forms.IntegerField(label='Introduzca un año',
                             widget=forms.NumberInput(),
                             validators=[MinValueValidator(1900), MaxValueValidator(datetime.today().year)],
                             required=True)
    
class PeliculasUsuario(forms.Form):
    idUsuario = forms.IntegerField(label='Introduzca el id de un usuario',
                                   widget=forms.NumberInput(),
                                   validators=[MinValueValidator(1)],
                                   required=True)