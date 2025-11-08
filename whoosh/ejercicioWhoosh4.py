import os
import shutil
import time
from datetime import datetime
from tkinter import *
from tkinter import messagebox
import urllib.request
from bs4 import BeautifulSoup
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, DATETIME, ID, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup, AndGroup
from whoosh import qparser, query

# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context



dirindex = "index-Whoosh4"

'''
SCRAPING CON BEAUTIFULSOUP
'''
# (Las fechas se pasan de un formato en español a datetime)
def extraer_datos():
    import locale
    locale.setlocale(locale.LC_TIME, "es_ES")
    
    res = []
    url_base = "https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    req_base = urllib.request.Request(url_base, headers=headers)
    f = urllib.request.urlopen(req_base)
    s = BeautifulSoup(f, 'lxml')
    urls_recetas = s.find("div", class_="clear padding-left-1").find_all("div", class_="resultado link")
    urls_recetas = [r.a['href'].strip() for r in urls_recetas]
    for url in urls_recetas:
        req_receta = urllib.request.Request(url, headers=headers)
        f2 = urllib.request.urlopen(req_receta)
        s2 = BeautifulSoup(f2, 'lxml')
        #Título
        titulo = s2.find("header", class_="header-post").find("h1", class_="titulo titulo--articulo").string.strip()
        print("DEBUG (extraer título) -- " + titulo)
        #Comensales
        comensales = s2.find("div", class_="recipe-info").find("div", class_="properties").find("span", class_="property comensales")
        if comensales:
            comensales = comensales.string.strip()
        else:
            comensales = s2.find("div", class_="recipe-info").find("div", class_="properties").find("span", class_="property unidades")
            comensales = comensales.string.strip() if comensales else "-"
        print("DEBUG (extraer comensales) -- " + comensales)
        #Autor
        autor = s2.find("div", class_="nombre_autor")
        autor = autor.a.string.strip() if autor else "-"
        print("DEBUG (extraer autor) -- " + autor)
        #Fecha de actualización
        fecha = s2.find("span", class_="date_publish")
        fecha = fecha.string.replace("Actualizado: ", "").strip() if fecha else "-"
        fecha = datetime.strptime(fecha, "%d %B %Y")
        print("DEBUG (extraer fecha) -- " + str(fecha))
        #Características adicionales
        caracteristicas = s2.find("div", class_="properties inline")
        if caracteristicas:
            caracteristicas = caracteristicas.text.replace("Características adicionales:","")
            caracteristicas = ",".join([c.strip() for c in caracteristicas.split(",")] )     
        else:
            caracteristicas = "-"
        print("DEBUG (extraer caracteristicas) -- " + caracteristicas)
        #Introducción
        intro = s2.find("div", class_="intro")
        intro = intro.find("p").text.strip() if intro else "-"
        print("DEBUG (extraer introducción) -- " + intro)
        res.append([titulo, comensales, autor, fecha, caracteristicas, intro])
    
    return res



'''
WHOOSH
'''
def crear_index():
    messagebox.showinfo("ADVERTENCIA","El proceso de carga llevará tiempo.")
    if  os.path.exists(dirindex):
        shutil.rmtree(dirindex)
    os.mkdir(dirindex)
    
    sch = Schema(titulo=TEXT(stored=True), comensales=TEXT(stored=True), autor=TEXT(stored=True),
                 fecha=DATETIME(stored=True), caracteristicas=KEYWORD(stored=True, commas=True), intro=TEXT(stored=True))
    ix = create_in(dirindex, schema=sch)
    writer = ix.writer()
    for r in extraer_datos():
        writer.add_document(titulo=r[0], comensales=r[1], autor=r[2], fecha=r[3], caracteristicas=r[4], intro=r[5])
    writer.commit()
    messagebox.showinfo("ÍNDICE CREADO", "Se han cargado " + str(ix.reader().doc_count()) + " documentos.")


# Listar todos los elementos del índice
def listar_todo():
    ix = open_dir(dirindex)
    try:
        with ix.searcher() as searcher:
            results = searcher.search(query.Every(), limit=None)
            listar_1(results)
    except Exception as e:
        messagebox.showerror("ERROR", f"Ha habido un error: {e}")

# Buscar EXACTAMENTE palabras en dos atributos (comillas)
def titulo_introduccion():
    def listar_recetas(event):
        myquery= '"'+str(entry.get()).strip()+'"'
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = MultifieldParser(["titulo", "intro"], ix.schema).parse(myquery)
                results = searcher.search(query, limit=3)
                listar_2(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
            
    v = Toplevel()
    label = Label(v, text="Introduzca un texto para buscar en el título o en la introducción: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_recetas)
    entry.pack(side=LEFT)

# Rango de fechas
def fechas():
    def listar_recetas(event):
        fecha_1 = str(entry.get()).split(" ")[0]
        fecha_2 = str(entry.get()).split(" ")[1]
        myquery = f"[{fecha_1} TO {fecha_2}]"
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("fecha", ix.schema).parse(myquery)
                results = searcher.search(query, limit=None)
                listar_1(results)
        except Exception as e:
            messagebox.showerror("ERROR", "Ha habido un error: formato de fechas incorrecto.")
            
    v = Toplevel()
    label = Label(v, text="Introduzca un rango de fechas (en formato AAAAMMDD AAAAMMDD): ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_recetas)
    entry.pack(side=LEFT)

# Filtrar con dos atributos, utilizando prefijos en la query para usar un valor distinto en cada atributo
def caracteristicas_titulo():
    def listar_recetas():
        myquery= 'caracteristicas:'+ '"'+str(entry.get())+'"' +' '+str(entry2.get())
        # el 'características' es un prefijo de campo.
        # Le dice al motor de búsqueda: "La palabra o frase que viene justo después,
        # búscala únicamente en el campo llamado caracteristicas"
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("titulo", ix.schema, group=AndGroup).parse(myquery)
                results = searcher.search(query, limit=None)
                listar_1(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    caracteristicas = set()
    ix = open_dir(dirindex)
    with ix.searcher() as searcher:
        results = searcher.search(query.Every(), limit=None)
        for i in results:
            caracteristicas.update(i['caracteristicas'].split(","))
    caracteristicas = list(caracteristicas)
    print(caracteristicas)
    
    v = Toplevel()
    label = Label(v, text="Selecciona una característica: ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(caracteristicas), state='readonly')
    entry.pack(side=LEFT)
    label2 = Label(v, text="Introduce para buscar en el título: ")
    label2.pack(side=LEFT)
    entry2 = Entry(v)
    entry2.pack(side=LEFT)
    bt = Button(v, text="Aceptar", command=listar_recetas)
    bt.pack(side=LEFT)
    

'''
TKINTER
'''   
def listar_1(results):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=200, yscrollcommand=sc.set)
    if len(results) == 0:
        lb.insert(END, "No se encontraron resultados.")
    else:
        for row in results:
            lb.insert(END, "")
            s = 'Receta: ' + row['titulo']
            lb.insert(END, s)
            s = '    ' + row['comensales']
            lb.insert(END, s)
            s = '    Autor: ' + row['autor']
            lb.insert(END, s)
            s = '    Fecha: ' + str(row['fecha'])
            lb.insert(END, s)
            s = '    Características: ' + row['caracteristicas']
            lb.insert(END, s)
            s = '    Introducción: ' + row['intro']
            lb.insert(END, s)
            lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
    
def listar_2(results):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=200, yscrollcommand=sc.set)
    if len(results) == 0:
        lb.insert(END, "No se encontraron resultados.")
    else:
        for row in results:
            lb.insert(END, "")
            s = 'Receta: ' + row['titulo']
            lb.insert(END, s)
            s = '    Introducción: ' + row['intro']
            lb.insert(END, s)
            
            lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)


def ventana_ppal():
    raiz = Tk()
    
    menu = Menu(raiz)
    
    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=crear_index)
    menudatos.add_command(label="Listar", command=listar_todo)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Título o introducción", command=titulo_introduccion)
    menubuscar.add_command(label="Fecha", command=fechas)
    menubuscar.add_command(label="Características y título", command=caracteristicas_titulo)
    menu.add_cascade(label="Buscar", menu=menubuscar)
    
    raiz.config(menu=menu)
    
    raiz.mainloop()


'''
MAIN
'''
if __name__ == "__main__":
    ventana_ppal()