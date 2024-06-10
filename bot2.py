import telebot
import sqlite3
import threading
import re
import ast
import unicodedata
from nltk.tokenize import word_tokenize
from telebot import apihelper
import numpy as np
import io
import nltk
nltk.download('punkt')
from collections import Counter
from io import BytesIO
import base64
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib
import os 
from tabulate import tabulate
import random
from prettytable import PrettyTable

matplotlib.use('Agg')

# Establecer el tiempo de espera de la API en 30 segundos
apihelper.READ_TIMEOUT = 30
# Creación del bot
bot = telebot.TeleBot('TU_TOKEN')


@bot.message_handler(commands=["start"])
def cmd_start(message):
    username = message.from_user.first_name
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(
        message,
        f"¡Hola, {username}! ¡Bienvenido a StaBotix! Soy tu Asistente Virtual para el área de la Estadística Descriptiva. Mi objetivo es ayudarte en lo relacionado con conceptos básicos, cálculos y gráficos estadísticos."
    )
@bot.message_handler(commands=["help"])
def cmd_start(message):
    username = message.from_user.first_name
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(
        message,
        f"¡Bienvenido, {username}! Aquí están los comandos que puedes usar:\n- /start: Inicia una nueva sesión con el bot.\n- /help: Muestra este mensaje de ayuda.\n Además de estos comandos, puedes interactuar conmigo usando lenguaje natural. Por ejemplo, puedes preguntarme ¿Cuál es la media de estos números: 1, 2, 3, 4, 5? o Calcula la desviación estándar de 1, 2, 3, 4, 5.\nEs importante saber que a la hora de realizar la solicitud, los únicos números, deben ser los datos, el resto de la solicitud no debe contener números para obtener un mejor resultado.\nEstoy aquí para ayudarte con tus necesidades de estadísticas. Si tienes alguna pregunta o necesitas más ayuda, no dudes en preguntar."
    )

# Función para manejar los mensajes de texto
def process_message(message):
    oracion = message.text.lower()  # Convertir la oración a minúsculas
    # Eliminar los acentos
    oracion = ''.join(c for c in unicodedata.normalize('NFD', oracion) if unicodedata.category(c) != 'Mn')

    # Tokenizar la oración en palabras
    palabras_simples = word_tokenize(oracion)
    palabras_compuestas = re.findall(r'\b\w+(?:\s\w+){1,2}\b', oracion)  # Buscar palabras compuestas

    # Verificar si hay números en la lista de palabras
    hay_numeros = any(palabra.isdigit() for palabra in palabras_simples)

    # Crear una lista para almacenar las definiciones encontradas
    definiciones_encontradas = []
    # Crear una lista para almacenar los cálculos estadísticos
    resultados = []
    numeros = []
    enviar_mensaje_no_reconocido = True

    if hay_numeros:
        # Realizar los cálculos estadísticos solo si hay números en el mensaje
        for palabra in palabras_simples:
            if palabra.isdigit() or (palabra.isalpha() and palabra in ["media", "promedio", "average", "mediana", "moda", "desviacion", "varianza"]):
                # Realizar cálculos estadísticos si la palabra es un número o una solicitud de cálculo
                resultado = calcular_estadisticas(palabras_simples, palabra)
                if resultado:
                    resultados.append(resultado)
        enviar_mensaje_no_reconocido = False

        # Generar gráficos según la solicitud del usuario
        if "grafico" in palabras_simples or "diagrama" in palabras_simples:
            if "circular" in palabras_simples or "pastel" in palabras_simples:
                numeros = [float(palabra) for palabra in palabras_simples if palabra.isdigit()]
                chat_id = message.chat.id
                hacer_grafico_circular(chat_id, numeros)
            elif "barra" in palabras_simples or "barras" in palabras_simples:
                numeros = [float(palabra) for palabra in palabras_simples if palabra.isdigit()]
                chat_id = message.chat.id
                hacer_diagrama_barras(chat_id, numeros)
            elif "linea" in palabras_simples:
                numeros = [float(palabra) for palabra in palabras_simples if palabra.isdigit()]
                chat_id = message.chat.id
                x = [i + 1 for i in range(len(numeros))]
                hacer_grafico_linea(chat_id, x, numeros)
        elif "histograma" in palabras_simples:
            numeros = [float(palabra) for palabra in palabras_simples if palabra.isdigit()]
            chat_id = message.chat.id
            rango_valores = (0, 100)
            hacer_histograma(chat_id, numeros, rango = rango_valores)
        elif "poligono" in palabras_simples:
            numeros = [float(palabra) for palabra in palabras_simples if palabra.isdigit()]
            chat_id = message.chat.id
            hacer_poligono_frecuencia(chat_id, numeros)

        elif "tabla" in palabras_simples or "distribucion" in palabras_simples:
                numeros = [float(palabra) for palabra in palabras_simples if palabra.isdigit()]
                chat_id = message.chat.id
                tabla_frecuencia = generar_tabla_frecuencia(numeros)
                enviar_tabla_frecuencia(chat_id, tabla_frecuencia)

    else:
        # No hay números en el mensaje, realizar consulta a la base de datos para buscar definiciones
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()

        # Crear un conjunto de palabras compuestas para facilitar la búsqueda
        palabras_compuestas_set = set(palabras_compuestas)
        
        for palabra in palabras_simples:
            if palabra not in palabras_compuestas_set and palabra not in definiciones_encontradas:
                cursor.execute("SELECT descr FROM definicion WHERE nombre=?", (palabra,))
                result = cursor.fetchone()
                if result:
                    definicion = result[0]
                    definiciones_encontradas.append(definicion)

        # Buscar definiciones de palabras compuestas
        for palabra in palabras_compuestas:
            if palabra not in definiciones_encontradas:
                cursor.execute("SELECT descr FROM definicion WHERE nombre=?", (palabra,))
                result = cursor.fetchone()
                if result:
                    definicion = result[0]
                    definiciones_encontradas.append(definicion)

        if "ejercicio" in palabras_simples or "propuesto" in palabras_simples:
            cursor.execute("SELECT enunciado FROM ejercicios ORDER BY RANDOM() LIMIT 1")
            ejercicio_propuesto = cursor.fetchone()
            if ejercicio_propuesto:
                enviar_mensaje_no_reconocido = False
                bot.send_message(message.chat.id, ejercicio_propuesto[0])

        conn.close()
        if definiciones_encontradas:
            enviar_mensaje_no_reconocido = False

    # Enviar las definiciones encontradas al usuario
    if definiciones_encontradas:
        respuesta_definiciones = "\n".join(definiciones_encontradas)
        bot.send_chat_action(message.chat.id, "typing")
        bot.send_message(message.chat.id, respuesta_definiciones)

    # Enviar los resultados de los cálculos estadísticos al usuario
    if resultados:
        respuesta_resultados = "\n".join(resultados)
        bot.send_message(message.chat.id, respuesta_resultados)

    # Enviar un mensaje al usuario si no se encontró ninguna palabra clave
    if enviar_mensaje_no_reconocido:
        bot.send_chat_action(message.chat.id, "typing")
        bot.reply_to(message, "Lo siento! No reconozco tu solicitud. Recuerda que solo puedo ayudarte con las definiciones básica, cálculos y gráficos estadísticos.")
    
# Función para realizar cálculos estadísticos
def calcular_estadisticas(palabras, tipo):
    # Realizar los cálculos estadísticos en base a las palabras y el tipo de cálculo solicitado
    if tipo == "media" or tipo == "promedio" or tipo == "average":
        # Calcular la media en base a los números en la lista de palabras
        numeros = [float(palabra) for palabra in palabras if palabra.isdigit()]
        suma =sum(numeros)
        total = len(numeros)
        pasos = f"Para calcular la media primero se suman los valores de los datos introducidos {suma} y luego se divide entre el número total de datos\n {total}."
        media = round(np.mean(numeros), 2)
        resultado = f"{pasos} Finalmente la media de los números es {media}"
    elif tipo == "mediana":
        # Calcular la mediana en base a los números en la lista de palabras
        numeros = [float(palabra) for palabra in palabras if palabra.isdigit()]
        numeros_ordenados = sorted(numeros)
        pasos = f"Para calcular la mediana de los datos introducidos, primero se ordenan los numeros de forma ascendente y luego se identifica el que está en el centro de la lista\n {numeros_ordenados}"
        mediana = round(np.median(numeros), 2)
        resultado = f"{pasos}\nLa mediana de los números es {mediana}"
    elif tipo == "moda":
        # Calcular la moda en base a los números en la lista de palabras
        numeros = [float(palabra) for palabra in palabras if palabra.isdigit()]
        frecuencias = np.bincount(numeros)
        moda_indices = np.where(frecuencias == np.max(frecuencias))[0]
        modas = [float(index) for index in moda_indices]
        numeros_ordenados = sorted(numeros)
        pasos = f"Para encontrar la moda o modas de los datos, primero se ordenan de forma ascendente y se cuentan las repeticiones de cada número, luedo se identifican los números con mayor frecuencia.\n {numeros_ordenados}"
        resultados = f"Las modas de los números son: {modas}" if modas else "No se encontró ninguna moda."
        resultado = f"{pasos}\n\nResultado:\n{resultados}"
    elif tipo == "desviacion":
        # Calcular la desviación estándar en base a los números en la lista de palabras
        numeros = [float(palabra) for palabra in palabras if palabra.isdigit()]
        media = round(np.mean(numeros), 2)
        suma_diferencia = round(sum([(numero - sum(numeros) / len(numeros)) ** 2 for numero in numeros]), 2)
        pasos = f"Para obtener la desviación de los datos primero se calcula la media de los números. {media}\n Se calcula la suma de las diferencias al cuadrado entre cada número y la media. {suma_diferencia}\n Se divide la suma de las diferencias al cuadrado entre la cantidad de números y se calcula la raíz cuadrada"
        desviacion = round(np.std(numeros), 2)
        resultado = f"{pasos}\nLa desviación estándar de los números es {desviacion}"
    elif tipo == "varianza":
        # Calcular la desviación estándar en base a los números en la lista de palabras
        numeros = [float(palabra) for palabra in palabras if palabra.isdigit()]
        media = round(np.mean(numeros), 2)
        suma_diferencia = round(sum([(numero - sum(numeros) / len(numeros)) ** 2 for numero in numeros]), 2)
        pasos = f"Para obtener la varianza de los datos primero se calcula la media de los números. {media}\n Se calcula la suma de las diferencias al cuadrado entre cada número y la media. {suma_diferencia}\n Se divide la suma de las diferencias al cuadrado entre la cantidad de números"
        varianza = round(np.var(numeros), 2)
        resultado = f"{pasos} La varianza de los números es {varianza}"
    else:
        resultado = None
    return resultado
    
def hacer_histograma(chat_id, numeros, rango):
    plt.clf()  # Limpiar la figura actual
    plt.hist(numeros, bins='auto')
    plt.xlabel('Valores')
    plt.ylabel('Frecuencia')
    plt.title('Histograma')
    # Guardar el gráfico en un archivo temporal
    temp_file = 'histogram.png'
    plt.savefig(temp_file)
    # Enviar el gráfico al usuario
    with open(temp_file, 'rb') as file:
        bot.send_chat_action(chat_id, "typing")
        bot.send_photo(chat_id, file)
    # Eliminar el archivo temporal
    os.remove(temp_file)

def hacer_diagrama_barras(chat_id, numeros):
    plt.clf()  # Limpiar la figura actual
    etiquetas = list(set(numeros))  # Obtener las etiquetas únicas
    etiquetas.sort()  # Ordenar las etiquetas de forma ascendente
    frecuencias = [numeros.count(etiqueta) for etiqueta in etiquetas]  # Calcular la frecuencia de cada etiqueta
    plt.bar(etiquetas, frecuencias)
    plt.xlabel('Etiquetas')
    plt.ylabel('Frecuencias')
    plt.title('Diagrama de Barras')
    # Guardar el gráfico en un archivo temporal
    temp_file = 'barras.png'
    plt.savefig(temp_file)
    # Enviar el gráfico al usuario
    with open(temp_file, 'rb') as file:
        bot.send_chat_action(chat_id, "typing")
        bot.send_photo(chat_id, file)
    # Eliminar el archivo temporal
    os.remove(temp_file)

def hacer_grafico_linea(chat_id, x, y):
    plt.clf()  # Limpiar la figura actual
    plt.plot(x, y)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Gráfico de Línea')
    # Guardar el gráfico en un archivo temporal
    temp_file = 'linea.png'
    plt.savefig(temp_file)
    # Enviar el gráfico al usuario
    with open(temp_file, 'rb') as file:
        bot.send_chat_action(chat_id, "typing")
        bot.send_photo(chat_id, file)
    # Eliminar el archivo temporal
    os.remove(temp_file)

def hacer_grafico_circular(chat_id, numeros):
    plt.clf()  # Limpiar la figura actual
    etiquetas = [str(i) for i in range(len(numeros))]
    plt.pie(numeros, labels=etiquetas)
    plt.legend()
    plt.title('Gráfico Circular')
    # Guardar el gráfico en un archivo temporal
    temp_file = 'circular.png'
    plt.savefig(temp_file)
    # Enviar el gráfico al usuario
    with open(temp_file, 'rb') as file:
        bot.send_chat_action(chat_id, "typing")
        bot.send_photo(chat_id, file)
    # Eliminar el archivo temporal
    os.remove(temp_file)

def hacer_poligono_frecuencia(chat_id, numeros):
    plt.clf()  # Limpiar la figura actual
    freq = Counter(numeros)
    x, y = zip(*sorted(freq.items()))
    plt.plot(x, y, 'o-')
    plt.xlabel('Valores')
    plt.ylabel('Frecuencia')
    plt.title('Polígono de Frecuencia')
    # Guardar el gráfico en un archivo temporal
    temp_file = 'poligono.png'
    plt.savefig(temp_file)
    # Enviar el gráfico al usuario
    with open(temp_file, 'rb') as file:
        bot.send_chat_action(chat_id, "typing")
        bot.send_photo(chat_id, file)
    # Eliminar el archivo temporal
    os.remove(temp_file)

def generar_tabla_frecuencia(numeros):
    num_datos = len(numeros)
    max_valor = max(numeros)
    min_valor = min(numeros)
    rango = max_valor - min_valor

    if max_valor < 10:
        tabla = {}
        total = len(numeros)
        frecuencia_acumulada = 0

        for numero in sorted(set(numeros)):
            numero_entero = int(numero)
            tabla[numero_entero] = {
                'Marca de Clase': numero_entero,
                'Frecuencia': numeros.count(numero),
                'Frecuencia Acumulada': 0,
            }
            frecuencia_acumulada += tabla[numero_entero]['Frecuencia']
            tabla[numero_entero]['Frecuencia Acumulada'] = frecuencia_acumulada

        return tabla
    if rango < 10:
        tabla = {}
        total = len(numeros)
        frecuencia_acumulada = 0

        for numero in sorted(set(numeros)):
            numero_entero = int(numero)
            tabla[numero_entero] = {
                'Marca de Clase': numero_entero,
                'Frecuencia': numeros.count(numero),
                'Frecuencia Acumulada': 0,
            }
            frecuencia_acumulada += tabla[numero_entero]['Frecuencia']
            tabla[numero_entero]['Frecuencia Acumulada'] = frecuencia_acumulada

        return tabla

    else:
        if num_datos < 25:
            tabla = {}
            total = len(numeros)
            frecuencia_acumulada = 0

            for numero in sorted(set(numeros)):
                numero_entero = int(numero)
                tabla[numero_entero] = {
                    'Marca de Clase': numero_entero,
                    'Frecuencia': numeros.count(numero),
                    'Frecuencia Acumulada': 0,
                }
                frecuencia_acumulada += tabla[numero_entero]['Frecuencia']
                tabla[numero_entero]['Frecuencia Acumulada'] = frecuencia_acumulada

            return tabla
        else:
            num_intervalos = math.ceil(1 + math.log2(num_datos))
            ancho_intervalo = rango / num_intervalos
            tabla = {}
            total = len(numeros)
            frecuencia_acumulada = 0
            
            for i in range(num_intervalos):
                intervalo_min = min_valor + i * ancho_intervalo
                intervalo_max = intervalo_min + ancho_intervalo
                
                intervalo = f"{intervalo_min:.2f} - {intervalo_max:.2f}"
                marca_clase = round((intervalo_max + intervalo_min)/2, 2)
                
                tabla[intervalo] = {
                    'Marca de Clase': marca_clase,
                    'Frecuencia': 0,
                    'Frecuencia Acumulada': 0,
                }
                
                for numero in numeros:
                    if intervalo_min <= numero < intervalo_max:
                        tabla[intervalo]['Frecuencia'] += 1

                tabla[intervalo]['Frecuencia Acumulada'] = frecuencia_acumulada + tabla[intervalo]['Frecuencia']
                frecuencia_acumulada = tabla[intervalo]['Frecuencia Acumulada']

            return tabla

def enviar_tabla_frecuencia(chat_id, tabla):
    headers = ["Datos", "Xm", "F", "FA"]
    data = []
    for numero, frecuencias in tabla.items():
        row = [
            numero,
            frecuencias['Marca de Clase'],
            frecuencias['Frecuencia'],
            frecuencias['Frecuencia Acumulada']
        ]  
        data.append(row)

    # Crear la tabla
    table = PrettyTable()

    # Añadir los encabezados a la tabla
    table.field_names = headers

    # Añadir los datos a la tabla
    for row in data:
        table.add_row(row)

    # Convertir la tabla a una cadena
    tabla_formateada = str(table)

    bot.send_chat_action(chat_id, "typing")
    bot.send_message(chat_id, tabla_formateada)


# Manejador para los mensajes de texto
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Crear un hilo para procesar el mensaje
    thread = threading.Thread(target=process_message, args=(message,))
    thread.start()

def start_bot():
    # Iniciar el bot
    bot.polling()

# Iniciar el bot
if __name__ == '__main__':
    threading.Thread(target=start_bot).start()
    print("Bot iniciado")
