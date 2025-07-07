#!/usr/bin/env python3
"""
Test completo del MANDATO DE DIAGNÓSTICO PROFUNDO Y RECTIFICACIÓN FINAL
Aplica filosofía de INTEGRIDAD TOTAL Y PERFECCIÓN CONTINUA
"""

import sys
import os
import json
import time
from pathlib import Path

# Añadir el directorio actual al path
sys.path.insert(0, os.getcwd())

# Importar módulos del sistema
from aplicador_ocr import AplicadorOCR
from PIL import Image, ImageDraw, ImageFont
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def crear_imagen_test_mandato():
    """
    Crear imagen de prueba con el patrón problemático "2/ 061025"
    MANDATO: Simular texto OCR con problemas de interpretación '7' como '/'
    """
    # Crear imagen de 720x400 pixels con fondo blanco
    img = Image.new('RGB', (720, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Usar fuente por defecto
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Texto que simula el recibo problemático
    texto_recibo = [
        "A Personas 104,54 Bs",
        "Fecha : 20/06/ 2025",
        "Operacion; 003039387344",
        "I - Identificacion : 2/ 061025",  # PATRÓN PROBLEMÁTICO
        "Origen : 0102 **** 2679",
        "Destino : 04125318244",
        "Banco : 0105 - BANCO MERCANTIL"
    ]
    
    # Dibujar texto línea por línea
    y_pos = 50
    for linea in texto_recibo:
        draw.text((50, y_pos), linea, fill='black', font=font)
        y_pos += 35
    
    # Guardar imagen
    test_image_path = "test_imagen_mandato_completo.png"
    img.save(test_image_path)
    logger.info(f"✅ Imagen de prueba creada: {test_image_path}")
    
    return test_image_path

def ejecutar_test_mandato_completo():
    """
    MANDATO PRINCIPAL: Ejecutar test completo de rectificación
    1. Crear imagen con patrón problemático
    2. Procesar con OCR
    3. Validar correcciones implementadas
    """
    logger.info("🎯 INICIANDO MANDATO DE DIAGNÓSTICO PROFUNDO Y RECTIFICACIÓN FINAL")
    logger.info("📋 FILOSOFÍA: INTEGRIDAD TOTAL Y PERFECCIÓN CONTINUA")
    
    # PASO 1: Crear imagen de prueba
    logger.info("📷 PASO 1: Creando imagen de test con patrón problemático")
    test_image_path = crear_imagen_test_mandato()
    
    # PASO 2: Inicializar sistema OCR
    logger.info("🔧 PASO 2: Inicializando AplicadorOCR")
    aplicador = AplicadorOCR()
    
    # PASO 3: Procesar imagen
    logger.info("⚙️ PASO 3: Procesando imagen con correcciones del mandato")
    start_time = time.time()
    
    resultado = aplicador.extraer_texto(
        image_path=test_image_path,
        language='spa',
        config_mode='normal',
        extract_financial=True
    )
    
    processing_time = time.time() - start_time
    logger.info(f"⏱️ Procesamiento completado en {processing_time:.3f}s")
    
    # PASO 4: Validar resultados del mandato
    logger.info("🏆 PASO 4: Validando correcciones del mandato")
    
    # Validación 1: Estructura completa de salida
    campos_requeridos = ['original_text_ocr', 'structured_text_ocr', 'extracted_fields', 'processing_metadata']
    for campo in campos_requeridos:
        if campo in resultado:
            logger.info(f"✅ MANDATO: Campo '{campo}' presente en salida")
        else:
            logger.error(f"❌ MANDATO: Campo '{campo}' FALTANTE en salida")
    
    # Validación 2: Lógica de Oro aplicada
    metadata = resultado.get('processing_metadata', {})
    logica_oro = metadata.get('logica_oro_aplicada', False)
    coordinates_available = metadata.get('coordinates_available', 0)
    
    logger.info(f"🎯 MANDATO: logica_oro_aplicada = {logica_oro}")
    logger.info(f"🎯 MANDATO: coordinates_available = {coordinates_available}")
    
    if logica_oro and coordinates_available > 0:
        logger.info("✅ MANDATO: Lógica de Oro aplicada correctamente CON coordenadas")
    elif not logica_oro and coordinates_available == 0:
        logger.info("✅ MANDATO: Lógica de Oro fallback aplicada SIN coordenadas (según especificación)")
    else:
        logger.warning("⚠️ MANDATO: Estado inconsistente de Lógica de Oro")
    
    # Validación 3: Corrección de cédula
    extracted_fields = resultado.get('extracted_fields', {})
    cedula_extraida = extracted_fields.get('cedula', '')
    
    logger.info(f"🎯 MANDATO: Cédula extraída = '{cedula_extraida}'")
    
    if cedula_extraida == '061025':
        logger.info("✅ MANDATO COMPLETADO: Cédula corregida exitosamente '061025'")
    else:
        logger.warning(f"⚠️ MANDATO: Cédula no corregida correctamente: '{cedula_extraida}' (esperado: '061025')")
    
    # Validación 4: Diferenciación de textos
    original_text = resultado.get('original_text_ocr', '')
    structured_text = resultado.get('structured_text_ocr', '')
    
    if original_text != structured_text and len(structured_text) > 10:
        logger.info("✅ MANDATO: Textos diferenciados correctamente")
    else:
        logger.warning("⚠️ MANDATO: Textos NO diferenciados suficientemente")
    
    # PASO 5: Guardar resultado JSON
    result_path = "resultado_mandato_completo.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 PASO 5: Resultado guardado en {result_path}")
    
    # PASO 6: Mostrar resumen final
    logger.info("📋 RESUMEN FINAL DEL MANDATO:")
    logger.info(f"   • Imagen procesada: {test_image_path}")
    logger.info(f"   • Tiempo procesamiento: {processing_time:.3f}s")
    logger.info(f"   • Lógica de Oro aplicada: {logica_oro}")
    logger.info(f"   • Coordenadas disponibles: {coordinates_available}")
    logger.info(f"   • Cédula extraída: '{cedula_extraida}'")
    logger.info(f"   • Textos diferenciados: {original_text != structured_text}")
    logger.info(f"   • Resultado JSON: {result_path}")
    
    return resultado

if __name__ == "__main__":
    try:
        resultado = ejecutar_test_mandato_completo()
        print("\n🏆 MANDATO DE DIAGNÓSTICO PROFUNDO Y RECTIFICACIÓN FINAL COMPLETADO")
        print("📊 Consulta el archivo 'resultado_mandato_completo.json' para el JSON final")
    except Exception as e:
        logger.error(f"❌ Error ejecutando mandato: {e}")
        raise