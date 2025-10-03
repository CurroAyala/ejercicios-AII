import csv
from tkinter import *
from tkinter import messagebox
import sqlite3


# MÉTODO PARA EXTRAER LOS DATOS DEL ARCHIVO .CSV (books.csv)
def extraer_datos(fichero):
    try :
        with open(fichero) as f: # abre el fichero con "with", que es un context manager en Python: abre un recurso y lo cierra al terminar su uso
            l = [row for row in csv.reader(f, delimiter=';',quotechar='"')] # lee, línea a línea, el fichero, usando como delimitador ";"
            # el quotechar="" sirve para indicar el caracter que se usa para encerrar campos de texto que pueden contener ;
        return l[1:]
    except:
        messagebox.showerror("Error", "Error en la apertura del fichero.")
        return None

# MÉTODO PARA ALMACENAR LOS LIBROS DE LA LISTA EXTRAÍDA EN UNA BASE DE DATOS   
def almacenar_bd(lista):
    conn = sqlite3.connect('../generated/databases/books.db') # abre o crea la base de datos "libros" y devuelve el objeto de conexión "con"
    conn.text_factory = str # establece que todos los textos de SQLite sean leído como str en Python
    conn.execute("DROP TABLE IF EXISTS BOOKS") # ejecuta el comando SQL
    conn.execute('''CREATE TABLE BOOKS (ISBN CHAR(9) PRIMARY KEY,
                                      TITLE TEXT NOT NULL,
                                      AUTHOR TEXT NOT NULL,
                                      YEAR INTEGER NOT NULL,
                                      PUBLISHER TEXT NOT NULL);''') # se usan tres comillas para instrucciones multilíneas
    for i in lista:
        if i[3] == 'Unknown': # el if es para tratar las líneas con el campo year como "Unknown", ya que debe ser un entero
            i[3] = 999999
        conn.execute('''INSERT INTO BOOKS (ISBN, TITLE, AUTHOR, YEAR, PUBLISHER)
                        VALUES (?,?,?,?,?)''',(i[0],i[1],i[2],i[3],i[4]))
    conn.commit() # confirma la transacción y persiste los cambiso en la base de datos
    cursor = conn.execute("SELECT COUNT(*) FROM BOOKS") # guarda la consulta en una variable
    messagebox.showinfo("Base de datos", "Base de datos creada correctamente.\n Hay " + str(cursor.fetchone()[0]) + " registros.")
    # el <str(cursor.fetchone()[0])> sirve para convertir el primer (y único) valor de la consulta guardada en cursor en str
    conn.close() # cierra la conexión con la base de datos

# MÉTODO PARA PREGUNTAR SI RECARGAR LOS DATOS DEL .CSV
def cargar():
    respuesta = messagebox.askyesno(title="Confirmar", message="¿Está seguro de que quiere recargar los datos?") # muestra un diálogo yes/no
    if respuesta:
        libros = extraer_datos("../data/books.csv")
        if libros:
            almacenar_bd(libros)

# MÉTODO PARA CREAR LA VENTANA DONDE LISTAR LOS DATOS
def listar(cursor):
    v = Toplevel() # crea una ventana secundaria para mostrar la lista
    sc = Scrollbar(v) # crea un ccrollbar, hijo de la ventana v
    sc.pack(side=RIGHT, fill=Y) # coloca la barra de desplazamiento a la derecha y la hace llenar verticalmente
    lb = Listbox(v, width=150, yscrollcommand=sc.set) # crea un listbox de 150 de ancho, enlazando su scrollbar a sc
    for row in cursor: # añade al listbox la información de cada fila
        s = 'TÍTULO: ' + row[1]
        lb.insert(END, s)
        lb.insert(END, "__________________________________________\n")
        s = "    ISBN: " + row[0] + " || AUTOR: " + row[2] + " || AÑO: " + (str(row[3]) if row[3] != 0 else "Desconocido")
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH) # empaqueta el Listbox a la izquierda y que llene el espacio horizontal y vertical disponible
    sc.config(command=lb.yview) # configura la Scrollbar para que su comando sea lb.yview, enlazando el listbox y la barra

# MÉTODO PARA LISTAR TODOS LOS DATOS
def listar_completo(): 
    conn = sqlite3.connect('../generated/databases/books.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT ISBN, TITLE, AUTHOR, YEAR FROM BOOKS")
    conn.close
    listar(cursor)
    
# MÉTODO PARA CREAR LA VENTANA DONDE LISTAR POR EDITORIAL (MUESTRA LAS COLUMNAS POR OTRO ORDEN)
def listar_editorial(cursor):
    v = Toplevel() # crea una ventana secundaria para mostrar la lista
    sc = Scrollbar(v) # crea un ccrollbar, hijo de la ventana v
    sc.pack(side=RIGHT, fill=Y) # coloca la barra de desplazamiento a la derecha y la hace llenar verticalmente
    lb = Listbox(v, width=150, yscrollcommand=sc.set) # crea un listbox de 150 de ancho, enlazando su scrollbar a sc
    for row in cursor:
        s = 'TÍTULO: ' + row[1]
        lb.insert(END, s)
        lb.insert(END, "__________________________________________\n")
        s = "    AUTOR: " + row[1] + " || EDITORIAL: " + row[2]
        lb.insert(END, s)
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

# MÉTODO PARA LISTAR LOS DATOS ORDENADOS SEGÚN PREFERENCIA
def listar_ordenado():
    def lista():
        conn = sqlite3.connect('../generated/databases/books.db')
        conn.text_factory = str
        if control.get() == 1: # según el valor de entrada
            cursor = conn.execute("SELECT ISBN, TITLE, AUTHOR, YEAR FROM BOOKS ORDER BY ISBN")
        else:
            cursor = conn.execute("SELECT ISBN, TITLE, AUTHOR, YEAR FROM BOOKS ORDER BY YEAR")
        conn.close
        listar(cursor)
    ventana = Toplevel()
    control = IntVar() # crea un IntVar que almacenará la opción seleccionada por los radiobutton
    rb1 = Radiobutton(ventana, text='Ordenado por año', variable=control, value=0) # radiobutton que asigna 0 a control
    rb2 = Radiobutton(ventana, text='Ordenado por ISBN', variable=control, value=1) # radiobutton que asigna 1 a control
    b = Button(ventana, text='Listar', command=lista) # botón que ejecuta la función lista definida arriba al pulsarlo
    rb1.pack()
    rb2.pack()
    b.pack()
    # los tres últimos comando son para empaquetar los widgets a la ventana

# MÉTODO PARA BUSCAR POR EDITORIAL
def buscar_editorial():
    def lista(event):
        conn = sqlite3.connect('../generated/databases/books.db') # conectarse a la base de datos
        conn.text_factory = str
        cursor = conn.execute("SELECT TITLE, AUTHOR, PUBLISHER FROM BOOKS WHERE PUBLISHER='" + sb.get() + "'") # guarda en cursor la consulta sql
        conn.close
        listar_editorial(cursor) # llama a listar_editoriales
    conn = sqlite3.connect('../generated/databases/books.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT PUBLISHER FROM BOOKS")
    editoriales = [i[0] for i in cursor] # construye una lista editoriales con la primera (y única) columna de cada fila del cursor
    
    v = Toplevel()
    sb = Spinbox(v, values=editoriales) # crea un Spinbox cuyos valores son la lista editoriales. El usuario puede seleccionar una de ellas
    sb.bind("<Return>", lista) # enlaza la tecla Return (Enter) en el Spinbox para ejecutar la función lista definida arriba
    sb.pack() # empaqueta el spinbox
    
    conn.close
    
# MÉTODO PARA BUSCAR POR TÍTULO
def buscar_titulo():
    def lista(event):
        conn = sqlite3.connect('../generated/databases/books.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT ISBN, TITLE, AUTHOR, YEAR FROM BOOKS WHERE TITLE LIKE '%" + entrada.get() + "%'")
        conn.close
        listar(cursor)
    conn = sqlite3.connect('../generated/databases/books.db')
    conn.text_factory = str
    
    v = Toplevel()
    lb = Label(v, text = 'Introduzca la palabra a buscar') # crea una etiqueta con instrucciones
    entrada = Entry(v) # crea un campo de entrada (Entry) donde el usuario escribirá la palabra
    entrada.bind("<Return>", lista) # al pulsar Return en el Entry se ejecutará la función lista
    lb.pack(side=LEFT)
    entrada.pack(side=LEFT)
    
    conn.close

# MÉTODO PARA DEFINIR LA VENTANA PRINCIPAL
def ventana_principal():
    raiz = Tk() # crea la raíz principal de la aplicación Tkinter.
    menu = Menu(raiz) # crea un Menu principal asociado a raiz
    # DATOS
    menudatos = Menu(menu, tearoff=0) # crea un submenú menudatos. tearoff=0 evita que se "despegue" el menú
    menudatos.add_command(label='Cargar', command=cargar) # añade item "Cargar" que ejecuta la función cargar
    menudatos.add_command(label='Salir', command=raiz.quit) # añade item "Salir" que cierra la aplicación (método quit de la raíz)
    menu.add_cascade(label='Datos', menu=menudatos) # añade el submenú menudatos al menú principal con la etiqueta "Datos".
    # LISTAR
    menulistar = Menu(menu, tearoff=0)
    menulistar.add_command(label='Completo', command=listar_completo)
    menulistar.add_command(label='Ordenado', command=listar_ordenado)
    menu.add_cascade(label='Listar', menu=menulistar)
    # BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label='Título', command=buscar_titulo)
    menubuscar.add_command(label='Editorial', command=buscar_editorial)
    menu.add_cascade(label='Buscar', menu=menubuscar)
    
    raiz.config(menu=menu)
    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()