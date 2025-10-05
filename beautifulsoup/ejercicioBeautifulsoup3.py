from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime
import re

# líneas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
    

def extraer_datos():
    res = []
    url = "https://zacatrus.es/juegos-de-mesa.html"
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
        if info:
            tematicas = info.find("div", class_="col label", string="Temática").find_next_sibling().text.strip()
            complejidad = info.find("div", class_="col label", string="Complejidad").find_next_sibling().text.strip()
        res.append([titulo,valoracion,precio,tematicas,complejidad])
    return res

def almacenar_db(lista):
    conn = sqlite3.connect('../generated/databases/juegos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS JUEGOS;")
    conn.execute('''CREATE TABLE JUEGOS
        (TITULO        TEXT        NOT NULL,
         VALORACION    INT         NOT NULL,
         PRECIO        DOUBLE      NOT NULL,
         TEMATICAS     TEXT        NOT NULL,
         COMPLEJIDAD   TEXT        NOT NULL);''')
    for juego in lista:
        conn.execute("INSERT INTO JUEGOS (TITULO, VALORACION, PRECIO, TEMATICAS, COMPLEJIDAD) VALUES (?,?,?,?,?)",
                     (juego[0], juego[1], juego[2], juego[3], juego[4]))
    conn.commit()
    
    cursor = conn.execute("SELECT COUNT(*) FROM JUEGOS;")
    messagebox.showinfo("Base de datos", "Base de datos creada correctamente.\nHay " + str(cursor.fetchone()[0]) + " registros.")
    
    conn.close
    
def cargar():
    respuesta = messagebox.askyesno("Confirmar", "¿Está seguro de que quiere recargar los datos?\nEsta operación puede ser lenta.")
    if (respuesta):
        d = extraer_datos()
        almacenar_db(d)
        
def listar1(cursor):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 200, yscrollcommand=sc.set)
    
    for row in cursor:
        lb.insert(END, "Título: " + row[0])
        lb.insert(END, "    Valoración: " + str(row[1]))
        lb.insert(END, "    Precio: " + str(row[2]))
        lb.insert(END, "    Temáticas: " + row[3])
        lb.insert(END, "    Complejidad: " + row[4])
        lb.insert(END, "___________________________________")
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
    
def listar2(cursor):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 200, yscrollcommand=sc.set)
    
    for row in cursor:
        lb.insert(END, "Título: " + row[0])
        lb.insert(END, "    Temáticas: " + row[1])
        lb.insert(END, "    Complejidad: " + row[2])
        lb.insert(END, "___________________________________")
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
        
def listar_todo():
    conn = sqlite3.connect('../generated/databases/juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT TITULO, VALORACION, PRECIO, TEMATICAS, COMPLEJIDAD FROM JUEGOS;")
    conn.close
    
    listar1(cursor)
    
def listar_mejores():
    conn = sqlite3.connect('../generated/databases/juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT TITULO, VALORACION, PRECIO, TEMATICAS, COMPLEJIDAD FROM JUEGOS WHERE VALORACION > ? ORDER BY VALORACION DESC;",(90,))
    conn.close
    
    listar1(cursor)

def buscar_tematica():
    def listar(event):
        conn = sqlite3.connect('../generated/databases/juegos.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT TITULO, TEMATICAS, COMPLEJIDAD FROM JUEGOS WHERE TEMATICAS LIKE '%" + str(entry.get()) + "%';")
        conn.close
        listar2(cursor)
        
    conn = sqlite3.connect('../generated/databases/juegos.db')
    conn.text_factory = str
    cursor_tematicas = conn.execute("SELECT TEMATICAS FROM JUEGOS;")
    tematicas = set()
    for row in cursor_tematicas:
        row = re.split(r',|y', row[0])
        l = [t.strip() for t in row]
        tematicas.update(l)
    
    v = Toplevel()
    label = Label(v, text = "Seleccione una temática: ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(tematicas), state='readonly')
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
def buscar_complejidad():
    def listar(event):
        conn = sqlite3.connect('../generated/databases/juegos.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT TITULO, TEMATICAS, COMPLEJIDAD FROM JUEGOS WHERE COMPLEJIDAD LIKE '%" + str(entry.get()) + "%';")
        conn.close
        listar2(cursor)
        
    conn = sqlite3.connect('../generated/databases/juegos.db')
    conn.text_factory = str
    cursor_complejidad = conn.execute("SELECT COMPLEJIDAD FROM JUEGOS;")
    tematicas = set()
    for row in cursor_complejidad:
        row = re.split(r',|y', row[0])
        c = [c.strip() for c in row]
        tematicas.update(c)
    
    v = Toplevel()
    label = Label(v, text = "Seleccione una complejidad: ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(tematicas), state='readonly')
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
        
    

def ventana_ppal():
    raiz = Tk()
    menu = Menu(raiz)
    
    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)
    
    #LISTAR
    menulistar = Menu(menu, tearoff=0)
    menulistar.add_command(label="Juegos", command=listar_todo)
    menulistar.add_command(label="Mejores juegos", command=listar_mejores)
    menu.add_cascade(label="Listar", menu=menulistar)
    
    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Buscar por temática", command=buscar_tematica)
    menubuscar.add_command(label="Buscar por complejidad", command=buscar_complejidad)
    menu.add_cascade(label="Buscar", menu=menubuscar)
    
    raiz.config(menu=menu)
    
    raiz.mainloop()
    
    
    
    
if __name__ == "__main__":
    ventana_ppal()
    