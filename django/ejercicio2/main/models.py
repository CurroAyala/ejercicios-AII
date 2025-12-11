from django.db import models

class Vino(models.Model):
    idVino = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    precio = models.FloatField(null=False, blank=False)
    denominacion = models.ForeignKey('DenominacionOrigen', on_delete=models.CASCADE, related_name='denominacion')
    tiposUva = models.ManyToManyField('TipoUva', related_name='TipoUva')
    
class DenominacionOrigen(models.Model):
    idDenominacion = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    pais = models.ForeignKey('Pais', on_delete=models.CASCADE, related_name='pais')

class Pais(models.Model):
    idPais = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False, blank=False)

class TipoUva(models.Model):
    idTipoUva = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.nombre