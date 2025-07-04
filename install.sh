#!/bin/bash

# Instalación con Una Sola Línea - Sistema OCR de Bajos Recursos
# Ejecutar con: curl -fsSL https://raw.githubusercontent.com/juancspjr/OcrAcorazado/main/install.sh | bash

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "==================================================================="
echo "  🚀 INSTALACIÓN AUTOMÁTICA DESDE GITHUB"
echo "  📦 Sistema OCR de Bajos Recursos con OnnxTR"
echo "==================================================================="

# Verificar si se ejecuta como root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecute este script como root. Use su usuario normal."
   exit 1
fi

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    print_status "Instalando Git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# Crear directorio de instalación
INSTALL_DIR="$HOME/OcrAcorazado"
if [ -d "$INSTALL_DIR" ]; then
    print_warning "El directorio $INSTALL_DIR ya existe"
    echo "¿Desea eliminar y reinstalar? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        print_error "Instalación cancelada"
        exit 1
    fi
fi

# Clonar repositorio
print_status "Clonando repositorio desde GitHub..."
git clone https://github.com/juancspjr/OcrAcorazado.git "$INSTALL_DIR"
cd "$INSTALL_DIR"

print_success "Repositorio clonado exitosamente"

# Hacer ejecutable el script de instalación
chmod +x install_requirements.sh

# Ejecutar instalación
print_status "Iniciando instalación automática..."
./install_requirements.sh --skip-github

print_success "¡Instalación completada exitosamente!"
echo ""
echo "==================================================================="
echo "  🎉 INSTALACIÓN TERMINADA"
echo "==================================================================="
echo ""
echo "Para usar el sistema:"
echo ""
echo "1. ${YELLOW}Navegar al directorio:${NC}"
echo "   cd $INSTALL_DIR"
echo ""
echo "2. ${YELLOW}Activar entorno:${NC}"
echo "   source venv_ocr/bin/activate"
echo ""
echo "3. ${YELLOW}Iniciar servidor web:${NC}"
echo "   python main.py"
echo "   # Abrir: http://localhost:5000"
echo ""
echo "4. ${YELLOW}Usar línea de comandos:${NC}"
echo "   python main_ocr_process.py imagen.jpg --json-only"
echo ""
echo "==================================================================="