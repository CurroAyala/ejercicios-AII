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
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from whoosh import qparser, query



dirindex = "index-Whoosh3"

'''
SCRAPING CON BEAUTIFULSOUP
''' 
def extraer_datos():
    res = []
    url_base = "https://www.elseptimoarte.net/estrenos/2024/"
    for i in range(1,4):
        if i == 1:
            url = url_base
        else:
            url = url_base+str(i)
        f = urllib.request.urlopen(url)
        s = BeautifulSoup(f, 'lxml')
        peliculas_html = s.find("ul", class_="elements").find_all("li")
        for peli in peliculas_html:
            url_peli = "https://www.elseptimoarte.net/" + peli.a['href'].strip()
            f2 = urllib.request.urlopen(url_peli)
            s2 = BeautifulSoup(f2, 'lxml')
            ficha = s2.find("main", class_="informativo").find("section", class_="highlight").find("dl")
            titulo = ficha.find("dt", string="Título").find_next_sibling("dd").string.strip()
            titulo_original = ficha.find("dt", string="Título original").find_next_sibling("dd").string.strip()
            fecha_españa = ficha.find("dt", string="Estreno en España").find_next_sibling("dd").string.strip()
            fecha_españa = datetime.strptime(fecha_españa, "%d/%m/%Y")
            pais = ficha.find("dt", string="País").find_next_sibling("dd").find_all("a")
            pais = [p.text.strip() for p in pais]
            pais = ", ".join(pais)
            generos = s2.find("div", class_="wrapper cinema1").find("p", class_="categorias").find_all("a")
            generos = [g.text.strip() for g in generos]
            generos = ", ".join(generos)
            directores = ficha.find("dt", string="Director").find_next_sibling("dd").find_all("a")
            directores = [d.text.strip() for d in directores]
            directores = ", ".join(directores)
            sinopsis = s2.find("main", class_="informativo").find("section", class_="highlight").find_next_sibling().find("div", class_="info").find("p")
            sinopsis = sinopsis.text.strip() if sinopsis else "-"
            res.append([titulo, titulo_original, fecha_españa, pais, generos, directores, sinopsis, url_peli])
                       
    return res


'''
WHOOSH
'''
def crear_index():
    messagebox.showinfo("ADVERTENCIA","El proceso de carga llevará tiempo.")
    if  os.path.exists(dirindex):
        shutil.rmtree(dirindex)
    os.mkdir(dirindex)
    
    sch = Schema(titulo=TEXT(stored=True), titulo_original=TEXT(stored=True), fecha=DATETIME(stored=True),
                 paises=KEYWORD(stored=True,commas=True), generos=KEYWORD(stored=True,commas=True), directores=KEYWORD(stored=True, commas=True),
                 sinopsis=TEXT(stored=True, phrase=False), url=ID(stored=True, unique=True))

    ix = create_in(dirindex, schema=sch)
    writer = ix.writer()
    for l in extraer_datos():
        writer.add_document(titulo=l[0], titulo_original=l[1], fecha=l[2], paises=l[3],
                            generos=l[4], directores=l[5], sinopsis=l[6], url=l[7])
    writer.commit()
    messagebox.showinfo("ÍNDICE CREADO", "Se han cargado " + str(ix.reader().doc_count()) + " documentos.")
 
    
# Buscar una o más palabras en dos atributos y seleccionar los 10 elementos más relevantes.
def titulo_sinopsis():
    def listar_peliculas(event):
        myquery=str(entry.get())
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = MultifieldParser(["titulo","sinopsis"], ix.schema, group=OrGroup).parse(myquery)
                results = searcher.search(query)
                listar_1(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    v = Toplevel()
    label = Label(v, text="Introduzca una o varias palabras para buscar en el título o sinopsis: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_peliculas)
    entry.pack(side=LEFT)
    
# Filtrar comparando un atributo (ver si contiene una entrada)
def genero():
    def listar_peliculas(event):
        myquery = '*'+str(entry.get()).strip()+'*'
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("generos", ix.schema).parse(myquery)
                results = searcher.search(query, limit=20)
                listar_2(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    generos = set()
    ix = open_dir(dirindex)
    with ix.searcher() as searcher:
        results = searcher.search(query.Every(), limit=None)
        for i in results:
            generos.update(i['generos'].split(","))
    generos = list(generos)
    
    v = Toplevel()
    label = Label(v, text="Selecciona un género: ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(generos), state='readonly')
    entry.bind("<Return>", listar_peliculas)
    entry.pack(side=LEFT)
    
# Filtrar viendo si un atributo datetime está en un rango
def fechas():
    def listar_peliculas(event):
        fecha_1 = str(entry.get()).split(" ")[0]
        fecha_2 = str(entry.get()).split(" ")[1]
        myquery = f"[{fecha_1} TO {fecha_2}]"
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("fecha", ix.schema).parse(myquery)
                results = searcher.search(query, limit=None)
                listar_2(results)
        except Exception as e:
            messagebox.showerror("ERROR", "Ha habido un error: formato de fechas incorrecto.")
            
    v = Toplevel()
    label = Label(v, text="Introduzca un rango de fechas (en formato AAAAMMDD AAAAMMDD): ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar_peliculas)
    entry.pack(side=LEFT)
    
# Modificar un atributo de todos los elementos que cumplan con un filtrado
def modificar():
    def mod(results):
        yesno = messagebox.askyesno(title="Confirmar", message="¿Está seguro de que quiere modificar las fechas de estreno de las películas?")
        ix = open_dir(dirindex)
        if yesno:
            writer = ix.writer()
            for r in results:
                writer.update_document(titulo=r['titulo'], titulo_original=r['titulo_original'],
                                       fecha=datetime.strptime(str(entry2.get()), "%Y%m%d"),
                                       paises=r['paises'], generos=r['generos'], directores=r['directores'],
                                       sinopsis=r['sinopsis'], url=r['url'])
            writer.commit()
    def mos():
        myquery=str(entry.get())
        ix = open_dir(dirindex)
        try:
            with ix.searcher() as searcher:
                query = QueryParser("titulo", ix.schema).parse(myquery)
                results = searcher.search(query)
                listar_3(results)
                mod(results)
        except Exception as e:
            messagebox.showerror("ERROR", f"Ha habido un error: {e}")
    
    v = Toplevel()
    label = Label(v, text="Introduce el título que quieras buscar (o una palabra que esté en él): ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.pack(side=LEFT)
    label2 = Label(v, text="Introduce la nueva fecha (en formato AAAAMMDD): ")
    label2.pack(side=LEFT)
    entry2 = Entry(v)
    entry2.pack(side=LEFT)
    bt = Button(v, text="Aceptar", command=mos)
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
            s = 'Título: ' + row['titulo']
            lb.insert(END, s)
            s = '    Título original: ' + str(row['titulo_original'])
            lb.insert(END, s)
            s = '    Directores: ' + row['directores']
            lb.insert(END, s)
            s = '    Fecha de estreno en España: ' + str(row['fecha'])
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
            s = 'Título: ' + row['titulo']
            lb.insert(END, s)
            s = '    Título original: ' + str(row['titulo_original'])
            lb.insert(END, s)
            s = '    Países: ' + row['paises']
            lb.insert(END, s)
            lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
    
def listar_3(results):
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
            s = '    Fecha de estreno en España: ' + str(row['fecha'])
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
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Título o sinopsis", command=titulo_sinopsis)
    menubuscar.add_command(label="Género", command=genero)
    menubuscar.add_command(label="Fecha", command=fechas)
    menubuscar.add_command(label="Modificar fecha", command=modificar)
    menu.add_cascade(label="Buscar", menu=menubuscar)
    
    raiz.config(menu=menu)
    
    raiz.mainloop()
    

'''
MAIN
'''
if __name__ == "__main__":
    ventana_ppal()