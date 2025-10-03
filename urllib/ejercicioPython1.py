import urllib.request
import os.path
import re


# MÉTODO PARA CARGAR LA URL
def abrir_enlace (url, fichero): # url es el enlace que se va a abrir y fichero es el nombre del archivo donde se va a guardar
    try:
        if os.path.exists(fichero): # si el fichero existe
            recargar = input("La página ya ha sido cargada. ¿Desea recargar? (s/n):\n")
            if recargar == "s":
                urllib.request.urlretrieve(url, fichero) # se descarga el contenido de una url a un archivo local
            elif recargar != "n":
                print("Entrada incorrecta. No se recargará la página.")
        else: # si el fichero no existe
            urllib.request.urlretrieve(url, fichero)
        return fichero
    except:
        print("Error al conectarse a la página")
        return None

# MÉTODO PARA EXTRAER LA LISTA DE ITEMS
def extraer_lista(fichero):
    f = open(fichero, "r", encoding='utf-8') # se abre el fichero
    r = f.read() # se lee el fichero
    l1 = re.findall(r'<title>(.*)</title>\s*<link>(.*)</link>', r) # devuelve una lista de tuplas con las subcadenas que cumplen el patrón
    # Explicación patrón:
    #     la r al principio siginifica que la cadena es una raw string, se pone para poder usar \
    #     <title> busca literalmente esa cadena
    #     (.*) indica un grupo de captura, el punto significa cualquier caracter excepto salto de línea y el asterisco significa "cero o más veces"
    #     </title> busca literalmente esa cadena
    #     \s* el \s significa cualquier espacio en blanco y el asterisco "cero o más veces"
    # Para la etiqueta link es igual
    l2 = re.findall(r'<pubDate>(.*)</pubDate>', r)
    l = [list(e1) for e1 in l1] # convierte cada elemento de l1, que son tuplas, en una lista. Así se obtiene una lista de listas
    for e1, e2 in zip(l,l2): # la función zip junta dos listas elemento a elemento
        e1.append(e2)
    f.close()
    l = [x for x in l if len(x)==3]
    return l[1:]

# MÉTODO PARA IMPRIMIR LA LISTA DE ÍTEMS COMO PIDE EL ENUNCIADO
def imprimir_lista(l):
    for i in l:
        print("Título: ", str(i[0]))
        print("Link: ", i[1])
        fecha = formatear_fecha(i[2])
        print ("Fecha: {0:2s}/{1:2s}/{2:4s}\n".format(fecha[0],fecha[1],fecha[2])) 
        # se muestra la fecha en formato DD/MM/AAAA usando los valores de la tupla fecha
        
# MÉTODO AUXILIAR PARA FOMATEAR LAS FECHAS
def formatear_fecha(f):
    meses = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    fecha = re.match(r'.*(\d\d)\s*(.{3})\s*(\d{4}).*', f)
    # Explicación patrón:
    #     .* ignora cualquier cosa al principio. El punto es cualquier caracter, excepto salto de línea, y el asterisco "cero o más veces"
    #     (\d\d) captura dos dígitos cualesquiera (el día)
    #     \s* indica que puede haber espacios
    #     (.{3}) captura 3 caracteres cualesquiera (el mes)
    #     \s* indica que puede haber espacios
    #     (\d{4}) captura cuatro dígitos cualesquiera (el año)
    l = list(fecha.groups()) # convierte fecha en una lista
    l[1] = meses[l[1]] # sustituye el mes en letras por el número correspondiente
    return tuple(l) # tuple(l) convierte l en una tupla

# MÉTODO PARA BUSCAR NOTICIAS POR DÍA Y MES
def buscar_fecha(l):
    mes = input("Introduzca el mes (mm): ")
    dia = input("Introduzca el dia (dd): ")
    encontrado = False
    for i in l:
        f = formatear_fecha(i[2])
        if mes == f[1] and dia == f[0]:
            print ("Título:", str(i[0])) 
            print ("Link:", i[1]) 
            print ("Fecha: {0:2s}/{1:2s}/{2:4s}\n".format(f[0],f[1],f[2])) 
            encontrado = True
    if not encontrado:
        print ("No hay noticias para el", dia, "del", mes + ".") 

    


if __name__ == "__main__":
    fichero="noticias" # se le da nombre al fichero que se va a utilizar
    if abrir_enlace("https://www.abc.es/rss/2.0/espana/andalucia/", fichero): # se llama al método abrir_enlace, si funciona
        l = extraer_lista(fichero) # se llama al método extraer_lista y se guarda en l
    if l: # si existe l, se llama a las funciones imprimir_lista y buscar_fecha
        imprimir_lista(l)
        buscar_fecha(l)