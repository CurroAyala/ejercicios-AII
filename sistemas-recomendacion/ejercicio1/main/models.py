from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Ocupacion(models.Model):
    nombre = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    idUsuario = models.IntegerField(primary_key=True, null=False, blank=False)
    edad = models.IntegerField(MinValueValidator(0), null=False, blank=False)
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=False,blank=False)
    ocupacion = models.ForeignKey('Ocupacion', on_delete=models.CASCADE, related_name='ocupacion')
    codigo_postal = models.CharField(max_length=10, null=False, blank=False)

    def __str__(self):
        return str(self.idUsuario)


class Categoria(models.Model):
    idCategoria = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Pelicula(models.Model):
    idPelicula = models.IntegerField(primary_key=True)
    titulo = models.CharField(max_length=200)
    fecha_estreno = models.DateField(null=True, blank=True)
    imdb_url = models.URLField()
    categorias = models.ManyToManyField('Categoria', related_name='categoria')

    def __str__(self):
        return self.titulo


class Puntuacion(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='usuario')
    pelicula = models.ForeignKey('Pelicula', on_delete=models.CASCADE, related_name='pelicula')
    puntuacion = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __str__(self):
        return f'{self.usuario} - {self.pelicula} : {self.puntuacion}'