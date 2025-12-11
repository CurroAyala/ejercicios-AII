from django.shortcuts import render
from main.models import Vino, DenominacionOrigen, Pais, TipoUva
from main.forms import VinosAño, VinosUva

def inicio(request):
    return render(request, 'inicio.html')

def cargar_bd(request):
    from main.poblar_bd import poblar_paises, poblar_denominaciones, poblar_tipos_uva, poblar_vinos

    num_paises = poblar_paises()
    num_tipos_uva = poblar_tipos_uva()
    num_denominaciones = poblar_denominaciones()
    num_vinos = poblar_vinos()
    
    contexto = {
        'num_paises': num_paises,
        'num_denominaciones': num_denominaciones,
        'num_tipos_uva': num_tipos_uva,
        'num_vinos': num_vinos,
    }

    return render(request, 'cargar_bd.html', contexto)

def vinos_denominacion(request):
    denominaciones = DenominacionOrigen.objects.all()

    res = {}
    for denominacion in denominaciones:
        vinos = Vino.objects.filter(denominacion=denominacion)
        res[denominacion.nombre] = [(vino.nombre, vino.precio) for vino in vinos]
    
    contexto = {
        'vinos_denominacion': res
    }

    return render(request, 'vinos_denominacion.html', contexto)

def vinos_año(request):
    form = VinosAño()
    vinos = None
    año = ''

    if request.method == 'POST':
        form = VinosAño(request.POST)

        if form.is_valid():
            año = form.cleaned_data['año']
            vinos = Vino.objects.filter(nombre__contains=año)

    return render(request, 'vinos_año.html', {'form': form, 'vinos': vinos, 'año': año})

def vinos_uva(request):
    form = VinosUva()
    vinos = None

    if request.method == 'POST':
        form = VinosUva(request.POST)

        if form.is_valid():
            uva = TipoUva.objects.get(idTipoUva=form.cleaned_data['uva'].idTipoUva)
            vinos = Vino.objects.filter(tiposUva=uva)

    return render(request, 'vinos_uva.html', {'form': form, 'vinos': vinos})