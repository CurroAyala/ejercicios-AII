import os
import shutil
import time
import re
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
    
INDEX_DIR = "Index"


'''
SCRAPING CON BEAUTIFULSOUP
'''
def extraer_datos():
    import locale
    locale.setlocale(locale.LC_TIME, "es_ES")

    res = []
    url_base = "https://www.sensacine.com/noticias"
    for i in range(1,5):
        if i == 1:
            url = url_base
        else:
            url = url_base + "?page=" + str(i)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}) 
        f = urllib.request.urlopen(req) 
        s = BeautifulSoup(f, 'lxml')
        #noticias = []
        noticias = s.find("div", class_="gd-col-left").find_all("div", class_="news-card")
        noticias2 = s.find_all("div", class_="card news-card news-card-row mdl cf")
        noticias3 = s.find_all("div", class_="card news-card news-card-col mdl cf")
        for n in noticias:
            categoria = n.find("div", class_="meta-category")
            categoria = categoria.string.replace("Noticias - ", "").replace(" y ",",").replace(" en ", ",").strip() if categoria else "-"
            titulo = n.find("a",class_="meta-title-link")
            titulo = titulo.string.strip() if titulo else "-"
            enlace = n.find("h2", class_="meta-title")
            enlace = url_base + enlace.a['href'].strip() if enlace else "-"
            descripcion = n.find("div", class_="meta-body")
            descripcion = descripcion.string.strip() if descripcion else "-"
            fecha = n.find("div", class_="meta-date")
            fecha = datetime.strptime(fecha.string.strip(), "%A, %d de %B de %Y")      
            res.append([categoria, titulo, enlace, descripcion, fecha])
    return res


def almacenar_datos():
    schema = Schema(
        categoria=KEYWORD(stored=True, commas=True),
        titulo=TEXT(stored=True),
        enlace=ID(stored=True, unique=True),
        descripcion=TEXT(stored=True),
        fecha=DATETIME(stored=True)
    )

    if os.path.exists(INDEX_DIR):
        shutil.rmtree(INDEX_DIR)
    os.mkdir(INDEX_DIR)

    ix = create_in(INDEX_DIR, schema)
    writer = ix.writer()
    lista = extraer_datos()
    for cat, tit, link, desc, f in lista:
        writer.add_document(categoria=cat, titulo=tit, enlace=link, descripcion=desc, fecha=f)
    writer.commit()
    messagebox.showinfo("FIN", f"Se han indexado {len(lista)} noticias.")

def cargar():
    if os.path.exists(INDEX_DIR):
        r = messagebox.askyesno("Confirmar", "El índice ya existe. ¿Desea recrearlo?")
        if not r:
            return
    almacenar_datos()


def imprimir_lista(resultados):
    v = Toplevel()
    v.title("NOTICIAS DE SENSACINE")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for r in resultados:
        lb.insert(END, "Categoría: " + r["categoria"])
        lb.insert(END, "Título: " + r["titulo"])
        lb.insert(END, "Enlace: " + r["enlace"])
        lb.insert(END, "Fecha: " + r["fecha"].strftime("%d/%m/%Y"))
        lb.insert(END, "-----------------------------------------------")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

def listar_todo():
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        results = searcher.search(query.Every(), limit=None)
        imprimir_lista(results)


# =======================
# OPCIONES DE BÚSQUEDA
# =======================
def buscar_descripcion():
    def mostrar(event):
        ix = open_dir(INDEX_DIR)
        with ix.searcher() as searcher:
            q = QueryParser("descripcion", ix.schema).parse('"' + e.get() + '"')
            results = searcher.search(q, limit=10)
            imprimir_lista(results)

    v = Toplevel()
    Label(v, text="Frase en descripción: ").pack(side=LEFT)
    e = Entry(v, width=50)
    e.bind("<Return>", mostrar)
    e.pack(side=LEFT)


def buscar_categoria_titulo():
    def mostrar_lista():
        with ix.searcher() as searcher:
            entrada = '"' + str(sp.get()) + '"'
            query = QueryParser("titulo", ix.schema).parse('categoria:' + entrada + ' ' + str(en.get()))
            results = searcher.search(query, limit=None)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Búsqueda por Categoría y Título")
    l = Label(v, text="Seleccione categoría:")
    l.pack(side=LEFT)

    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        lista_categorias = [i.decode('utf-8') for i in searcher.lexicon('categoria')]

    sp = Spinbox(v, values=lista_categorias, state="readonly")
    sp.pack(side=LEFT)

    l1 = Label(v, text="Escriba palabras del título:")
    l1.pack(side=LEFT)
    en = Entry(v, width=40)
    en.pack(side=LEFT)

    b = Button(v, text="Buscar", command=mostrar_lista)
    b.pack(side=LEFT)


def buscar_titulo_y_descripcion():
    def mostrar():
        ix = open_dir(INDEX_DIR)
        with ix.searcher() as searcher:
            q1 = QueryParser("titulo", ix.schema).parse('"' + en1.get() + '"')
            q2 = QueryParser("descripcion", ix.schema).parse(en2.get())
            q_final = q1 & q2
            results = searcher.search(q_final, limit=None)
            imprimir_lista(results)

    v = Toplevel()
    v.title("Búsqueda por Título y Descripción")

    l1 = Label(v, text="Frase en el título:")
    l1.pack(side=LEFT)
    en1 = Entry(v, width=40)
    en1.pack(side=LEFT)

    l2 = Label(v, text="Palabras en la descripción:")
    l2.pack(side=LEFT)
    en2 = Entry(v, width=40)
    en2.pack(side=LEFT)

    b = Button(v, text="Buscar", command=mostrar)
    b.pack(side=LEFT)


def buscar_fecha():
    import locale
    locale.setlocale(locale.LC_TIME, "es_ES")
    
    def mostrar_lista(event):
        patron = re.match(
            r"^\s*(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\s+hasta\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\s*$",
            en.get(), re.I
        )
        if not patron:
            messagebox.showerror(
                "ERROR",
                "Formato incorrecto.\nEjemplo: 5 de Noviembre de 2025 hasta 6 de Noviembre de 2025"
            )
            return

        try:
            # Convertimos ambas fechas al formato datetime
            f1 = datetime.strptime(f"{patron.group(1)} {patron.group(2)} {patron.group(3)}", "%d %B %Y")
            f2 = datetime.strptime(f"{patron.group(4)} {patron.group(5)} {patron.group(6)}", "%d %B %Y")
        except:
            messagebox.showerror("ERROR", "No se ha podido interpretar alguna de las fechas.")
            return
        
        if f1 > f2:
            f1, f2 = f2, f1

        ix = open_dir(INDEX_DIR)
        with ix.searcher() as searcher:
            consulta = f"[{f1.strftime('%Y%m%d')} TO {f2.strftime('%Y%m%d')}]"
            q = QueryParser("fecha", ix.schema).parse(consulta)
            resultados = searcher.search(q, limit=None)
            imprimir_lista(resultados)

    v = Toplevel()
    v.title("Búsqueda por Rango de Fechas")

    l = Label(v, text="Introduzca el rango de fechas (5 de Noviembre de 2025 hasta 6 de Noviembre de 2025):")
    l.pack(side=LEFT)

    en = Entry(v, width=70)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)


def eliminar_por_descripcion():
    def mostrar(event):
        ix = open_dir(INDEX_DIR)
        with ix.searcher() as searcher:
            q = QueryParser("titulo", ix.schema).parse(e.get())
            results = [r for r in searcher.search(q) if r["descripcion"].strip() == "-"]
            if not results:
                messagebox.showinfo("Info", "No hay noticias con descripción vacía.")
                return
            imprimir_lista(results)
            if messagebox.askyesno("Confirmar", "¿Eliminar estas noticias?"):
                writer = ix.writer()
                for r in results:
                    writer.delete_by_term("enlace", r["enlace"])
                writer.commit()
                messagebox.showinfo("OK", "Noticias eliminadas.")

    v = Toplevel()
    Label(v, text="Palabras en título: ").pack(side=LEFT)
    e = Entry(v, width=40)
    e.bind("<Return>", mostrar)
    e.pack(side=LEFT)


def buscar_titulo_y_fecha():
    def mostrar():
        if not re.match(r"\d{8}", e2.get()):
            messagebox.showerror("ERROR", "Formato de fecha incorrecto (DDMMAAAA).")
            return
        ix = open_dir(INDEX_DIR)
        with ix.searcher() as searcher:
            q = MultifieldParser(["titulo", "fecha"], ix.schema).parse(e1.get())
            results = searcher.search(q, limit=5)
            imprimir_lista(results)

    v = Toplevel()
    Label(v, text="Frase en título: ").pack(side=LEFT)
    e1 = Entry(v, width=30)
    e1.pack(side=LEFT)
    Label(v, text="Fecha (DDMMAAAA): ").pack(side=LEFT)
    e2 = Entry(v, width=15)
    e2.pack(side=LEFT)
    Button(v, text="Buscar", command=mostrar).pack(side=LEFT)
    
    
def imprimir_lista_titulo_fecha(resultados):
    v = Toplevel()
    v.title("NOTICIAS DE SENSACINE")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=120, yscrollcommand=sc.set)
    for r in resultados:
        lb.insert(END, r["titulo"])
        lb.insert(END, "Fecha: " + r["fecha"].strftime("%d/%m/%Y"))
        lb.insert(END, "")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)



'''
VENTANA PRINCIPAL CON TKINTER
'''
def ventana_principal():
    def listar_todo():
        ix=open_dir(INDEX_DIR)
        with ix.searcher() as searcher:
            results = searcher.search(query.Every(),limit=None)
            imprimir_lista_titulo_fecha(results)
    
    raiz = Tk()
    raiz.geometry("200x120")
    raiz.title("Noticias SensaCine")
    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    #Para listar 
    menudatos.add_command(label="Listar", command=listar_todo)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Descripción", command=buscar_descripcion)
    menubuscar.add_command(label="Categoría y título", command=buscar_categoria_titulo)
    menubuscar.add_command(label="Título y Descripción", command=buscar_titulo_y_descripcion)
    menubuscar.add_command(label="Fecha", command=buscar_fecha)
    menubuscar.add_command(label="Eliminar por Descripción", command=eliminar_por_descripcion)
    menubuscar.add_command(label="Título y Fecha", command=buscar_titulo_y_fecha)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()


'''
MAIN
'''
if __name__ == "__main__":
    ventana_principal()