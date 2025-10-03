#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime

# líneas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
    

# MÉTODO PARA EXTRAER ELEMENTOS DE LA URL
def extraer_elementos():
    lista = []
    url = "https://www.elseptimoarte.net/estrenos/2025/"
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f, "lxml")
    # el find() busca el primer bloque "ul" cuya clase sea "elements" (en este caso no hay más)
    # el find_all() busca todos los bloques "li"
    lista_peliculas = s.find("ul", class_="elements").find_all("li") # aquí hay una lista de "li" de cada película
    for pelicula in lista_peliculas:
        url_base = "https://www.elseptimoarte.net"
        url_pelicula = pelicula.a['href'] # hay que meterse en la página de cada película porque nos pide información que solo está ahí
        f = urllib.request.urlopen(url_base + url_pelicula)
        s = BeautifulSoup(f, "lxml")
        datos = s.find("main", class_="informativo").find("section", class_="highlight")
        titulo_original = datos.find("dt", string="Título original").find_next_sibling("dd").string.strip()
        titulo = ""
        # el find_next_sibling("dd") busca el siguiente elemento hermano (al <dt<) que sea un <dd>
        if (datos.find("dt", string="Título")): # si la película tiene título (traducido)
            titulo = datos.find("dt", string="Título").find_next_sibling("dd").string.strip()
        else: # si no tienen titulo, se pone el original
            titulo = titulo_original
        pais = datos.find("dt", string="País").find_next_sibling("dd").a.get_text().strip()
        fecha_estreno = datetime.strptime(datos.find("dt", string="Estreno en España").find_next_sibling("dd").string.strip(), '%d/%m/%Y')
        director = datos.find("dt", string="Director").find_next_sibling("dd").a.get_text().strip()
        generos = "".join(s.find("p", class_="categorias").stripped_strings) # devuelve un string de la union de cada string dentro de p        
        
        lista.append([titulo_original, titulo, pais, fecha_estreno, director, generos])
    
    return lista

# MÉTODO PARA ALMACENAR EN UNA BASE DE DATOS
def almacenar_bd(lista):
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS PELICULA;")
    conn.execute('''CREATE TABLE PELICULA
                    (TITULO TEXT            NOT NULL,
                     TITULO_ORIGINAL        TEXT NOT NULL,
                     PAIS                   TEXT NOT NULL,
                     FECHA         DATE,
                     DIRECTOR               TEXT NOT NULL,
                     GENEROS                TEXT NOT NULL);''')
    for e in lista:
        conn.execute("""INSERT INTO PELICULA (TITULO, TITULO_ORIGINAL, PAIS, FECHA, DIRECTOR, GENEROS) VALUES (?,?,?,?,?,?)""",
                     (e[1],e[0],e[2],e[3],e[4],e[5]))
    conn.commit()
    
    cursor = conn.execute("SELECT COUNT(*) FROM PELICULA")
    messagebox.showinfo("Base de datos", "Base de datos creada correctamente.\nHay " + str(cursor.fetchone()[0]) + " películas.")
    
    conn.close()
    
def cargar():
    respuesta = messagebox.askyesno("Confirmar", "¿Está seguro de que quiere recargar los datos?\nEsta operación puede ser lenta.")
    if (respuesta):
        l = extraer_elementos()
        almacenar_bd(l)
        
def listar_peliculas_1(cursor): # título, país y director
    v = Toplevel() # se crea una ventana secundaria sobre la ppal
    sc = Scrollbar(v) # se crea una barra de desplazamiento dentro de la ventana definida en v
    sc.pack(side=RIGHT, fill=Y) # acomoda la barra a la derecha y hace que ocupe toda la altura
    lb = Listbox(v, width = 200, yscrollcommand=sc.set) # se crea una lista, se define el ancho y se conecta con la barra 
    
    for row in cursor:
        s = "TÍTULO: " + row[0]
        lb.insert(END, s)
        s = "    PAÍS: " + str(row[1]) + " | DIRECTOR: " + row[2]
        lb.insert(END, s)
        s = "____________________________"
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH) # coloca la lista a la izquierda de la ventana y hace que se expanda vertical y horizontalmente
    sc.config(command=lb.yview) # conecta la lista con la barra de desplazamiento
    
def listar_peliculas_2(cursor): # título y fecha de estreno
    v = Toplevel() # se crea una ventana secundaria sobre la ppal
    sc = Scrollbar(v) # se crea una barra de desplazamiento dentro de la ventana definida en v
    sc.pack(side=RIGHT, fill=Y) # acomoda la barra a la derecha y hace que ocupe toda la altura
    lb = Listbox(v, width = 200, yscrollcommand=sc.set) # se crea una lista, se define el ancho y se conecta con la barra 
    
    for row in cursor:
        s = "TÍTULO: " + row[0]
        lb.insert(END, s)
        s = "    FECHA DE ESTRENO: " + str(row[1])
        lb.insert(END, s)
        s = "____________________________"
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH) # coloca la lista a la izquierda de la ventana y hace que se expanda vertical y horizontalmente
    sc.config(command=lb.yview) # conecta la lista con la barra de desplazamiento
        
def listar_todo(): # ejercicio 1.b
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT TITULO, PAIS, DIRECTOR FROM PELICULA")
    conn.close
    
    listar_peliculas_1(cursor)
    
def buscar_titulo():
    def listar(event):
        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT TITULO, PAIS, DIRECTOR FROM PELICULA WHERE TITULO LIKE '%" + str(entry.get()) + "%'")
        conn.close
        listar_peliculas_1(cursor)
        
    v = Toplevel() # se crea la ventana para introducir el texto
    label = Label(v, text = "Introduzca una cadena para busca: ") # se crea una etiqueta para la ventana
    label.pack(side=LEFT) # se empaqueta la etiqueta
    entry = Entry(v) # se crea una entrada asociada a la ventana
    entry.bind("<Return>", listar) # cuando se pulse la letra "Enter", se ejecutará la función listar
    entry.pack(side=LEFT) # se empaquieta la entrada       

def buscar_fecha():
    def listar(event):
        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str
        try:
            fecha = datetime.strptime(str(entry.get()), "%d-%m-%Y")
            cursor = conn.execute("SELECT TITULO, FECHA FROM PELICULA WHERE FECHA > ?", (fecha,))
            conn.close
        except:
            conn.close
            messagebox.showerror(title="Error", message="Error al formatear la fecha.\nFormato correcto: dd-mm-aaaa")
        listar_peliculas_2(cursor)
    v = Toplevel()
    label = Label(v, text = "Introduzca una fecha para busca (dd-mm-aaaa): ")
    label.pack(side=LEFT)
    entry = Entry(v)
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)
    
def buscar_genero():
    def listar(event):
        conn = sqlite3.connect('peliculas.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT TITULO, FECHA FROM PELICULA WHERE GENEROS LIKE '%" + str(entry.get()) + "%'")
        conn.close
        listar_peliculas_2(cursor)
        
    conn = sqlite3.connect('peliculas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT GENEROS FROM PELICULA")
    conn.close
    generos = set()
    for row in cursor:
        generos_pelicula = row[0].split(",")
        for genero in generos_pelicula:
            generos.add(genero.strip())
    
    v = Toplevel()
    label = Label(v, text = "Seleccione un género: ")
    label.pack(side=LEFT)
    entry = Spinbox(v, values=list(generos), state='readonly')
    entry.bind("<Return>", listar)
    entry.pack(side=LEFT)

def ventana_ppal():
    raiz = Tk()
    
    menu = Menu(raiz)
    
    # DATOS
    menudatos = Menu(menu, tearoff=0) # se crea el submenú (dentro de menu) 
    # tearoff=0 significa que no se puede "separar" ese menú en una ventana flotante (por defecto Tkinter permite eso si se deja en tearoff=1).
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Listar", command=listar_todo)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos) # se agrega el submenú al menú
    
    # BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Título", command=buscar_titulo)
    menubuscar.add_command(label="Fecha", command=buscar_fecha)
    menubuscar.add_command(label="Generos", command=buscar_genero)
    menu.add_cascade(label="Buscar", menu=menubuscar)
    
    raiz.config(menu=menu)
    
    raiz.mainloop()



if __name__ == "__main__":
    ventana_ppal()