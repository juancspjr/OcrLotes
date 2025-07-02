#!/bin/bash

# OCR System Performance Optimization Test Script
# Validates all optimizations and generates performance report

echo "🎯 OCR System - Optimización y Pruebas de Rendimiento"
echo "======================================================"
echo ""

# Check if Python environment is set up
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask no está instalado. Ejecuta: pip install flask"
    exit 1
fi

# Check for required dependencies
echo "🔍 Verificando dependencias..."
missing_deps=()

for dep in "psutil" "numpy" "opencv-python" "pytesseract"; do
    if ! python -c "import ${dep//-/_}" 2>/dev/null; then
        missing_deps+=("$dep")
    fi
done

if [ ${#missing_deps[@]} -gt 0 ]; then
    echo "⚠️  Dependencias faltantes: ${missing_deps[*]}"
    echo "💡 Ejecuta: pip install ${missing_deps[*]}"
    echo ""
fi

# Test 1: Quick startup test
echo "🚀 Test 1: Tiempo de startup optimizado"
echo "----------------------------------------"
time_start=$(python -c "import time; print(time.time())")
python -c "import app" 2>/dev/null
time_end=$(python -c "import time; print(time.time())")
startup_time=$(python -c "print(round($time_end - $time_start, 3))")

if (( $(echo "$startup_time < 1.0" | bc -l) )); then
    echo "✅ Startup time: ${startup_time}s (Excelente - <1s)"
elif (( $(echo "$startup_time < 2.0" | bc -l) )); then
    echo "⚠️  Startup time: ${startup_time}s (Bueno - <2s)"
else
    echo "❌ Startup time: ${startup_time}s (Necesita optimización - >2s)"
fi
echo ""

# Test 2: Config cache performance
echo "🗄️  Test 2: Performance del cache de configuración"
echo "----------------------------------------------------"
python -c "
import time
import config

# Test cache performance
start = time.time()
for _ in range(10):
    config.get_tesseract_config()
    config.get_performance_profiles()
first_run = time.time() - start

start = time.time()
for _ in range(10):
    config.get_tesseract_config()
    config.get_performance_profiles()
cached_run = time.time() - start

speedup = first_run / cached_run if cached_run > 0 else float('inf')
print(f'Primera ejecución: {first_run:.4f}s')
print(f'Con cache: {cached_run:.4f}s')
print(f'Speedup: {speedup:.1f}x')

if speedup > 5:
    print('✅ Cache funcionando correctamente')
else:
    print('⚠️  Cache podría mejorarse')
"
echo ""

# Test 3: Memory usage
echo "💾 Test 3: Uso de memoria optimizado"
echo "-------------------------------------"
python -c "
import psutil
import sys

process = psutil.Process()
initial_memory = process.memory_info().rss / 1024**2

# Import heavy modules
import config
import routes
from main_ocr_process import OrquestadorOCR

# Create instance (lazy loading test)
orquestador = OrquestadorOCR()

final_memory = process.memory_info().rss / 1024**2
increase = final_memory - initial_memory

print(f'Memoria inicial: {initial_memory:.1f} MB')
print(f'Memoria final: {final_memory:.1f} MB')
print(f'Incremento: {increase:.1f} MB')

if increase < 100:
    print('✅ Uso de memoria optimizado (<100MB)')
elif increase < 200:
    print('⚠️  Uso de memoria moderado (<200MB)')
else:
    print('❌ Alto uso de memoria (>200MB)')
"
echo ""

# Test 4: Bundle size analysis
echo "📦 Test 4: Análisis de tamaño del bundle"
echo "-----------------------------------------"

if [ -f "static/css/custom.min.css" ]; then
    original_css=$(stat -f%z "static/css/custom.css" 2>/dev/null || stat -c%s "static/css/custom.css" 2>/dev/null || echo "0")
    minified_css=$(stat -f%z "static/css/custom.min.css" 2>/dev/null || stat -c%s "static/css/custom.min.css" 2>/dev/null || echo "0")
    
    if [ "$original_css" -gt 0 ] && [ "$minified_css" -gt 0 ]; then
        reduction=$(python -c "print(round((1 - $minified_css / $original_css) * 100, 1))")
        echo "✅ CSS minificado: $reduction% reducción (${original_css} → ${minified_css} bytes)"
    fi
else
    echo "⚠️  Archivo CSS minificado no encontrado"
fi

if [ -f "static/js/main.opt.js" ]; then
    echo "✅ JavaScript optimizado disponible"
else
    echo "⚠️  JavaScript optimizado no encontrado"
fi
echo ""

# Test 5: Run comprehensive performance test
echo "🧪 Test 5: Análisis completo de rendimiento"
echo "--------------------------------------------"
if [ -f "performance_test.py" ]; then
    echo "Ejecutando análisis completo..."
    python performance_test.py
    
    if [ -f "performance_report.json" ]; then
        echo ""
        echo "📊 Reporte detallado generado: performance_report.json"
        echo "🔍 Resumen de optimizaciones:"
        
        # Extract key metrics from report
        python -c "
import json
try:
    with open('performance_report.json', 'r') as f:
        data = json.load(f)
    
    print('   • Startup time:', data.get('tests', {}).get('startup', {}).get('import_time_seconds', 'N/A'), 's')
    print('   • Memory increase:', data.get('tests', {}).get('memory', {}).get('increase_mb', 'N/A'), 'MB')
    print('   • Bundle size:', data.get('tests', {}).get('bundle_size', {}).get('total_mb', 'N/A'), 'MB')
    
    if 'summary' in data:
        print('')
        print('📋 Recomendaciones:')
        for rec in data['summary'].get('recommendations', []):
            print(f'   • {rec}')
            
except Exception as e:
    print(f'Error leyendo reporte: {e}')
"
    fi
else
    echo "⚠️  performance_test.py no encontrado"
fi

echo ""
echo "🎉 Pruebas de optimización completadas!"
echo ""
echo "📈 Para monitoreo continuo:"
echo "   • Ejecuta: python performance_test.py"
echo "   • Revisa: performance_report.json"
echo "   • Monitorea uso de memoria en producción"
echo ""
echo "💡 Próximos pasos de optimización:"
echo "   • Implementar cache Redis para imágenes procesadas"
echo "   • Configurar CDN para assets estáticos"
echo "   • Considerar microservicios para OCR processing"