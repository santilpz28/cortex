FROM php:8.2-apache

# Instalar dependencias de sistema para CURL
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar extensiones PHP necesarias
RUN docker-php-ext-install curl 

#json

# Habilitar mod_rewrite (buena práctica)
RUN a2enmod rewrite

# Copiar el código web
COPY . /var/www/html/

# Asegurar permisos
RUN chown -R www-data:www-data /var/www/html/

EXPOSE 80