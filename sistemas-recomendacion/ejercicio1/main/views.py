from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings

from main.cargar_bd import cargar_ocupaciones, cargar_usuarios, cargar_categorias, cargar_peliculas, cargar_puntuaciones
from main.models import Usuario, Ocupacion, Pelicula, Puntuacion
from main.recommendations import invertir_diccionario, calcular_similitudes, obtener_recomendaciones, obtener_recomendaciones_item, calcular_mas_similares
from main.forms import UsuarioBusquedaForm, PeliculaBusquedaForm

import shelve


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


def cargar_diccionarios():
    '''
    Función que carga en un diccionario anidado todas las puntuaciones de usuarios a películas (Usuario:(Pelicula:Puntuacion)).
    También carga el diccionario inverso (Pelicula:(Usuario:Puntuacion)).
    '''
    prefs = {} # prefs quiere decir <preferencias>
    archivo = shelve.open('dataRS.dat') # Crea el archivo binario donde se guardarán las matrices (los diccionarios)
    puntuaciones = Puntuacion.objects.all()
    for p in puntuaciones:
        idUsuario = p.usuario.idUsuario
        idPelicula = p.pelicula.idPelicula
        puntuacion = p.puntuacion
        prefs.setdefault(idUsuario, {}) # Inicializa la clave idUsuario en el diccionario si no existe
        prefs[idUsuario][idPelicula] = puntuacion # Diccionario anidado (diccionario de diccionarios)
    archivo['UsuarioPeliculas'] = prefs # Guarda la primera matriz
    archivo['PeliculasUsuarios'] = invertir_diccionario(prefs) # Guarda la segunda matriz (la inversa de la primera)
    archivo['Similitudes'] = calcular_similitudes(prefs, n=10)


def cargar_rs(request):
    cargar_diccionarios()
    return HttpResponseRedirect('/rs_cargado')


def rs_cargado(request):
    return render(request, 'rs_cargado.html')


def recomendar_peliculas_RSusuario(request):
    form = UsuarioBusquedaForm()
    items = None
    usuario = None

    if request.method == 'POST':
        form = UsuarioBusquedaForm(request.POST)

        if form.is_valid():
            idUsuario = form.cleaned_data['idUsuario']
            usuario = get_object_or_404(Usuario, pk=idUsuario)
            archivo = shelve.open('dataRS.dat')
            prefs = archivo['UsuarioPeliculas']
            archivo.close()
            rankings = obtener_recomendaciones(prefs, int(idUsuario))
            recomendadas= rankings[:2]
            peliculas = []
            puntuaciones = []
            for re in recomendadas:
                peliculas.append(Pelicula.objects.get(pk=re[1]))
                puntuaciones.append(re[0])
            items= zip(peliculas,puntuaciones)
    
    return render(request, 'recomendar_peliculas_usuario.html', {'form':form, 'items':items, 'usuario':usuario, 'STATIC_URL':settings.STATIC_URL})


def recomendar_peliculas_RSitem(request):
    form = UsuarioBusquedaForm()
    items = None
    usuario = None

    if request.method == 'POST':
        form = UsuarioBusquedaForm(request.POST)

        if form.is_valid():
            idUsuario = form.cleaned_data['idUsuario']
            usuario = get_object_or_404(Usuario, pk=idUsuario)
            archivo = shelve.open('dataRS.dat')
            prefs = archivo['UsuarioPeliculas']
            similares = archivo['Similitudes']
            archivo.close()
            rankings = obtener_recomendaciones_item(prefs, similares, int(idUsuario))
            recomendadas= rankings[:3]
            peliculas = []
            puntuaciones = []
            for re in recomendadas:
                peliculas.append(Pelicula.objects.get(pk=re[1]))
                puntuaciones.append(re[0])
            items= zip(peliculas,puntuaciones)
    
    return render(request, 'recomendar_peliculas_usuario.html', {'form':form, 'items':items, 'usuario':usuario, 'STATIC_URL':settings.STATIC_URL})


def mostrar_peliculas_parecidas(request):
    form = PeliculaBusquedaForm()
    pelicula = None
    items = None

    if request.method == 'POST':
        form = PeliculaBusquedaForm(request.POST)

        if form.is_valid():
            idPelicula = form.cleaned_data['idPelicula']
            pelicula = get_object_or_404(Pelicula, pk=idPelicula)
            archivo = shelve.open('dataRS.dat')
            similares = archivo['PeliculasUsuarios']
            archivo.close()
            parecidas = calcular_mas_similares(similares, int(idPelicula), n=3)
            peliculas = []
            similaridad = []
            for p in parecidas:
                peliculas.append(Pelicula.objects.get(pk=p[1]))
                similaridad.append(p[0])
            items= zip(peliculas,similaridad)
    
    return render(request, 'peliculas_parecidas.html', {'form':form, 'pelicula': pelicula, 'items': items, 'STATIC_URL':settings.STATIC_URL})


def recomendar_usuarios_pelicula(request):
    formulario = PeliculaBusquedaForm()
    items = None
    pelicula = None
    
    if request.method=='POST':
        form = PeliculaBusquedaForm(request.POST)
        if form.is_valid():
            idPelicula = form.cleaned_data['idPelicula']
            pelicula = get_object_or_404(Pelicula, pk=idPelicula)
            archivo = shelve.open("dataRS.dat")
            Prefs = archivo['PeliculasUsuarios']
            archivo.close()
            rankings = obtener_recomendaciones(Prefs,int(idPelicula))
            recomendadas = rankings[:3]
            usuarios = []
            puntuaciones = []
            for re in recomendadas:
                usuarios.append(Usuario.objects.get(pk=re[1]))
                puntuaciones.append(re[0])
            items= zip(usuarios,puntuaciones)
            
    return render(request, 'recomendar_usuarios_pelicula.html', {'formulario':formulario, 'items':items, 'pelicula':pelicula, 'STATIC_URL':settings.STATIC_URL})


def mostrar_puntuaciones_usuario(request):
    formulario = UsuarioBusquedaForm()
    puntuaciones = None
    idusuario = None
    usuario = None
    
    if request.method=='POST':
        formulario = UsuarioBusquedaForm(request.POST)
        
        if formulario.is_valid():
            idusuario = formulario.cleaned_data['idUsuario']
            usuario = get_object_or_404(Usuario, pk=idusuario)
            puntuaciones = Puntuacion.objects.filter(usuario = Usuario.objects.get(pk=idusuario))
            
    return render(request, 'puntuaciones_usuario.html', {'formulario':formulario, 'puntuaciones':puntuaciones, 'usuario':usuario, 'STATIC_URL':settings.STATIC_URL})

