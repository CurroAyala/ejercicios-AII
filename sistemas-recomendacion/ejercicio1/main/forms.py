from django import forms
   
class UsuarioBusquedaForm(forms.Form):
    idUsuario = forms.CharField(label="Id de usuario", widget=forms.TextInput, required=True)
    
class PeliculaBusquedaForm(forms.Form):
    idPelicula = forms.CharField(label="Id de película", widget=forms.TextInput, required=True)