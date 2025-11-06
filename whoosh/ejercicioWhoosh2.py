import os
import shutil
from tkinter import *
from tkinter import messagebox
import urllib.request
from bs4 import BeautifulSoup
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, DATETIME, ID, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import qparser, query


dirindex = "index-Whoosh2"

'''
SCRAPING CON BEAUTIFULSOUP
''' 
def extraer_datos():
    res = []
    url_base = "https://zacatrus.es/juegos-de-mesa.html"
    for i in range(1,4):
        if i == 1:
            url = url_base
        else:
            url = url_base+"?p="+str(i)
        f = urllib.request.urlopen(url)
        s = BeautifulSoup(f, 'lxml')
        lista_juegos = s.find("ol", class_="products list items product-items").find_all("li")
        for juego in lista_juegos:
            detalles = juego.find("div", class_="product details product-item-details")
            titulo = detalles.find("strong", class_="product name product-item-name").find("a").text.strip()
            valoracion = detalles.find("div", class_="rating-result")
            if valoracion:
                valoracion = int(valoracion.find("span").text.replace("%","").strip())
            else:
                valoracion = -1
            precio = float(
                detalles.find("div", class_="price-box price-final_price").find("span", class_="price").text
                .replace("\xa0€","").replace(',','.').strip())
            enlace = juego.find("div", class_="product-item-info").a['href'].strip()
            f2 = urllib.request.urlopen(enlace)
            s2 = BeautifulSoup(f2, 'lxml')
            info = s2.find("div", class_="trs")
            tematicas = "-"
            complejidad = "-"
            jugadores = "-"
            if info:
                tematicas = info.find("div", class_="col label", string="Temática")
                tematicas = tematicas.find_next_sibling().text.strip() if tematicas else "-"
                complejidad = info.find("div", class_="col label", string="Complejidad")
                complejidad = complejidad.find_next_sibling().text.strip() if complejidad else "-"
                jugadores = info.find("div", class_="trh").find("div", class_="tr").find_next_sibling()
                jugadores = jugadores.text.replace("Núm. jugadores","").strip() if jugadores else "-"
            descripcion = s2.find("div", class_="product attribute description")
            descripcion = descripcion.text.strip() if descripcion else "-"
            res.append([titulo,precio,tematicas,complejidad,jugadores,descripcion])
    return res


'''
WHOOSH
'''
# CREAR ESQUEMA E ÍNDICE
def crear_index():
    messagebox.showinfo("ADVERTENCIA","El proceso de carga llevará tiempo.")
    if  os.path.exists(dirindex):
        shutil.rmtree(dirindex)
    os.mkdir(dirindex)
    
    # Se crea el esquema, que sirve para definir la estructura de los documentos.
    sch = Schema(titulo=TEXT(stored=True), precio=NUMERIC(stored=True, numtype=float), tematicas=KEYWORD(stored=True),
                 complejidad=TEXT(stored=True), jugadores=KEYWORD(stored=True), detalles=TEXT(stored=True))
    # Se crea el índice, que agiliza las búsquedas
    ix = create_in(dirindex, schema=sch)
    # Se crea el writer, que sirve para añadir documentos al índice
    writer = ix.writer()
    for l in extraer_datos():
        writer.add_document(titulo=l[0], precio=l[1], tematicas=l[2], complejidad=l[3], jugadores=l[4], detalles=l[5])
    writer.commit()
    messagebox.showinfo("ÍNDICE CREADO", "Se han cargado " + str(ix.reader().doc_count()) + " documentos.")


def listar(results):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=200, yscrollcommand=sc.set)
    if len(results) == 0:
        lb.insert(END, "No se encontraron resultados.")
    else:
        for row in results:
            lb.insert(END, "")
            s = 'Título: ' + row['titulo']
            lb.insert(END, s)
            s = '    Precio: ' + str(row['precio'])
            lb.insert(END, s)
            s = '    Temática/s: ' + row['tematicas']
            lb.insert(END, s)
            s = '    Complejidad: ' + row['complejidad']
            lb.insert(END, s)
            s = '    Jugadores: ' + row['jugadores']
            lb.insert(END, s)
            lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
        
    
# Buscar una cadena de texto en un texto mayor
def detalles():
    def listar_juegos(event):
        myquery= '*'+str(entry.get()).strip()+'*'
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("detalles", ix.schema).parse(myquery)
                results = searcher.search(query)
                listar(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    v = Toplevel()
    label = Label(v, text="Introduzca un texto para buscar en los detalles: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_juegos)
    entry.pack(side=LEFT)
    
# Buscar en todos los elementos del índice
def tematicas():
    def listar_juegos(event):
        myquery = '*'+str(entry.get()).strip()+'*'
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("tematicas", ix.schema).parse(myquery)
                results = searcher.search(query)
                listar(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    tematicas = set()
    ix = open_dir(dirindex)
    with ix.searcher() as searcher:
        results = searcher.search(query.Every(), limit=None)
        for i in results:
            tematicas.update(i['tematicas'].split(","))
    tematicas = list(tematicas)
    
    v = Toplevel()
    label = Label(v, text="Selecciona una temática: ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(tematicas), state='readonly')
    entry.bind("<Return>", listar_juegos)
    entry.pack(side=LEFT)
        
# Filtrar comparando un atributo (precio menor a la entrada)
def precio():
    def listar_juegos(event):
        myquery = '{TO' + str(entry.get()) + ']'
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("precio", ix.schema).parse(myquery)
                results = searcher.search(query)
                listar(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    v = Toplevel()
    label = Label(v, text="Introduzca un precio: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_juegos)
    entry.pack(side=LEFT)

def jugadores():
    def listar_juegos(event):
        myquery = '*'+str(entry.get()).strip()+'*'
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("jugadores", ix.schema).parse(myquery)
                results = searcher.search(query)
                listar(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
            
    v = Toplevel()
    label = Label(v, text="Introduzca un número de jugadores: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_juegos)
    entry.pack(side=LEFT)
    
    

'''
    TKINTER
'''   
def ventana_ppal():
    raiz = Tk()
    
    menu = Menu(raiz)
    
    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=crear_index)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Detalles", command=detalles)
    menubuscar.add_command(label="Temáticas", command=tematicas)
    menubuscar.add_command(label="Precio", command=precio)
    menubuscar.add_command(label="Jugadores", command=jugadores)
    menu.add_cascade(label="Buscar", menu=menubuscar)
    
    raiz.config(menu=menu)
    
    raiz.mainloop()
    

if __name__ == "__main__":
    ventana_ppal()