#!/usr/bin/env python3
"""
Script de prueba para validar la corrección del Mandato 1/2: 
Contradicción logica_oro_aplicada
"""

import sys
import os
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir directorio actual al path
sys.path.append('.')

from aplicador_ocr import AplicadorOCR

def test_mandato_correccion():
    """Prueba la corrección del mandato para logica_oro_aplicada"""
    
    print("=== MANDATO 1/2: PRUEBA DE CORRECCIÓN ===")
    print("Objetivo: Verificar que logica_oro_aplicada refleje exactamente si se aplicó lógica de oro basada en coordenadas")
    print()
    
    # Inicializar aplicador OCR
    aplicador = AplicadorOCR()
    
    # Imagen de prueba
    imagen_path = "data/processed/20250709-J--21760390085035@lid_Luis_07-56_20250709_221748_182.png"
    
    if not os.path.exists(imagen_path):
        print(f"❌ ERROR: Imagen no encontrada en {imagen_path}")
        # Buscar imagen en otros directorios
        posibles_paths = [
            "uploads/20250709-J--21760390085035@lid_Luis_07-56_20250709_221748_182.png",
            "temp/20250709-J--21760390085035@lid_Luis_07-56_20250709_221748_182.png",
            "20250709-J--21760390085035@lid_Luis_07-56_20250709_221748_182.png"
        ]
        
        for path in posibles_paths:
            if os.path.exists(path):
                imagen_path = path
                print(f"✅ Imagen encontrada en: {path}")
                break
        else:
            print("❌ No se encontró la imagen en ningún directorio")
            return
    
    print(f"📁 Procesando imagen: {imagen_path}")
    print()
    
    try:
        # Procesar imagen usando el método correcto
        resultado = aplicador.extraer_texto(imagen_path, 'spa', extract_financial=True)
        
        # Extraer metadatos relevantes
        metadata = resultado.get('processing_metadata', {})
        logica_oro_aplicada = metadata.get('logica_oro_aplicada', False)
        coordinates_available = metadata.get('coordinates_available', 0)
        error_messages = metadata.get('error_messages', [])
        
        print("=== RESULTADOS DE LA CORRECCIÓN ===")
        print(f"📊 coordinates_available: {coordinates_available}")
        print(f"🏆 logica_oro_aplicada: {logica_oro_aplicada}")
        print(f"⚠️  error_messages: {error_messages}")
        print()
        
        # Validar corrección según mandato
        print("=== VALIDACIÓN DEL MANDATO ===")
        
        if coordinates_available > 0:
            if logica_oro_aplicada:
                print("✅ CORRECTO: coordinates_available > 0 y logica_oro_aplicada = true")
                print("   La lógica de oro basada en coordenadas se aplicó correctamente")
                estado_mandato = "CORRECTO"
            else:
                print("❌ ERROR: coordinates_available > 0 pero logica_oro_aplicada = false")
                print("   Debería ser true cuando hay coordenadas disponibles")
                estado_mandato = "ERROR"
        else:
            if not logica_oro_aplicada:
                print("✅ CORRECTO: coordinates_available = 0 y logica_oro_aplicada = false")
                print("   Se usó fallback y el flag refleja correctamente que no se aplicó lógica de oro")
                estado_mandato = "CORRECTO"
            else:
                print("❌ ERROR: coordinates_available = 0 pero logica_oro_aplicada = true")
                print("   Debería ser false cuando no hay coordenadas disponibles")
                estado_mandato = "ERROR"
        
        print()
        print("=== ANÁLISIS ADICIONAL ===")
        
        # Comparar textos
        original_text = resultado.get('original_text_ocr', '')
        structured_text = resultado.get('structured_text_ocr', '')
        
        print(f"📄 Longitud original_text_ocr: {len(original_text)} caracteres")
        print(f"📄 Longitud structured_text_ocr: {len(structured_text)} caracteres")
        
        if original_text.strip() == structured_text.strip():
            print("⚠️  ATENCIÓN: Los textos original y estructurado son idénticos")
            print("   Esto podría indicar que no se aplicó diferenciación")
        else:
            print("✅ Los textos original y estructurado son diferentes")
            print("   Diferenciación aplicada correctamente")
        
        print()
        print("=== RESUMEN FINAL ===")
        print(f"🎯 Estado del Mandato: {estado_mandato}")
        
        if estado_mandato == "CORRECTO":
            print("🏆 MANDATO 1/2 COMPLETADO EXITOSAMENTE")
            print("   El flag logica_oro_aplicada refleja correctamente la aplicación de lógica de oro")
        else:
            print("❌ MANDATO 1/2 REQUIERE CORRECCIÓN ADICIONAL")
            print("   El flag logica_oro_aplicada no refleja correctamente el estado")
        
        # Guardar resultado para análisis
        resultado_prueba = {
            'timestamp': datetime.now().isoformat(),
            'mandato': 'Mandato 1/2: Corrección logica_oro_aplicada',
            'imagen_procesada': imagen_path,
            'coordinates_available': coordinates_available,
            'logica_oro_aplicada': logica_oro_aplicada,
            'error_messages': error_messages,
            'estado_mandato': estado_mandato,
            'metadata_completo': metadata,
            'textos_diferentes': original_text.strip() != structured_text.strip()
        }
        
        with open('resultado_mandato_correccion.json', 'w', encoding='utf-8') as f:
            json.dump(resultado_prueba, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultado guardado en: resultado_mandato_correccion.json")
        
        return estado_mandato == "CORRECTO"
        
    except Exception as e:
        print(f"❌ ERROR durante el procesamiento: {e}")
        logger.error(f"Error en test_mandato_correccion: {e}")
        return False

if __name__ == "__main__":
    success = test_mandato_correccion()
    sys.exit(0 if success else 1)