#encoding:utf-8
from django import forms
from main.models import TipoUva
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator

class VinosAño(forms.Form):
    año = forms.IntegerField(label="Introduzca un año (entre 1950 y el año actual) ", 
                              widget=forms.TextInput, 
                              validators=[MinValueValidator(1950), MaxValueValidator(datetime.today().year)], 
                              required=True)
    
class VinosUva(forms.Form):
    uva = forms.ModelChoiceField(label="Seleccione un tipo de uva ",
                                 queryset=TipoUva.objects.all())