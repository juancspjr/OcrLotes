# Instalación Rápida en Ubuntu Server

## Método 1: Instalación Automática (Recomendado)

### 1. Descargar el script de instalación
```bash
# Conectarse al servidor por SSH
ssh usuario@tu-servidor

# Descargar archivos del proyecto
# (Transferir todos los archivos del proyecto al servidor)

# Dar permisos de ejecución al script
chmod +x install-ubuntu.sh
```

### 2. Ejecutar instalación automática
```bash
# Ejecutar script de instalación
sudo ./install-ubuntu.sh
```

### 3. Copiar archivos de la aplicación
```bash
# El script crea el directorio ~/ocr-system
# Copiar todos los archivos Python y templates ahí:
cp *.py ~/ocr-system/
cp -r templates ~/ocr-system/
cp -r static ~/ocr-system/
```

### 4. Iniciar el servicio
```bash
cd ~/ocr-system
./service.sh enable    # Habilitar inicio automático
./service.sh start     # Iniciar servicio
./service.sh status    # Verificar estado
```

## Método 2: Instalación Manual

### 1. Preparar el sistema
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y build-essential libopencv-dev python3-opencv
sudo apt install -y git curl wget
```

### 2. Configurar aplicación
```bash
# Crear directorio
mkdir -p ~/ocr-system
cd ~/ocr-system

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements_onnxtr.txt

# Crear configuración
echo "SESSION_SECRET=$(openssl rand -hex 32)" > .env
echo "FLASK_ENV=production" >> .env
echo "HOST=0.0.0.0" >> .env
echo "PORT=5000" >> .env

# Crear directorios
mkdir -p uploads temp static/results logs
chmod 777 temp
```

### 3. Copiar archivos de la aplicación
```bash
# Copiar todos los archivos Python
# Copiar directorio templates
# Copiar directorio static
```

### 4. Iniciar aplicación
```bash
# Activar entorno virtual
source venv/bin/activate

# Cargar configuración
source .env

# Iniciar aplicación
python3 main.py
```

## Verificación

### Comprobar que funciona
```bash
# Verificar servicio
curl http://localhost:5000

# Verificar desde otro equipo
curl http://IP_DEL_SERVIDOR:5000
```

### Ver logs
```bash
# Si usa servicio systemd
sudo journalctl -u ocr-system -f

# Si ejecuta manualmente
# Los logs aparecen en la consola
```

## Acceso a la Aplicación

Una vez instalado, acceder a:
```
http://IP_DEL_SERVIDOR:5000
```

## Comandos Útiles

```bash
# Controlar servicio
~/ocr-system/service.sh start      # Iniciar
~/ocr-system/service.sh stop       # Detener
~/ocr-system/service.sh restart    # Reiniciar
~/ocr-system/service.sh status     # Estado
~/ocr-system/service.sh logs       # Ver logs

# Actualizar aplicación
cd ~/ocr-system
git pull  # Si usas git
sudo systemctl restart ocr-system

# Verificar estado del sistema
free -h        # Memoria disponible
df -h          # Espacio en disco
htop           # Procesos en ejecución
```

## Solución de Problemas

### Error: Puerto en uso
```bash
# Cambiar puerto en .env
echo "PORT=5001" >> ~/ocr-system/.env
~/ocr-system/service.sh restart
```

### Error: Sin permisos
```bash
# Dar permisos apropiados
sudo chown -R $USER:$USER ~/ocr-system
chmod 777 ~/ocr-system/temp
```

### Error: Dependencias
```bash
# Reinstalar dependencias
cd ~/ocr-system
source venv/bin/activate
pip install --force-reinstall -r requirements_onnxtr.txt
```

### Error: Memoria insuficiente
```bash
# Crear swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Configuración de Producción

### Proxy Reverso con Nginx
```bash
# Instalar Nginx
sudo apt install -y nginx

# Configurar sitio
sudo nano /etc/nginx/sites-available/ocr-system

# Contenido del archivo:
server {
    listen 80;
    server_name tu-dominio.com;
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Activar sitio
sudo ln -s /etc/nginx/sites-available/ocr-system /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Firewall
```bash
# Configurar firewall básico
sudo ufw allow ssh
sudo ufw allow 5000/tcp  # o 80/tcp si usas Nginx
sudo ufw enable
```

¡Listo! Tu sistema OCR estará funcionando en el servidor Ubuntu.