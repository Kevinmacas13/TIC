from flask import Flask, render_template, request, Response, redirect, url_for
import threading  # Librería para segundo plano
import cv2  # Librería para manejar imágenes
import face_recognition  # Librería para realizar el reconocimiento facial
import os  # Librería para manejar archivos o directorios
import mysql.connector  # Librería para comunicarme con  la base de datos
import serial  # Librería para comución serial con Arduino
import random    # Librería generar número randómico
import telepot  # Libreria para el bot
import time  # Libreria para el tiempo
from datetime import datetime

## --------Creación de la app  de Flask-------------------##
app = Flask(__name__)

# Función para leer el puerto serial


def leer_puerto_serial():
    try:
        # Se define el puerto  Serial
        puerto_serial = serial.Serial('COM5', 9600)
        # Se definen variables iniciales
        letrac = ""
        codgenerado = "None"
        contadores = [0, 0, 0]
        Horas = ["", "", "", ""]
        # Inicializo el ciclo para ingreso de usuario
        while True:
            # Lectura puerto  Serial
            dato = puerto_serial.readline().decode().strip()
            if len(dato) > 5:
                Horas[0] = datetime.now().time()
            # Revisar si se ingreso una letra del teclado matricial
            if len(dato) == 1 and len(letrac) < 3:
                letrac += dato
                puerto_serial.write(("CI:"+letrac).encode())
            elif len(dato) == 1:
                letrac = ""+dato
            print(dato)
            # Activar función para solicitud de ingreso
            ingresou = solicita_ingreso(dato)
            if ingresou:
                contadores[0] += 1
                print(ingresou[1])
                # Obtener el  nombre del usuario que solicita el  ingreso
                nomf = ingresou[1]
                puerto_serial.write("LecturaCorrecta".encode())
                time.sleep(5)
                Lecmag = "1"
                # Generar el código para el acceso  del usuario
                while Lecmag == "1":
                    puerto_serial.write("CierrePuerta".encode())
                    Lecmag = puerto_serial.readline().decode().strip()
                    time.sleep(1)
                    print(Lecmag)
                Horas[1] = datetime.now().time().strftime("%H:%M:%S")
                codgenerado = enviocodigo(ingresou[5])
                # Indicar en el  monitor el  código que fue generado
                print(f"El codigo generado es: {codgenerado}")
                # Indicar en el LCD que el código fue enviado al usuario
                puerto_serial.write("Codigo enviado".encode())
                ingresou = "None"
            #  Comparar si el  código  enviado  al usuario coincide con el  ingresado.
            if codgenerado == letrac:
                Horas[2] = datetime.now().time().strftime("%H:%M:%S")
                contadores[1] += 1
                time.sleep(2)
                # Enviar mensaje de inicio de Reconocimiento Facial  en proceso
                puerto_serial.write("Reconocimiento Facial".encode())
                print("Reconocimiento Facial en proceso")
                # Iniciar el  reconocimiento  Facial
                reconocido = reconocimiento_facial(nomf)
                # Punto  de decisión  del  reconocimiento facial
                if reconocido:
                    contadores[2] += 1
                    # Si el  reconocimiento coincide se permite el ingreso y madan mensaje a la pantalla
                    puerto_serial.write("Usuario Correcto".encode())
                    print("Usuario ingresado correctamente")
                    # Registrar ingreso del usuario
                    Horas[3] = datetime.now().time().strftime("%H:%M:%S")
                    Ingresos = [str(Horas[1])+" ("+str(contadores[0])+")", str(Horas[2]) +
                                " ("+str(contadores[1])+")", str(Horas[3])+" ("+str(contadores[2])+")"]
                    registro_ingreso(
                        nomf, Horas[0], Ingresos[0], Ingresos[1], Ingresos[2])
                    contadores = [0, 0, 0]
                else:
                    # Si no coincide se niega el  acceso y  se manda el  mensaje en pantalla
                    puerto_serial.write("Usuario NR".encode())
                    print("Usuario no reconocido")
                    contadores[2] += 1
                letrac = ""
            # En caso  de que no  coincida el  código  ingresado con el código generado
            elif codgenerado != letrac and len(letrac) == 3:
                contadores[1] += 1
                print("Usuario incorrecto intente denuevo")
                time.sleep(3)
                puerto_serial.write("Codigo Incorrecto".encode())
                letrac = ""

    # Excepción en caso  de no poder leer el puerto
    except PermissionError:
        print("Error: No tienes permiso para acceder al puerto serial. Verifica que ningún otro programa esté utilizando el puerto COM5 y que tienes los permisos adecuados.")
    except Exception:
        print("")
    # Cierre del  puerto
    finally:
        if 'puerto_serial' in locals():
            puerto_serial.close()


# Definir una función para el reconocimiento facial
def reconocimiento_facial(nombre_usuario):
    # Inicializar la captura de video desde la cámara web
    cap = cv2.VideoCapture(0)  # Captura
    # Inicializar la variable para indicar si se reconoció un rostro conocido
    rostro_reconocido = False
    # Obtener el tiempo de inicio para el límite de tiempo de espera
    tiempo_inicio = time.time()
    # Definir el tiempo máximo de espera en segundos
    Tiempo_espera = 15
    # Crear la ruta a la carpeta del usuario dentro del directorio "dataset"
    carpeta_usuario = os.path.join("dataset", nombre_usuario)
    # Crear una lista de archivos de imagen en la carpeta del usuario que terminan con la extensión '.jpg'
    archivos_imagen = [f for f in os.listdir(
        carpeta_usuario) if f.endswith('.jpg')]
    # Inicializar listas para almacenar los rostros conocidos y los nombres asociados
    rostros_conocidos = []
    nombres_conocidos = []
    # Utilizar múltiples imágenes por usuario
    for archivo_imagen in archivos_imagen:
        # Cargar la imagen utilizando la biblioteca de reconocimiento facial
        imagen = face_recognition.load_image_file(
            os.path.join(carpeta_usuario, archivo_imagen))
        # Obtener la codificación facial de la imagen y agregarla a la lista de rostros conocidos
        encoding = face_recognition.face_encodings(imagen)[0]
        rostros_conocidos.append(encoding)
        # Agregar el nombre de usuario correspondiente a la lista de nombres conocidos
        nombres_conocidos.append(nombre_usuario)
    # Bucle principal para procesar fotogramas de video continuamente
    while True:
        # Capturar un fotograma de video desde la cámara web
        ret, frame = cap.read()
        # Verificar si la captura de video fue exitosa
        if not ret:
            break
        # Convertir el fotograma de video de BGR a RGB (formato utilizado por face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Encontrar las ubicaciones de los rostros en el fotograma
        ubicaciones = face_recognition.face_locations(rgb_frame)
        # Obtener las codificaciones faciales de los rostros encontrados en el fotograma
        encodings = face_recognition.face_encodings(rgb_frame, ubicaciones)
        # Verificar si ha pasado el tiempo de espera y no se han encontrado ubicaciones de rostros
        if time.time() - tiempo_inicio >= Tiempo_espera and not ubicaciones:
            break

        # Iterar sobre cada ubicación y codificación facial
        for ubicacion, encoding in zip(ubicaciones, encodings):
            # Comparar la codificación facial con las codificaciones faciales conocidas con una tolerancia del 50%
            coincidencias = face_recognition.compare_faces(
                rostros_conocidos, encoding, tolerance=0.5)
            # Inicializar el nombre como "Desconocido" por defecto
            nombre = "Desconocido"
            # Extraer las coordenadas del rectángulo que encierra el rostro
            top, right, bottom, left = ubicacion
            # Dibujar un rectángulo alrededor del rostro en el fotograma
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            # Mostrar el nombre del usuario sobre el rectángulo del rostro
            cv2.putText(frame, nombre, (left + 7, bottom - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)

            # Si se encuentra al menos una coincidencia
            if True in coincidencias:
                # Obtener el índice de la primera coincidencia verdadera
                indice_coincidencia = coincidencias.index(True)
                # Obtener el nombre asociado a la codificación facial coincidente
                nombre = nombres_conocidos[indice_coincidencia]
                # Establecer la variable de reconocimiento de rostro como verdadera
                rostro_reconocido = True
                # Cerrar todas las ventanas de visualización
                cv2.destroyAllWindows()
                # Devolver el valor de reconocimiento de rostro
                return rostro_reconocido

        # Mostrar el fotograma con los rostros detectados y sus nombres
        cv2.imshow('Reconocimiento Facial', frame)

        # Esperar a que se presione la tecla 'q' para salir del bucle
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
     # Verificar si se detectaron más de un rostro en el fotograma
    if len(ubicaciones) > 1:
        # Realizar alguna acción, como mostrar un mensaje o guardar el fotograma
        print("Se detectaron múltiples rostros en el fotograma.")
    # Liberar los recursos de la captura de video y cerrar todas las ventanas de visualización
    cap.release()
    cv2.destroyAllWindows()

    # Devolver el valor de reconocimiento de rostro
    return rostro_reconocido

# Define la función para tomar y guardar la foto del rostro


def tomar_y_guardar_foto(nombre):
    # Crear la carpeta si no existe para almacenar las fotos del usuario
    if not os.path.exists(f'dataset/{nombre}'):
        os.makedirs(f'dataset/{nombre}')
    # Inicializar la captura de video desde la cámara web
    cap = cv2.VideoCapture(0)
    # Ruta del archivo de cascada para la detección de rostros
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    # Cargar el clasificador de cascada para la detección de rostros
    face_cascade = cv2.CascadeClassifier(cascade_path)
    # Contador de fotos tomadas
    num_fotos = 0
    # Bucle para tomar 3 fotos
    while num_fotos < 3:
        # Capturar un fotograma de video desde la cámara web
        ret, img = cap.read()
        # Verificar si la captura fue exitosa
        if ret:
            # Convertir la imagen a escala de grises para la detección de rostros
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Detectar rostros en la imagen
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            # Iterar sobre los rostros detectados
            for (x, y, w, h) in faces:
                # Dibujar un rectángulo alrededor del rostro detectado
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                # Guardar la foto en la carpeta del usuario con un nombre único
                cv2.imwrite(f'dataset/{nombre}/image_{num_fotos}.jpg', img)
                # Incrementar el contador de fotos tomadas
                num_fotos += 1
                # Si se han tomado las 3 fotos necesarias, salir del bucle
                if num_fotos == 3:
                    break
            # Mostrar el fotograma con el rectángulo del rostro detectado
            cv2.imshow('Tomando foto', img)
            # Esperar 1 segundo entre cada foto
            cv2.waitKey(1000)
    # Liberar los recursos de la captura de video y cerrar todas las ventanas de visualización
    cap.release()
    cv2.destroyAllWindows()


# Función para solicitar peticiones con la base de Datos
def solicita_peticion(sql, valor):
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        database="mibase",
        port='3306'
    )
    cursor = conexion.cursor()
    if valor == "None":
        cursor.execute(sql)
        usuario_encontrado = cursor.fetchall()
    else:
        cursor.execute(sql, valor)
        usuario_encontrado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return usuario_encontrado

# Función para verificar el ingreso


def solicita_ingreso(valor):
    sql = "SELECT * FROM registro_usuarios WHERE codigo_rfid = %s"
    valores = (valor,)
    return solicita_peticion(sql, valores)

# Función para enviar un código de verificación


def enviocodigo(ID):
    # Digitos y letras a utilizar en el  código
    digitos_y_letras = ['0', '1', '2', '3', '4',
                        '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D']
    # Generar código  de ingreso de manera aleatoria.
    codigo = ''.join(random.choice(digitos_y_letras) for _ in range(3))
    SBot = telepot.Bot("5327399011:AAFUK0DctXubNsN5iA_5K8qvoEB6uzZRfSE")
    # ID = '1170653491'  # id del Usuario
    SBot.sendMessage(ID, f'Codigo de ingreso: {codigo}')
    return codigo

# Función para registrar el ingreso del usuario


def registro_ingreso(nombre_usuario, horaI, Ingreso1, Ingreso2, Ingreso3):
    fecha_ingreso = datetime.now().date()
    sql = "INSERT INTO control_usuarios (Nombre_usuario,Fecha_ingreso,Hora_inicio,Ingreso1,Ingreso2,Ingreso3) VALUES (%s,%s,%s,%s,%s,%s)"
    valores = (nombre_usuario, fecha_ingreso,
               horaI, Ingreso1, Ingreso2, Ingreso3)
    solicita_peticion(sql, valores)


# Ruta de inicio
@app.route("/")
def pantalla_principal():
    return render_template("index.html")


# Ruta para la página de registro facial
@app.route("/registro_facial")
def registro_facial():
    # Obtener el nombre de usuario de la solicitud GET
    nombre_usuario = request.args.get('nombre_usuario')
    if nombre_usuario:
        # Tomar y guardar tres fotos del rostro del usuario
        tomar_y_guardar_foto(nombre_usuario)
    return "Registro exitoso"


# Ruta de registro
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        # Lógica para procesar el formulario de registro
        nombre_usuario = request.form["usuario"]
        correo_electronico = request.form["correo"]
        contrasena = request.form["contrasena"]
        codigoRfid = request.form["codigorfid"]
        ncelular = request.form["numerocelular"]
        sql = "INSERT INTO registro_usuarios (nombre_usuario, correo_electronico, contrasena,codigo_rfid,numero_celular) VALUES (%s, %s, %s, %s, %s)"
        valores = (nombre_usuario, correo_electronico,
                   contrasena, codigoRfid, ncelular)
        solicita_peticion(sql, valores)
        # Redirige a la página de registro facial con el nombre de usuario
        return redirect(url_for('registro_facial', nombre_usuario=nombre_usuario))
    else:
        return render_template("registro.html")

# Ruta de inicio de sesión


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]
        sql = "SELECT * FROM registro_usuarios WHERE nombre_usuario = %s AND contrasena = %s"
        valores = (usuario, contrasena)
        usuario_encontrado = solicita_peticion(sql, valores)
        if usuario_encontrado:
            return redirect(url_for('control'))
        else:
            return render_template("login.html", mensaje="Usuario o contraseña incorrectos.")
    else:
        return render_template("login.html")

# Ruta de página de registros de ingreso


@app.route("/control")
def control():
    sql = "SELECT nombre_usuario, Fecha_ingreso, Hora_inicio, 	Ingreso1, 	Ingreso2 , 	Ingreso3 FROM control_usuarios"
    usuarios = solicita_peticion(sql, "None")
    return render_template('control.html', usuarios=usuarios)


# Inicio de la aplicación flask
if __name__ == "__main__":
    hilo_serial = threading.Thread(target=leer_puerto_serial)
    hilo_serial.daemon = True
    hilo_serial.start()
    app.run(debug=True)
