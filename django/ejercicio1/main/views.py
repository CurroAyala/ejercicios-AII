from django.shortcuts import render, redirect

from main.models import Temporada, Equipo, Jornada, Partido

# Cargar los datos desde la web a la base de datos
def cargar(request):
    from main import populateDB
    if populateDB.populateDatabase():
        tem = Temporada.objects.all().count()
        equ = Equipo.objects.all().count()
        jor = Jornada.objects.all().count()
        par = Partido.objects.all().count()
        informacion="Datos cargados correctamente" + "\n\n" + "Temporadas: " + str(tem) + " ; " + "Jornadas: " + str(jor) + " ; " + "Partidos: " + str(par) + " ; " + "Equipos: " + str(equ)
    else:
        informacion="ERROR en la carga de datos"    
    return render(request, 'carga.html', {'inf':informacion})
        
def inicio(request):
    temporadas = Temporada.objects.all()
    return render(request,'inicio.html', {'temporadas': temporadas, 'num_temporadas': temporadas.count()})

def ult_temporada(request):
    info = {}
    temporada = Temporada.objects.latest('anyo')
    jornadas = Jornada.objects.filter(temporada=temporada).order_by('numero')
    for jornada in jornadas:
        partidos = Partido.objects.filter(jornada=jornada).order_by('id')
        info[jornada] = partidos
    return render(request, 'ult_temporada.html', {'temporada': temporada, 'info': info})

def equipos(request):
    equipos = Equipo.objects.all().order_by('nombre')
    equipos = [e.nombre for e in equipos]
    return render(request, 'equipos.html', {'equipos': equipos})

def equipo(request, equipo_nombre):
    equipo = Equipo.objects.get(nombre=equipo_nombre)
    fundacion = equipo.fundacion
    estadio = equipo.estadio
    aforo = equipo.aforo
    direccion = equipo.direccion
    return render(request, 'equipo.html', {'equipo_nombre': equipo_nombre, 'fundacion': fundacion, 'estadio': estadio, 'aforo': aforo, 'direccion': direccion})

def estadios_aforo(request):
    equipos = Equipo.objects.all().order_by('aforo').reverse()
    equipos = equipos[:5]
    return render(request, 'estadios_aforo.html', {'equipos': equipos})
