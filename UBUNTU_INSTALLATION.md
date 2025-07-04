# Instalación en Ubuntu Server - Sistema OCR con OnnxTR

## Requisitos del Sistema

- Ubuntu Server 20.04 LTS o superior
- Mínimo 2GB RAM (recomendado 4GB)
- 2GB espacio libre en disco
- Conexión a internet
- Acceso SSH con privilegios sudo

## Instalación Paso a Paso

### 1. Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias del Sistema

```bash
# Instalar Python 3.11 y herramientas básicas
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential pkg-config
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y git curl wget unzip

# Instalar librerías para procesamiento de imágenes
sudo apt install -y libjpeg-dev libpng-dev libtiff-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt install -y libgtk2.0-dev libcanberra-gtk-module
```

### 3. Crear Usuario y Directorio del Sistema

```bash
# Crear usuario específico para la aplicación (opcional pero recomendado)
sudo useradd -m -s /bin/bash ocruser
sudo usermod -aG sudo ocruser

# Cambiar al usuario (o continuar con tu usuario actual)
sudo su - ocruser

# Crear directorio de trabajo
mkdir -p ~/ocr-system
cd ~/ocr-system
```

### 4. Clonar o Transferir el Código

```bash
# Opción A: Si tienes el código en Git
git clone [TU_REPOSITORIO_URL] .

# Opción B: Si transfieres archivos por SCP/SFTP
# Desde tu máquina local:
# scp -r /path/to/your/ocr-system/* usuario@servidor:~/ocr-system/

# Dar permisos de ejecución
chmod +x *.py
```

### 5. Configurar Entorno Virtual Python

```bash
# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel
```

### 6. Instalar Dependencias Python

```bash
# Instalar dependencias desde requirements
pip install -r requirements_onnxtr.txt

# Si hay problemas con algunas dependencias, instalar individualmente:
pip install flask flask-sqlalchemy gunicorn
pip install opencv-python pillow numpy scipy
pip install onnxtr onnx onnxruntime
pip install scikit-image psycopg2-binary
```

### 7. Configurar Variables de Entorno

```bash
# Crear archivo de configuración
cat > .env << 'EOF'
# Configuración Flask
SESSION_SECRET=$(openssl rand -hex 32)
FLASK_ENV=production
FLASK_DEBUG=false

# Configuración de base de datos (opcional)
# DATABASE_URL=postgresql://user:password@localhost/ocr_db

# Configuración del servidor
HOST=0.0.0.0
PORT=5000
EOF

# Cargar variables de entorno
source .env
export SESSION_SECRET=$(grep SESSION_SECRET .env | cut -d'=' -f2)
```

### 8. Crear Directorios Necesarios

```bash
# Crear directorios de trabajo
mkdir -p uploads temp static/results
mkdir -p logs

# Dar permisos apropiados
chmod 755 uploads temp static
chmod 777 temp  # Temporal necesita escritura completa
```

### 9. Probar la Instalación

```bash
# Activar entorno virtual si no está activo
source venv/bin/activate

# Probar que las dependencias se importan correctamente
python3 -c "import cv2, onnxtr, flask; print('Dependencias OK')"

# Probar la aplicación
python3 main.py
```

### 10. Configurar Servicio Systemd (Recomendado)

```bash
# Crear archivo de servicio
sudo tee /etc/systemd/system/ocr-system.service > /dev/null << 'EOF'
[Unit]
Description=Sistema OCR con OnnxTR
After=network.target

[Service]
Type=simple
User=ocruser
Group=ocruser
WorkingDirectory=/home/ocruser/ocr-system
Environment=PATH=/home/ocruser/ocr-system/venv/bin
EnvironmentFile=/home/ocruser/ocr-system/.env
ExecStart=/home/ocruser/ocr-system/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl enable ocr-system
sudo systemctl start ocr-system

# Verificar estado
sudo systemctl status ocr-system
```

### 11. Configurar Firewall (Opcional)

```bash
# Permitir tráfico en puerto 5000
sudo ufw allow 5000/tcp

# Si usas proxy reverso con Nginx/Apache
sudo ufw allow 'Nginx Full'  # o 'Apache Full'
```

### 12. Configurar Proxy Reverso con Nginx (Opcional)

```bash
# Instalar Nginx
sudo apt install -y nginx

# Crear configuración
sudo tee /etc/nginx/sites-available/ocr-system > /dev/null << 'EOF'
server {
    listen 80;
    server_name tu-dominio.com;  # Cambiar por tu dominio o IP

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /static {
        alias /home/ocruser/ocr-system/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/ocr-system /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl restart nginx
```

## Verificación de la Instalación

### 1. Verificar Servicios

```bash
# Verificar que el servicio está corriendo
sudo systemctl status ocr-system

# Ver logs en tiempo real
sudo journalctl -u ocr-system -f

# Verificar que el puerto está abierto
sudo netstat -tlnp | grep :5000
```

### 2. Probar la Aplicación

```bash
# Desde el servidor
curl http://localhost:5000

# Desde otro equipo (cambiar IP)
curl http://IP_DEL_SERVIDOR:5000
```

### 3. Probar OCR con Imagen de Prueba

```bash
# Cargar una imagen de prueba y verificar que el procesamiento funciona
# Acceder a: http://IP_DEL_SERVIDOR:5000
# Subir una imagen y verificar resultados
```

## Mantenimiento

### Actualizar el Sistema

```bash
# Detener servicio
sudo systemctl stop ocr-system

# Actualizar código
cd ~/ocr-system
git pull  # o transferir nuevos archivos

# Actualizar dependencias si es necesario
source venv/bin/activate
pip install --upgrade -r requirements_onnxtr.txt

# Reiniciar servicio
sudo systemctl start ocr-system
```

### Monitoreo de Logs

```bash
# Logs del servicio
sudo journalctl -u ocr-system -f

# Logs de Nginx (si se usa)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup

```bash
# Hacer backup de la configuración
tar -czf ocr-system-backup-$(date +%Y%m%d).tar.gz \
    ~/ocr-system/*.py \
    ~/ocr-system/.env \
    ~/ocr-system/requirements_onnxtr.txt \
    ~/ocr-system/static \
    ~/ocr-system/templates
```

## Solución de Problemas

### Error de Dependencias

```bash
# Reinstalar dependencias
source venv/bin/activate
pip install --force-reinstall -r requirements_onnxtr.txt
```

### Error de Permisos

```bash
# Dar permisos apropiados
sudo chown -R ocruser:ocruser ~/ocr-system
chmod -R 755 ~/ocr-system
chmod 777 ~/ocr-system/temp
```

### Error de Memoria

```bash
# Verificar uso de memoria
free -h
htop

# Ajustar workers de Gunicorn si es necesario
# Editar /etc/systemd/system/ocr-system.service
# Cambiar --workers 2 por --workers 1
```

### Puerto en Uso

```bash
# Verificar qué usa el puerto
sudo lsof -i :5000
sudo netstat -tlnp | grep :5000

# Cambiar puerto en .env si es necesario
echo "PORT=5001" >> .env
```

## Seguridad

### Configuración Básica

```bash
# Cambiar clave de sesión regularmente
sed -i "s/SESSION_SECRET=.*/SESSION_SECRET=$(openssl rand -hex 32)/" .env

# Limitar acceso a archivos sensibles
chmod 600 .env
chmod 700 ~/ocr-system/logs
```

### Configuración Avanzada

```bash
# Configurar fail2ban para proteger SSH
sudo apt install -y fail2ban

# Configurar firewall restrictivo
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 5000/tcp  # o 80/tcp si usas Nginx
sudo ufw enable
```

## Rendimiento

### Optimización del Sistema

```bash
# Aumentar límites de archivos si es necesario
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Configurar swap si hay poca RAM
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

¡La instalación está completa! El sistema OCR debería estar funcionando en `http://TU_IP:5000`