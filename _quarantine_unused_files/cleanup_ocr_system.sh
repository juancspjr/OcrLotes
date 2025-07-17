#!/bin/bash

# cleanup_ocr_system.sh - Complete OCR System Cleanup Script
# Use this script to completely reset the OCR system in case of installation problems

echo "🧹 Iniciando limpieza completa del sistema OCR..."

# 1. Remove virtual environment
if [ -d "venv_ocr" ]; then
    echo "Eliminando entorno virtual venv_ocr..."
    rm -rf venv_ocr
    echo "✅ Entorno virtual eliminado"
else
    echo "ℹ️  No se encontró entorno virtual venv_ocr"
fi

# 2. Remove temporary files
echo "Limpiando archivos temporales..."
rm -rf temp/*
rm -rf uploads/*
rm -rf __pycache__
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Archivos temporales eliminados"

# 3. Remove downloaded models (if corrupted)
if [ -d "models" ]; then
    echo "Eliminando modelos ONNX descargados..."
    rm -rf models/onnxtr/*
    echo "✅ Modelos eliminados"
else
    echo "ℹ️  No se encontraron modelos descargados"
fi

# 4. Remove pip cache
echo "Limpiando cache de pip..."
rm -rf ~/.cache/pip
echo "✅ Cache de pip eliminado"

# 5. Remove ONNX cache
echo "Limpiando cache de ONNX..."
rm -rf ~/.cache/onnxtr
echo "✅ Cache de ONNX eliminado"

# 6. Remove any lock files
echo "Eliminando archivos de bloqueo..."
rm -f ./*.lock
rm -f pip-selfcheck.json
echo "✅ Archivos de bloqueo eliminados"

# 7. Reset permissions
echo "Restableciendo permisos de scripts..."
chmod +x install_requirements.sh
chmod +x install.sh 2>/dev/null || true
chmod +x cleanup_ocr_system.sh
echo "✅ Permisos restablecidos"

# 8. Create necessary directories
echo "Creando directorios necesarios..."
mkdir -p temp uploads static models/onnxtr
echo "✅ Directorios creados"

# 9. Show system info
echo ""
echo "📊 Información del sistema:"
echo "Python version: $(python3 --version 2>/dev/null || echo 'Python3 not found')"
echo "Pip version: $(pip3 --version 2>/dev/null || echo 'Pip3 not found')"
echo "Available space: $(df -h . | tail -1 | awk '{print $4}')"

echo ""
echo "✅ Limpieza completa finalizada"
echo ""
echo "🚀 Próximos pasos:"
echo "1. Ejecutar: ./install_requirements.sh"
echo "2. Activar entorno: source venv_ocr/bin/activate"
echo "3. Verificar instalación: python download_models.py --verify"
echo "4. Iniciar aplicación: python main.py"