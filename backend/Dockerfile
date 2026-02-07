# Usamos Python 3.10 Slim (Equilibrio entre tamaño y compatibilidad)
FROM python:3.10-slim

# 1. INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA
# - whois: Necesario para que la librería de python pueda hacer consultas whois.
# - git: A veces pip lo necesita para bajar paquetes específicos.
RUN apt-get update && apt-get install -y \
    whois \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. CONFIGURACIÓN DEL ENTORNO
WORKDIR /app

# 3. INSTALACIÓN DE LIBRERÍAS PYTHON
# Copiamos primero requirements para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. COPIA DE CÓDIGO FUENTE
# Copiamos TODO: .py, .png (fondo), .env (si decides meterlo, aunque mejor por docker-compose)
COPY . .

# 5. EXPOSICIÓN Y EJECUCIÓN
EXPOSE 8000
CMD ["uvicorn", "guard:app", "--host", "0.0.0.0", "--port", "8000"]