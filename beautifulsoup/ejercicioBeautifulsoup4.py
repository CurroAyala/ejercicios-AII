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
    

def extraer_elementos():
    res = {}
    url = "https://as.com/resultados/futbol/primera/2023_2024/calendario/"
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f, "lxml")
    #jornadas = s.find("div", class_="container content").find("div", class_="row").find_next_sibling("div", class_="row").find_next_sibling("div", class_="row")
    jornadas = s.find("div", class_="cont-desplegable").find_next_sibling("div", class_="row").find_all("div", class_="col-md-6 col-sm-6 col-xs-12")
    i = 1
    for j in jornadas:
        datos_partidos = j.find("table", class_="tabla-datos").find("tbody").find_all("tr")
        partidos = []
        for p in datos_partidos:
            local = p.find("td").find("span", class_="nombre-equipo").string.strip()
            resultado = p.find("td").find_next_sibling("td", class_="col-resultado finalizado").find("a").string.strip()
            link = p.find("td").find_next_sibling("td", class_="col-resultado finalizado").a['href'].strip()
            goles_l = int(resultado[0])
            goles_v = int(resultado[4])
            visitante = p.find("td").find_next_sibling("td").find_next_sibling("td").find("span", class_="nombre-equipo").string.strip()
            partidos.append([local, goles_l, goles_v, visitante, link])
        res[i] = partidos
        i += 1
    return res

def almacenar_db(dicc):
    conn = sqlite3.connect('resultados.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS RESULTADOS;")
    conn.execute('''CREATE TABLE RESULTADOS
        (JORNADA          INT     NOT NULL,
         LOCAL            TEXT    NOT NULL,
         GOLES_LOCAL      INT     NOT NULL,
         GOLES_VISITANTE  INT     NOT NULL,
         VISITANTE        TEXT    NOT NULL,
         ENLACE           TEXT    NOT NULL);''')
    
    for jornada, partidos in dicc.items():
        for partido in partidos:
            conn.execute('''INSERT INTO RESULTADOS (JORNADA, LOCAL, GOLES_LOCAL, GOLES_VISITANTE, VISITANTE, ENLACE) VALUES (?,?,?,?,?,?)''',
                         (jornada, partido[0], partido[1], partido[2], partido[3], partido[4]))
    conn.commit()
    
    cursor = conn.execute("SELECT COUNT(*) FROM RESULTADOS;")
    messagebox.showinfo("Base de datos", "Base de datos creada correctamente.\nHay " + str(cursor.fetchone()[0]) + " registros.")
    
def cargar():
    respuesta = messagebox.askyesno("Confirmar", "¿Está seguro de que quiere recargar los datos?\nEsta operación puede ser lenta.")
    if (respuesta):
        d = extraer_elementos()
        almacenar_db(d)
        
def listar_todo():
    conn = sqlite3.connect('resultados.db')
    conn.text_factory = str
    numero_jornadas = conn.execute("SELECT COUNT (DISTINCT JORNADA) FROM RESULTADOS;").fetchone()[0]
    
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=200, yscrollcommand=sc.set)
    
    for j in range(1,numero_jornadas+1):
        cursor = conn.execute("SELECT LOCAL, GOLES_LOCAL, GOLES_VISITANTE, VISITANTE FROM RESULTADOS WHERE JORNADA = ?", (j,))
        
        s = "JORNADA " + str(j)
        lb.insert(END,s)
        lb.insert(END, "\n")
        
        for row in cursor:
            s = row[0] + " " + str(row[1]) + " - " + str(row[2]) + " " + row[3]
            lb.insert(END,s)
        
        lb.insert(END, "_____________________________________")
        lb.insert(END, "\n\n")
    
    conn.close
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
    
def buscar_jornada():
    conn = sqlite3.connect('resultados.db')
    conn.text_factory = str
    def mostrar(evento):
        v = Toplevel()
        sc = Scrollbar(v)
        sc.pack(side=RIGHT, fill=Y)
        lb = Listbox(v, width=200, yscrollcommand=sc.set)
        cursor = conn.execute("SELECT LOCAL, GOLES_LOCAL, GOLES_VISITANTE, VISITANTE FROM RESULTADOS WHERE JORNADA = ?", (j.get(),))
        s = "JORNADA " + str(j.get())
        lb.insert(END,s)
        lb.insert(END, "\n")
        
        for row in cursor:
            s = row[0] + " " + str(row[1]) + " - " + str(row[2]) + " " + row[3]
            lb.insert(END,s)
        
        lb.insert(END, "_____________________________________")
        lb.insert(END, "\n\n")
        
        lb.pack(side=LEFT, fill=BOTH)
        sc.config(command=lb.yview)
    
    v = Toplevel()
    label = Label(v, text = "Seleccione una jornada: ")
    label.pack(side=LEFT) 
    numero_jornadas = conn.execute("SELECT COUNT (DISTINCT JORNADA) FROM RESULTADOS;").fetchone()[0]
    j = Spinbox(v, values =list(range(1,numero_jornadas+1)), state='readonly')
    j.bind("<Return>", mostrar)
    j.pack(side=LEFT)
    conn.close
    
def estadisticas_jornada():
    conn = sqlite3.connect('resultados.db')
    conn.text_factory = str
    def mostrar(evento):
        v = Toplevel()
        sc = Scrollbar(v)
        sc.pack(side=RIGHT, fill=Y)
        lb = Listbox(v, width=200, yscrollcommand=sc.set)
        cursor = conn.execute("SELECT GOLES_LOCAL, GOLES_VISITANTE FROM RESULTADOS WHERE JORNADA = ?", (j.get(),))
        s = "JORNADA " + str(j.get())
        lb.insert(END,s)
        lb.insert(END, "\n")
        
        goles_total = 0
        victorias_locales = 0
        victorias_visitantes = 0
        empates = 0
        for row in cursor:
            goles_total += row[0] + row[1]
            if (row[0] > row[1]):
                victorias_locales += 1
            elif(row[0] < row[1]):
                victorias_visitantes += 1
            else:
                empates += 1
        
        lb.insert(END, "Total goles en la jornada: " + str(goles_total))
        lb.insert(END, "\n")
        lb.insert(END, "Empates: " + str(empates))
        lb.insert(END, "Victorias locales: " + str(victorias_locales))
        lb.insert(END, "Victorias visitantes: " + str(victorias_visitantes))
        lb.insert(END, "_____________________________________")
        lb.insert(END, "\n\n")
        
        lb.pack(side=LEFT, fill=BOTH)
        sc.config(command=lb.yview)
    
    v = Toplevel()
    label = Label(v, text = "Seleccione una jornada: ")
    label.pack(side=LEFT)
    numero_jornadas = conn.execute("SELECT COUNT (DISTINCT JORNADA) FROM RESULTADOS;").fetchone()[0]
    j = Spinbox(v, values =list(range(1,numero_jornadas+1)), state='readonly')
    j.bind("<Return>", mostrar)
    j.pack(side=LEFT)
    conn.close
    
def buscar_goles(j:int, lo:str, vi:str):
    conn = sqlite3.connect('resultados.db')
    conn.text_factory = str
    enlace = conn.execute("SELECT ENLACE FROM RESULTADOS WHERE JORNADA = ? AND LOCAl = ?;", (j,lo)).fetchone()[0]
    conn.close
    
    f = urllib.request.urlopen(enlace)
    s = BeautifulSoup(f, 'lxml')
    goleadores_local = s.find("header", class_="scr-hdr").find("div", class_="scr-hdr__team is-local").find("div", class_="scr-hdr__scorers").find_all("span", class_=False)
    goleadores_local = [g.text.replace(",", "").strip() for g in goleadores_local]
    goleadores_visitante = s.find("header", class_="scr-hdr").find("div", class_="scr-hdr__team is-visitor").find("div", class_="scr-hdr__scorers").find_all("span", class_=False)
    goleadores_visitante = [g.text.replace(",", "").strip() for g in goleadores_visitante]
    
    v = Toplevel()
    lb = Listbox(v, width=100)
    local = lo + ": "
    for gol in goleadores_local:
        local += gol
    visitante = vi + ": "
    for gol in goleadores_visitante:
        visitante += gol + " "
    lb.insert(END, local)
    lb.insert(END, "\n")
    lb.insert(END, visitante)
    lb.pack(side=LEFT, fill=BOTH)
    

def buscar_goles_ventana():
    conn = sqlite3.connect('resultados.db')
    conn.text_factory = str

    def actualizar_locales(*args):
        try:
            n = int(var_jornada.get())
        except:
            return
        filas = conn.execute("SELECT LOCAL FROM RESULTADOS WHERE JORNADA = ?", (n,)).fetchall()
        locales = [f[0] for f in filas]
        lo.config(values=locales)
        if locales:
            var_local.set(locales[0])
            actualizar_visitante()

    def actualizar_visitante(*args):
        try:
            n = int(var_jornada.get())
            l = var_local.get()
        except:
            return
        fila = conn.execute(
            "SELECT VISITANTE FROM RESULTADOS WHERE JORNADA = ? AND LOCAL = ?", 
            (n, l)
        ).fetchone()
        visitante = fila[0] if fila else "-"
        var_visitante.set(visitante)
        vi.config(values=[visitante])

    v = Toplevel()
    v.geometry("760x80")

    # SPINBOX PARA LA JORNADA
    Label(v, text="Seleccione una jornada: ").pack(side=LEFT)
    numero_jornadas = conn.execute("SELECT COUNT(DISTINCT JORNADA) FROM RESULTADOS;").fetchone()[0]
    var_jornada = StringVar()
    j = Spinbox(v, values=list(range(1, numero_jornadas + 1)), state='readonly', textvariable=var_jornada, width=5)
    j.pack(side=LEFT)
    # SPINBOX PARA EL EQUIPO LOCAL
    Label(v, text="Selecciona equipo local: ").pack(side=LEFT)
    var_local = StringVar()
    lo = Spinbox(v, values=[], state='readonly', textvariable=var_local, width=15)
    lo.pack(side=LEFT)
    # SPINBOX PARA EL EQUIPO VISITANTE
    Label(v, text="Equipo visitante: ").pack(side=LEFT)
    var_visitante = StringVar()
    vi = Spinbox(v, values=["-"], state=DISABLED, textvariable=var_visitante, width=15)
    vi.pack(side=LEFT)
    
    # Conectar trace para actualizaciones automáticas
    var_jornada.trace("w", actualizar_locales)
    var_local.trace("w", actualizar_visitante)

    # Inicializar primera jornada
    var_jornada.set("1")
    
    conn.close
        
    buscar = Button(v, text="Buscar goles", command=lambda: buscar_goles(var_jornada.get(), var_local.get(), var_visitante.get()))
    buscar.pack(side=LEFT)


def ventana_ppal():
    raiz = Tk()
    raiz.title("Ejercicio 4")
    
    almacenar = Button(raiz, text="Almacenar resultados", command=cargar)
    almacenar.place(x=35, y=15)
    
    listar = Button(raiz, text="Listar", command=listar_todo)
    listar.place(x=35, y=50)
    
    mostrar_jornada = Button(raiz, text="Buscar jornada", command=buscar_jornada)
    mostrar_jornada.place(x=35, y = 85)
    
    mostrar_estadisticas = Button(raiz, text="Estadística jornada", command=estadisticas_jornada)
    mostrar_estadisticas.place(x=35, y=120)
    
    mostrar_goles = Button(raiz, text="Buscar goles", command=buscar_goles_ventana)
    mostrar_goles.place(x=35, y = 155)
    
    raiz.mainloop()



if __name__ == "__main__":
    ventana_ppal()