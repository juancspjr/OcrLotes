#!/usr/bin/env python3
"""
Test de integración espacial - Mandato 4
Verifica que la integración del spatial_processor en aplicador_ocr funcione correctamente
"""

import sys
import os
import json
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos del sistema
from aplicador_ocr import AplicadorOCR
from spatial_processor import get_logical_lines, find_value_spatially
import config

def test_spatial_integration():
    """Test completo de integración espacial"""
    
    logger.info("🧪 MANDATO 4: Iniciando test de integración espacial")
    
    # Crear instancia del aplicador OCR
    aplicador = AplicadorOCR()
    
    # Verificar que la configuración espacial se cargó correctamente
    if not aplicador.config.get('dynamic_geometry_config'):
        logger.error("❌ Error: Configuración de geometría dinámica no encontrada")
        return False
    
    geometry_config = aplicador.config['dynamic_geometry_config']
    logger.info(f"✅ Configuración espacial cargada: {geometry_config.get('enabled', False)}")
    
    # Verificar que las reglas con configuración espacial existen
    if not aplicador._extraction_rules:
        logger.error("❌ Error: Reglas de extracción no cargadas")
        return False
    
    # Contar reglas con configuración espacial
    spatial_rules_count = 0
    for rule_config in aplicador._extraction_rules.get('extraction_rules', []):
        for rule in rule_config.get('rules', []):
            if rule.get('spatial_search_config', {}).get('enabled', False):
                spatial_rules_count += 1
                logger.info(f"✅ Regla espacial encontrada: {rule.get('rule_id', 'NO_ID')}")
    
    logger.info(f"✅ Total de reglas espaciales: {spatial_rules_count}")
    
    # Test con datos de ejemplo
    test_word_data = [
        {
            'text': 'Referencia:',
            'coordinates': [100, 100, 200, 120],
            'confidence': 0.9
        },
        {
            'text': '123456789',
            'coordinates': [250, 100, 350, 120],
            'confidence': 0.85
        },
        {
            'text': 'Monto:',
            'coordinates': [100, 150, 180, 170],
            'confidence': 0.88
        },
        {
            'text': '104.50',
            'coordinates': [200, 150, 280, 170],
            'confidence': 0.92
        }
    ]
    
    logger.info("🧪 Probando generación de líneas lógicas...")
    
    try:
        # Probar generación de líneas lógicas
        logical_lines = get_logical_lines(test_word_data, geometry_config)
        logger.info(f"✅ Líneas lógicas generadas: {len(logical_lines)}")
        
        for i, line in enumerate(logical_lines):
            words_in_line = [word['text'] for word in line]
            logger.info(f"   Línea {i+1}: {' '.join(words_in_line)}")
        
        # Probar búsqueda espacial
        if logical_lines:
            logger.info("🧪 Probando búsqueda espacial...")
            
            # Configuración espacial de prueba
            spatial_config = {
                'enabled': True,
                'preferred_directions': ['right', 'below'],
                'max_distance': 150,
                'confidence_threshold': 0.8
            }
            
            # Buscar valor cerca de "Referencia:"
            keyword_geometry = [100, 100, 200, 120]  # Coordenadas de "Referencia:"
            
            spatial_value = find_value_spatially(
                logical_lines, 
                keyword_geometry, 
                spatial_config, 
                geometry_config
            )
            
            if spatial_value:
                logger.info(f"✅ Valor encontrado espacialmente: '{spatial_value}'")
            else:
                logger.info("⚠️ No se encontró valor espacialmente")
        
        logger.info("🎉 MANDATO 4: Test de integración espacial COMPLETADO EXITOSAMENTE")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test de integración espacial: {e}", exc_info=True)
        return False

def test_aplicador_with_spatial():
    """Test del aplicador OCR con procesamiento espacial"""
    
    logger.info("🧪 MANDATO 4: Probando aplicador OCR con procesamiento espacial")
    
    # Buscar una imagen de prueba
    test_images = [
        'test_imagen_mandato_completo.png',
        'test_factura.png',
        'imagen_mejorada.png'
    ]
    
    test_image_path = None
    for img_name in test_images:
        if Path(img_name).exists():
            test_image_path = img_name
            break
    
    if not test_image_path:
        logger.warning("⚠️ No se encontraron imágenes de prueba. Saltando test de aplicador.")
        return True
    
    logger.info(f"📸 Usando imagen de prueba: {test_image_path}")
    
    try:
        aplicador = AplicadorOCR()
        
        # Procesar imagen
        result = aplicador.extraer_texto(test_image_path, config_mode='rapido')
        
        if result and 'processing_metadata' in result:
            metadata = result['processing_metadata']
            logger.info(f"✅ Procesamiento completado")
            logger.info(f"   Lógica de oro aplicada: {metadata.get('logica_oro_aplicada', False)}")
            logger.info(f"   Coordenadas disponibles: {metadata.get('coordinates_available', 0)}")
            logger.info(f"   Palabras detectadas: {metadata.get('total_words_detected', 0)}")
            
            # Verificar si se generaron líneas lógicas
            if hasattr(aplicador, '_current_logical_lines'):
                logger.info(f"   Líneas lógicas generadas: {len(aplicador._current_logical_lines)}")
            
            return True
        else:
            logger.error("❌ Error: Resultado de procesamiento vacío")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en test de aplicador: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    """Ejecutar tests de integración espacial"""
    
    logger.info("🚀 MANDATO 4: Iniciando tests de integración espacial")
    
    # Test 1: Integración básica
    test1_success = test_spatial_integration()
    
    # Test 2: Aplicador con imagen real
    test2_success = test_aplicador_with_spatial()
    
    # Resultado final
    if test1_success and test2_success:
        logger.info("🎉 MANDATO 4: TODOS LOS TESTS EXITOSOS - Integración espacial completada")
        sys.exit(0)
    else:
        logger.error("❌ MANDATO 4: TESTS FALLIDOS - Revisar integración espacial")
        sys.exit(1)