from django.db import models

class Partido(models.Model):
    local = models.ForeignKey('Equipo', on_delete=models.CASCADE, related_name='partidos_local')
    visitante = models.ForeignKey('Equipo', on_delete=models.CASCADE, related_name='partidos_visitante')
    goles_local = models.IntegerField(default=0, null=False, blank=False)
    goles_visitante = models.IntegerField(default=0, null=False, blank=False)
    jornada = models.ForeignKey('Jornada', on_delete=models.CASCADE, related_name='partidos')

    def __str__(self):
        return self.local.nombre + " vs " + self.visitante.nombre + " (" + str(self.goles_local) + "-" + str(self.goles_visitante) + ")"
    
class Equipo(models.Model):
    nombre = models.CharField(max_length=100, null=False, blank=False)
    fundacion = models.IntegerField(null=True, blank=True)
    estadio = models.CharField(max_length=100, null=True, blank=True)
    aforo = models.IntegerField(null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return self.nombre
    
class Jornada(models.Model):
    numero = models.IntegerField(default=1, null=False, blank=False)
    fecha = models.CharField(max_length=100, null=True, blank=True)
    temporada = models.ForeignKey('Temporada', on_delete=models.CASCADE, related_name='jornadas')

    def __str__(self):
        return "Jornada " + str(self.numero) + " - " + str(self.temporada.anyo) + "/" + str(self.temporada.anyo + 1)
    
class Temporada(models.Model):
    anyo = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return str(self.anyo) + "/" + str(self.anyo + 1)
    

