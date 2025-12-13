from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings

from main.cargar_bd import cargar_ocupaciones, cargar_usuarios, cargar_categorias, cargar_peliculas, cargar_puntuaciones
from main.models import Usuario, Ocupacion, Pelicula, Puntuacion
from main.forms import PeliculasAño, PeliculasUsuario


def inicio(request):
    return render(request, 'inicio.html')


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return(HttpResponseRedirect('/cargar_bd'))
    formulario = AuthenticationForm()
    if request.method=='POST':
        formulario = AuthenticationForm(request.POST)
        usuario=request.POST['username']
        clave=request.POST['password']
        acceso=authenticate(username=usuario,password=clave)
        if acceso is not None:
            if acceso.is_active:
                login(request, acceso)
                return (HttpResponseRedirect('/cargar_bd'))
            else:
                return render(request, 'mensaje_error.html',{'error':"USUARIO NO ACTIVO",'STATIC_URL':settings.STATIC_URL})
        else:
            return render(request, 'mensaje_error.html',{'error':"USUARIO O CONTRASEÑA INCORRECTOS",'STATIC_URL':settings.STATIC_URL})
                     
    return render(request, 'iniciar_sesion.html', {'formulario':formulario, 'STATIC_URL':settings.STATIC_URL})


@login_required(login_url='/iniciar_sesion')
def cargar_bd(request):
    ocupaciones = cargar_ocupaciones()
    usuarios = cargar_usuarios()
    categorias = cargar_categorias()
    peliculas = cargar_peliculas()
    puntuaciones = cargar_puntuaciones(usuarios, peliculas)

    contexto = {
        'num_ocupaciones': ocupaciones,
        'num_usuarios': len(usuarios),
        'num_categorias': categorias,
        'num_peliculas': len(peliculas),
        'num_puntuaciones': puntuaciones
    }

    return render(request, 'cargar_bd.html', contexto)


def usuarios_ocupacion(request):
    ocupaciones = Ocupacion.objects.all()

    res = {}

    for o in ocupaciones:
        res[o] = Usuario.objects.filter(ocupacion=o)

    contexto = {
        'data': res
    }

    return render(request, 'usuarios_ocupacion.html', contexto)

def mejores_peliculas(request):
    res = []
    for peli in Pelicula.objects.all():
        puntuaciones = Puntuacion.objects.filter(pelicula=peli)
        num_puntuaciones = len(puntuaciones)
        if num_puntuaciones > 100:
            media = sum([p.puntuacion for p in puntuaciones])/num_puntuaciones
            res.append([peli.titulo,media,num_puntuaciones,peli.fecha_estreno])
    
    top50 = sorted(res, key=lambda x:x[1], reverse=True)[:50]

    contexto = {
        'data': top50
    }

    return render(request, 'mejores_peliculas.html', contexto)


def peliculas_año(request):
    form = PeliculasAño()
    peliculas = None
    año = None

    if request.method == 'POST':
        form = PeliculasAño(request.POST)

        if form.is_valid():
            año = form.cleaned_data['año']
            peliculas = Pelicula.objects.filter(fecha_estreno__year=año)

    return render(request, 'peliculas_año.html', {'form':form, 'peliculas':peliculas, 'año':año})


def peliculas_usuario(request):
    form = PeliculasUsuario()
    data = {}
    idUsuario = None

    if request.method == 'POST':
        form = PeliculasUsuario(request.POST)

        if form.is_valid():
            idUsuario = form.cleaned_data['idUsuario']
            puntuaciones = Puntuacion.objects.filter(usuario__idUsuario=idUsuario)
            for p in puntuaciones:
                data[p.pelicula] = p.puntuacion
    
    return render(request, 'peliculas_usuario.html', {'form':form, 'data':data, 'idUsuario':idUsuario})