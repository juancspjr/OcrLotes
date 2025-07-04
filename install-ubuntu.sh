#!/bin/bash

# Script de Instalación Automática - Sistema OCR con OnnxTR
# Para Ubuntu Server 20.04+ 

set -e  # Salir si hay algún error

echo "=== Instalación Sistema OCR con OnnxTR ==="
echo "Iniciando instalación automática..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si se ejecuta con sudo para ciertas operaciones
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_error "Este script necesita permisos sudo. Por favor ejecuta: sudo ./install-ubuntu.sh"
        exit 1
    fi
}

# Paso 1: Actualizar sistema
log_info "Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Paso 2: Instalar dependencias del sistema
log_info "Instalando dependencias del sistema..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential pkg-config
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y git curl wget unzip
sudo apt install -y libjpeg-dev libpng-dev libtiff-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt install -y libgtk2.0-dev libcanberra-gtk-module

# Paso 3: Crear directorio de trabajo
log_info "Configurando directorio de trabajo..."
INSTALL_DIR="$HOME/ocr-system"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Paso 4: Crear entorno virtual
log_info "Creando entorno virtual Python..."
python3.11 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel

# Paso 5: Crear requirements.txt si no existe
if [ ! -f "requirements_onnxtr.txt" ]; then
    log_info "Creando archivo requirements_onnxtr.txt..."
    cat > requirements_onnxtr.txt << 'EOF'
click==8.1.7
email-validator==2.0.0
flask==3.0.0
flask-sqlalchemy==3.1.1
gunicorn==21.2.0
itsdangerous==2.1.2
jinja2==3.1.2
markupsafe==2.1.3
numpy==1.24.3
onnx==1.15.0
onnxruntime==1.16.3
onnxtr==0.8.1
opencv-python==4.8.1.78
pillow==10.0.1
psycopg2-binary==2.9.9
scikit-image==0.21.0
scipy==1.11.4
werkzeug==3.0.1
EOF
fi

# Paso 6: Instalar dependencias Python
log_info "Instalando dependencias Python..."
pip install -r requirements_onnxtr.txt

# Paso 7: Crear archivos de configuración
log_info "Creando configuración..."

# Crear .env
cat > .env << EOF
SESSION_SECRET=$(openssl rand -hex 32)
FLASK_ENV=production
FLASK_DEBUG=false
HOST=0.0.0.0
PORT=5000
EOF

# Crear directorios necesarios
mkdir -p uploads temp static/results logs
chmod 755 uploads temp static
chmod 777 temp

# Paso 8: Crear archivos principales si no existen
if [ ! -f "main.py" ]; then
    log_info "Creando archivo main.py básico..."
    cat > main.py << 'EOF'
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
fi

# Paso 9: Crear servicio systemd
log_info "Configurando servicio systemd..."
USER=$(whoami)
sudo tee /etc/systemd/system/ocr-system.service > /dev/null << EOF
[Unit]
Description=Sistema OCR con OnnxTR
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
sudo systemctl daemon-reload

# Paso 10: Configurar firewall básico
log_info "Configurando firewall..."
sudo ufw --force enable
sudo ufw allow 5000/tcp

# Paso 11: Probar instalación
log_info "Probando instalación..."
source venv/bin/activate
python3 -c "import cv2, onnxtr, flask; print('Dependencias verificadas correctamente')"

# Paso 12: Crear script de inicio
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
source .env
python3 main.py
EOF
chmod +x start.sh

# Paso 13: Crear script de servicio
cat > service.sh << 'EOF'
#!/bin/bash
case "$1" in
    start)
        sudo systemctl start ocr-system
        echo "Servicio iniciado"
        ;;
    stop)
        sudo systemctl stop ocr-system
        echo "Servicio detenido"
        ;;
    restart)
        sudo systemctl restart ocr-system
        echo "Servicio reiniciado"
        ;;
    status)
        sudo systemctl status ocr-system
        ;;
    enable)
        sudo systemctl enable ocr-system
        echo "Servicio habilitado para inicio automático"
        ;;
    disable)
        sudo systemctl disable ocr-system
        echo "Servicio deshabilitado del inicio automático"
        ;;
    logs)
        sudo journalctl -u ocr-system -f
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|enable|disable|logs}"
        exit 1
        ;;
esac
EOF
chmod +x service.sh

# Mostrar resumen de instalación
echo ""
echo "=== INSTALACIÓN COMPLETADA ==="
log_info "Directorio de instalación: $INSTALL_DIR"
log_info "Archivos creados:"
echo "  - venv/                 (entorno virtual Python)"
echo "  - .env                  (configuración)"
echo "  - requirements_onnxtr.txt (dependencias)"
echo "  - start.sh              (script de inicio manual)"
echo "  - service.sh            (script de control del servicio)"
echo "  - uploads/              (directorio para imágenes)"
echo "  - temp/                 (directorio temporal)"
echo "  - static/               (archivos estáticos)"
echo ""

echo "=== PRÓXIMOS PASOS ==="
echo "1. Copiar los archivos de tu aplicación OCR a: $INSTALL_DIR"
echo "   - app.py"
echo "   - routes.py"
echo "   - config.py"
echo "   - aplicador_ocr.py"
echo "   - mejora_ocr.py"
echo "   - validador_ocr.py"
echo "   - main_ocr_process.py"
echo "   - templates/ (directorio)"
echo ""

echo "2. Habilitar e iniciar el servicio:"
echo "   cd $INSTALL_DIR"
echo "   ./service.sh enable"
echo "   ./service.sh start"
echo ""

echo "3. Verificar funcionamiento:"
echo "   ./service.sh status"
echo "   curl http://localhost:5000"
echo ""

echo "4. Ver logs:"
echo "   ./service.sh logs"
echo ""

echo "5. Acceder a la aplicación:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""

log_info "Instalación base completada. Ahora copia los archivos de tu aplicación."