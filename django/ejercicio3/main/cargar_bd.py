from main.models import Ocupacion, Usuario, Categoria, Pelicula, Puntuacion

from datetime import datetime

path = 'data'

def cargar_ocupaciones():
    Ocupacion.objects.all().delete()

    file = open(f'{path}\\u.occupation', 'r')
    res = []
    i = 0
    for line in file:
        res.append(Ocupacion(nombre = line.strip()))
    
    Ocupacion.objects.bulk_create(res) # Se utiliza bulk_create para mejorar la eficiencia al insertar muchos registros

    file.close()

    return len(res)


def cargar_usuarios():
    Usuario.objects.all().delete()

    res = []
    dict = {} # Se crea un diccionario idUsuario:objeto Usuario para facilitar la carga de las puntuaciones posteriormente
    file = open(f'{path}\\u.user', 'r')
    for line in file:
        rip = line.strip().split('|')
        usuario = Usuario(idUsuario = int(rip[0].strip()), edad = int(rip[1].strip()), sexo = rip[2].strip(),
                          ocupacion = Ocupacion.objects.get(nombre = rip[3].strip()), codigo_postal = rip[4].strip())
        res.append(usuario)
        dict[usuario.idUsuario] = usuario
    
    Usuario.objects.bulk_create(res)

    file.close()

    return dict


def cargar_categorias():
    Categoria.objects.all().delete()

    res = []
    file = open(f'{path}\\u.genre', 'r')
    for line in file:
        rip = line.strip().split('|')
        res.append(Categoria(idCategoria = int(rip[1].strip()), nombre = rip[0].strip()))
    
    Categoria.objects.bulk_create(res)

    file.close()

    return len(res)


def cargar_peliculas():
    Pelicula.objects.all().delete()

    file = open(f'{path}\\u.item')
    for line in file:
        rip = line.strip().split('|')
        date = None if len(rip[2]) == 0 else datetime.strptime(rip[2], '%d-%b-%Y')
        peli = Pelicula(idPelicula = int(rip[0].strip()), titulo = rip[1].strip(), fecha_estreno=date, 
                            imdb_url = rip[4].strip())
        
        peli.save()

        categorias = []
        for i in range(5, len(rip)):
            if rip[i] == '1':
                _idCategoria = i-5
                categorias.append(Categoria.objects.get(idCategoria=_idCategoria))
        peli.categorias.set(categorias)

    file.close()

    # Se crea un diccionario idPelicula:objeto Pelicula para facilitar la carga de las puntuaciones posteriormente
    dict = {}
    for p in Pelicula.objects.all():
        dict[p.idPelicula] = p

    return dict

def cargar_puntuaciones(usuarios, peliculas):
    Puntuacion.objects.all().delete()

    res = []
    file = open(f'{path}\\u.data')
    for line in file:
        rip = line.strip().split('\t')
        res.append(Puntuacion(usuario = usuarios[int(rip[0].strip())], pelicula = peliculas[int(rip[1].strip())],
                              puntuacion = int(rip[2].strip())))
        
    file.close()
    
    Puntuacion.objects.bulk_create(res)

    return len(res)