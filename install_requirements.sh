#!/bin/bash

# Script de instalación para el Sistema OCR de Bajos Recursos
# Instala todas las dependencias necesarias en Ubuntu

set -e  # Salir si hay algún error

echo "==================================================================="
echo "  🔧 INSTALACIÓN DEL SISTEMA OCR DE BAJOS RECURSOS"
echo "  🚀 Nuevo Motor: OnnxTR para CPU Optimizado"
echo "==================================================================="
echo ""
echo "🌟 ${YELLOW}INSTALACIÓN CON UNA SOLA LÍNEA DESDE GITHUB:${NC}"
echo "curl -fsSL https://raw.githubusercontent.com/juancspjr/OcrAcorazado/main/install.sh | bash"
echo ""
echo "==================================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[ÉXITO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ADVERTENCIA]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para instalación desde GitHub
install_from_github() {
    echo "==================================================================="
    echo "  📥 INSTALACIÓN DESDE GITHUB"
    echo "==================================================================="
    
    # Verificar si git está instalado
    if ! command -v git &> /dev/null; then
        print_status "Instalando Git..."
        sudo apt-get update
        sudo apt-get install -y git
    fi
    
    # Clonar repositorio
    print_status "Clonando repositorio desde GitHub..."
    git clone https://github.com/juancspjr/OcrAcorazado.git
    cd OcrAcorazado
    
    print_success "Repositorio clonado exitosamente"
    
    # Hacer ejecutable el script de instalación
    chmod +x install_requirements.sh
    
    # Ejecutar instalación
    print_status "Iniciando instalación automática..."
    ./install_requirements.sh --skip-github
    
    exit 0
}

# Verificar si se está ejecutando desde GitHub
if [ "$1" != "--skip-github" ]; then
    # Verificar si estamos en un directorio vacío o sin el proyecto
    if [ ! -f "main.py" ] || [ ! -f "config.py" ]; then
        print_warning "No se detectaron archivos del proyecto OCR"
        echo ""
        echo "¿Desea instalar desde GitHub? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            install_from_github
        else
            print_error "Instalación cancelada. Asegúrese de estar en el directorio del proyecto."
            exit 1
        fi
    fi
fi

# Verificar si se ejecuta como root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecute este script como root. Use su usuario normal."
   exit 1
fi

# Actualizar repositorios del sistema
print_status "Actualizando repositorios del sistema..."
sudo apt update

# Instalar dependencias del sistema
print_status "Instalando dependencias del sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    pkg-config \
    build-essential \
    cmake \
    wget \
    curl \
    unzip \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev

print_success "Dependencias del sistema instaladas"

print_success "Dependencias del sistema instaladas correctamente"
print_status "Nota: Sistema migrado a OnnxTR - No requiere Tesseract"

# Crear entorno virtual Python
VENV_DIR="venv_ocr"
print_status "Creando entorno virtual Python en $VENV_DIR..."

if [ -d "$VENV_DIR" ]; then
    print_warning "El entorno virtual ya existe. Eliminando..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

print_success "Entorno virtual creado y activado"

# Actualizar pip dentro del entorno virtual
print_status "Actualizando pip..."
pip install --upgrade pip

# Función para limpiar instalación fallida
cleanup_failed_install() {
    print_warning "Limpiando instalación fallida..."
    rm -rf venv_ocr
    rm -rf __pycache__
    rm -rf *.pyc
    rm -rf .pytest_cache
    print_success "Limpieza completada"
}

# Instalar dependencias Python
print_status "Instalando dependencias Python..."

# Lista de paquetes Python necesarios
PYTHON_PACKAGES=(
    "opencv-python>=4.5.0"
    "onnxtr==0.7.1"
    "onnx>=1.15.0"
    "onnxruntime>=1.17.0"
    "Pillow>=9.0.0"
    "numpy>=1.21.0"
    "scikit-image>=0.19.0"
    "Flask>=2.0.0"
    "Werkzeug>=2.0.0"
    "click>=8.0.0"
    "markupsafe>=2.0.0"
    "itsdangerous>=2.0.0"
    "jinja2>=3.0.0"
    "flask-sqlalchemy>=3.0.0"
    "gunicorn>=21.0.0"
    "psycopg2-binary>=2.9.0"
    "email-validator>=2.0.0"
    "requests>=2.25.0"
)

for package in "${PYTHON_PACKAGES[@]}"; do
    print_status "Instalando $package..."
    if ! pip install "$package"; then
        print_error "Error instalando $package"
        cleanup_failed_install
        exit 1
    fi
done

# Instalar desde archivo requirements si existe
if [ -f "requirements_onnxtr.txt" ]; then
    print_status "Instalando dependencias adicionales desde requirements_onnxtr.txt..."
    if ! pip install -r requirements_onnxtr.txt; then
        print_error "Error instalando desde requirements_onnxtr.txt"
        cleanup_failed_install
        exit 1
    fi
fi

print_success "Todas las dependencias Python instaladas"

# Descargar modelos ONNX para independencia
print_status "Descargando modelos ONNX para almacenamiento local..."
if python download_models.py --download; then
    print_success "Modelos ONNX descargados exitosamente"
else
    print_warning "No se pudieron descargar algunos modelos ONNX (continuando con cache del sistema)"
fi

# Verificar instalaciones
print_status "Verificando instalaciones..."

# Crear script de prueba temporal
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
import sys

def test_imports():
    """Prueba la importación de todos los módulos necesarios"""
    modules = [
        'cv2',
        'onnxtr',
        'onnx',
        'onnxruntime',
        'PIL',
        'numpy',
        'skimage',
        'flask',
        'json',
        'pathlib',
        'logging'
    ]
    
    failed_imports = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def test_onnxtr():
    """Prueba la funcionalidad de OnnxTR"""
    try:
        from onnxtr.io import DocumentFile
        from onnxtr.models import ocr_predictor
        import cv2
        import numpy as np
        
        print("Inicializando OnnxTR (esto puede tomar un momento)...")
        
        # Crear imagen de prueba simple
        img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, 'TEST OCR', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Guardar imagen temporal
        cv2.imwrite('test_image.png', img)
        
        # FIX: Inicializar predictor OnnxTR con parámetros compatibles 0.7.1
        # REASON: Eliminamos parámetros inexistentes que causan error de API
        # IMPACT: Test funcional de OnnxTR sin errores de compatibilidad
        predictor = ocr_predictor(
            det_arch='db_resnet50',
            reco_arch='crnn_vgg16_bn'
        )
        
        # Procesar imagen
        doc = DocumentFile.from_images(['test_image.png'])
        result = predictor(doc)
        
        # Extraer texto
        text = ""
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    for word in line.words:
                        text += word.value + " "
        
        text = text.strip()
        
        # Limpiar archivo temporal
        import os
        os.remove('test_image.png')
        
        if 'TEST' in text.upper() or 'OCR' in text.upper():
            print("✅ OnnxTR OCR funcional")
            return True
        else:
            print(f"❌ OnnxTR no reconoció texto correctamente: '{text}'")
            return False
            
    except Exception as e:
        print(f"❌ Error probando OnnxTR: {e}")
        return False

if __name__ == "__main__":
    print("Probando importaciones de módulos...")
    imports_ok = test_imports()
    
    print("\nProbando funcionalidad de OnnxTR...")
    onnxtr_ok = test_onnxtr()
    
    if imports_ok and onnxtr_ok:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo para usar.")
        sys.exit(0)
    else:
        print("\n❌ Algunas pruebas fallaron. Revise la instalación.")
        sys.exit(1)
EOF

# Ejecutar pruebas
print_status "Ejecutando pruebas de verificación..."
python test_installation.py

if [ $? -eq 0 ]; then
    print_success "Todas las pruebas pasaron"
else
    print_error "Algunas pruebas fallaron"
    exit 1
fi

# Limpiar archivo de prueba
rm test_installation.py

# Crear script de activación
print_status "Creando script de activación..."
cat > activate_ocr.sh << 'EOF'
#!/bin/bash
# Script para activar el entorno OCR

echo "Activando entorno virtual OCR..."
source venv_ocr/bin/activate

echo "Entorno OCR activado. Para usar el sistema:"
echo ""
echo "  Línea de comandos:"
echo "    python main_ocr_process.py imagen.jpg --profile rapido"
echo ""
echo "  Servidor web:"
echo "    python app.py"
echo "    Luego abrir: http://localhost:5000"
echo ""
echo "Para desactivar el entorno use: deactivate"
EOF

chmod +x activate_ocr.sh

# Crear archivo de configuración de ejemplo
print_status "Creando archivo de configuración de ejemplo..."
cat > .env.example << 'EOF'
# Configuración de ejemplo para el sistema OCR
# Copie este archivo a .env y ajuste según necesite

# Configuración de sesión Flask
SESSION_SECRET=your_secret_key_here

# Configuración de logging
LOG_LEVEL=DEBUG

# Configuración de OnnxTR (opcional)
ONNXTR_CACHE_DIR=/home/runner/.cache/onnxtr
ONNXTR_DOWNLOAD_TIMEOUT=300

# Configuración de base de datos (opcional)
DATABASE_URL=postgresql://user:password@localhost/dbname
EOF

# Mostrar información final
echo ""
print_success "🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo ""
echo "==================================================================="
echo "  📋 INSTRUCCIONES DE USO"
echo "==================================================================="
echo ""
echo "1. Para activar el entorno virtual:"
echo "   ${YELLOW}source venv_ocr/bin/activate${NC}"
echo "   o use: ${YELLOW}./activate_ocr.sh${NC}"
echo ""
echo "2. Para usar por línea de comandos:"
echo "   ${YELLOW}python main_ocr_process.py imagen.jpg --profile rapido${NC}"
echo ""
echo "3. Para iniciar el servidor web:"
echo "   ${YELLOW}python main.py${NC}"
echo "   o para producción: ${YELLOW}gunicorn --bind 0.0.0.0:5000 main:app${NC}"
echo "   Luego abrir: ${YELLOW}http://localhost:5000${NC}"
echo ""
echo "4. Perfiles disponibles:"
echo "   • ultra_rapido: Máxima velocidad"
echo "   • rapido: Balance velocidad/calidad (recomendado)"
echo "   • normal: Máxima calidad"
echo ""
echo "5. Para más opciones:"
echo "   ${YELLOW}python main_ocr_process.py --help${NC}"
echo ""
echo "==================================================================="
echo "  📁 ARCHIVOS IMPORTANTES"
echo "==================================================================="
echo ""
echo "• activate_ocr.sh     - Script para activar entorno"
echo "• .env.example        - Configuración de ejemplo"
echo "• venv_ocr/           - Entorno virtual Python"
echo "• uploads/            - Imágenes cargadas"
echo "• temp/               - Archivos temporales"
echo ""
echo "==================================================================="
echo "  🌐 GUÍA DE USO WEB LOCAL"
echo "==================================================================="
echo ""
echo "1. ${YELLOW}Iniciar servidor web:${NC}"
echo "   source venv_ocr/bin/activate"
echo "   python main.py"
echo ""
echo "2. ${YELLOW}Acceder a la aplicación:${NC}"
echo "   Abrir navegador en: ${YELLOW}http://localhost:5000${NC}"
echo "   o desde otra máquina: ${YELLOW}http://IP_DEL_SERVIDOR:5000${NC}"
echo ""
echo "3. ${YELLOW}Usar la interfaz web:${NC}"
echo "   • Seleccionar archivo de imagen"
echo "   • Elegir perfil de procesamiento (ultra_rapido/rapido/normal)"
echo "   • Hacer clic en 'Procesar Imagen'"
echo "   • Ver resultados con texto extraído y estadísticas"
echo ""
echo "==================================================================="
echo "  ⚡ LÍNEA DE COMANDOS COMPLETA (Para n8n y automatización)"
echo "==================================================================="
echo ""
echo "${YELLOW}Uso básico:${NC}"
echo "python main_ocr_process.py imagen.jpg"
echo ""
echo "${YELLOW}Opciones completas:${NC}"
echo "python main_ocr_process.py imagen.jpg \\"
echo "  --language spa \\"
echo "  --profile rapido \\"
echo "  --save-intermediate \\"
echo "  --output-dir /path/output \\"
echo "  --json-only"
echo ""
echo "${YELLOW}Parámetros disponibles:${NC}"
echo "• imagen.jpg          - Ruta a la imagen (requerido)"
echo "• --language, -l      - Idioma: spa, eng (default: spa)"
echo "• --profile, -p       - Perfil: ultra_rapido, rapido, normal"
echo "• --save-intermediate - Guardar archivos procesados"
echo "• --output-dir, -o    - Directorio de salida personalizado"
echo "• --json-only, -j     - Solo devolver JSON (ideal para n8n)"
echo ""
echo "${YELLOW}Ejemplos para n8n:${NC}"
echo ""
echo "# OCR rápido con JSON:"
echo "python main_ocr_process.py imagen.jpg --json-only"
echo ""
echo "# OCR completo con archivos guardados:"
echo "python main_ocr_process.py imagen.jpg --profile normal --save-intermediate --output-dir ./resultados"
echo ""
echo "# OCR de documento en inglés:"
echo "python main_ocr_process.py document.png --language eng --profile normal --json-only"
echo ""
echo "${YELLOW}Resultado JSON incluye:${NC}"
echo "• execution_id        - ID único de ejecución"
echo "• tiempo_total        - Tiempo de procesamiento"
echo "• texto_extraido      - Texto completo extraído"
echo "• confianza_promedio  - Nivel de confianza OCR"
echo "• datos_financieros   - Información financiera estructurada"
echo "• estadisticas_ocr    - Métricas detalladas"
echo "• temp_directory      - Ubicación archivos temporales"
echo ""
echo "==================================================================="
echo "  🔧 CONFIGURACIÓN PARA PRODUCCIÓN"
echo "==================================================================="
echo ""
echo "${YELLOW}Para ejecutar como servicio:${NC}"
echo ""
echo "1. Crear archivo de servicio systemd:"
echo "   sudo nano /etc/systemd/system/ocr-web.service"
echo ""
echo "2. Contenido del archivo:"
echo "[Unit]"
echo "Description=Sistema OCR Web"
echo "After=network.target"
echo ""
echo "[Service]"
echo "Type=simple"
echo "User=$(whoami)"
echo "WorkingDirectory=$(pwd)"
echo "Environment=PATH=$(pwd)/venv_ocr/bin"
echo "ExecStart=$(pwd)/venv_ocr/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app"
echo "Restart=always"
echo ""
echo "[Install]"
echo "WantedBy=multi-user.target"
echo ""
echo "3. Activar servicio:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable ocr-web"
echo "   sudo systemctl start ocr-web"
echo ""
echo "${YELLOW}Para configurar firewall:${NC}"
echo "sudo ufw allow 5000/tcp"
echo ""
print_warning "Recuerde activar el entorno virtual antes de usar el sistema"
echo ""
