# Usa una imagen base de Python
FROM python:3.8-slim-buster

# Establece un directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código del bot
COPY bot2.py .

# Copia la base de datos
COPY bot.db .

# Ejecuta el bot
CMD ["python", "bot2.py"]
