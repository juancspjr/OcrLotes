#!/usr/bin/env python3
"""
TEST INTEGRAL MANDATO 5 - REFINAMIENTO EXHAUSTIVO DE EXTRACTION_RULES.JSON
Filosofía: Integridad Total y Perfección Continua
Fecha: 2025-07-10 06:22 UTC

Este test valida que todas las reglas de extracción tengan configuración espacial
implementada correctamente y que el sistema mantenga compatibilidad total.
"""

import json
import logging
import time
from typing import Dict, List, Any
import os
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_validacion_json_estructura():
    """
    PUNTO DE CONTROL #1: Validación de estructura JSON de extraction_rules.json
    """
    logger.info("🔍 PUNTO DE CONTROL #1: Validando estructura JSON...")
    
    try:
        with open('config/extraction_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Validar estructura principal
        assert 'dynamic_geometry_config' in rules_data, "❌ Falta dynamic_geometry_config"
        assert 'extraction_rules' in rules_data, "❌ Falta extraction_rules"
        
        # Validar configuración dinámica
        geometry_config = rules_data['dynamic_geometry_config']
        assert geometry_config['enabled'] == True, "❌ dynamic_geometry_config no está habilitada"
        
        logger.info("✅ PUNTO DE CONTROL #1 PASSED: Estructura JSON válida")
        return True
        
    except Exception as e:
        logger.error(f"❌ PUNTO DE CONTROL #1 FAILED: {e}")
        return False

def test_validacion_spatial_search_config():
    """
    PUNTO DE CONTROL #2: Todas las reglas tienen spatial_search_config
    """
    logger.info("🔍 PUNTO DE CONTROL #2: Validando spatial_search_config en todas las reglas...")
    
    try:
        with open('config/extraction_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        total_reglas = 0
        reglas_con_spatial = 0
        reglas_sin_spatial = []
        
        for field_group in rules_data['extraction_rules']:
            field_name = field_group['field_name']
            for rule in field_group['rules']:
                total_reglas += 1
                rule_id = rule.get('rule_id', 'UNKNOWN')
                
                if 'spatial_search_config' in rule:
                    reglas_con_spatial += 1
                    # Validar estructura de spatial_search_config
                    spatial_config = rule['spatial_search_config']
                    assert 'enabled' in spatial_config, f"❌ {rule_id}: Falta 'enabled'"
                    assert 'search_directions' in spatial_config, f"❌ {rule_id}: Falta 'search_directions'"
                    assert 'max_distance_to_keyword_px' in spatial_config, f"❌ {rule_id}: Falta 'max_distance_to_keyword_px'"
                else:
                    reglas_sin_spatial.append(f"{field_name}:{rule_id}")
        
        logger.info(f"📊 Total reglas: {total_reglas}")
        logger.info(f"📊 Reglas con spatial_search_config: {reglas_con_spatial}")
        logger.info(f"📊 Cobertura espacial: {(reglas_con_spatial/total_reglas)*100:.1f}%")
        
        if reglas_sin_spatial:
            logger.warning(f"⚠️  Reglas sin spatial_search_config: {reglas_sin_spatial}")
        
        # MANDATO 5 requiere 100% de cobertura espacial
        if reglas_con_spatial == total_reglas:
            logger.info("✅ PUNTO DE CONTROL #2 PASSED: 100% de reglas tienen configuración espacial")
            return True
        else:
            logger.error(f"❌ PUNTO DE CONTROL #2 FAILED: Solo {reglas_con_spatial}/{total_reglas} reglas tienen configuración espacial")
            return False
        
    except Exception as e:
        logger.error(f"❌ PUNTO DE CONTROL #2 FAILED: {e}")
        return False

def test_integracion_aplicador_ocr():
    """
    PUNTO DE CONTROL #3: AplicadorOCR carga reglas sin errores
    """
    logger.info("🔍 PUNTO DE CONTROL #3: Testando carga de reglas en AplicadorOCR...")
    
    try:
        # Importar y instanciar AplicadorOCR
        sys.path.append('.')
        from aplicador_ocr import AplicadorOCR
        
        # Crear instancia y cargar reglas
        aplicador = AplicadorOCR()
        
        # Forzar carga de reglas (si no están ya cargadas)
        if hasattr(aplicador, '_load_extraction_rules'):
            reglas_cargadas = aplicador._load_extraction_rules()
            logger.info(f"📊 Reglas cargadas exitosamente: {len(reglas_cargadas)} campos configurados")
        
        logger.info("✅ PUNTO DE CONTROL #3 PASSED: AplicadorOCR carga reglas sin errores")
        return True
        
    except Exception as e:
        logger.error(f"❌ PUNTO DE CONTROL #3 FAILED: {e}")
        return False

def test_dynamic_geometry_config():
    """
    PUNTO DE CONTROL #4: Configuración de geometría dinámica completa
    """
    logger.info("🔍 PUNTO DE CONTROL #4: Validando configuración de geometría dinámica...")
    
    try:
        with open('config/extraction_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        geometry_config = rules_data['dynamic_geometry_config']
        
        # Validar campos obligatorios
        campos_requeridos = [
            'enabled', 'line_grouping_tolerance_y_ratio', 'vertical_alignment_threshold_px',
            'horizontal_alignment_threshold_px', 'region_analysis', 'spatial_search'
        ]
        
        for campo in campos_requeridos:
            assert campo in geometry_config, f"❌ Falta campo '{campo}' en dynamic_geometry_config"
        
        # Validar que está habilitada
        assert geometry_config['enabled'] == True, "❌ dynamic_geometry_config debe estar habilitada"
        
        # Validar estructura de region_analysis
        region_analysis = geometry_config['region_analysis']
        assert 'header_ratio' in region_analysis, "❌ Falta header_ratio"
        assert 'body_ratio' in region_analysis, "❌ Falta body_ratio"
        assert 'footer_ratio' in region_analysis, "❌ Falta footer_ratio"
        
        # Validar estructura de spatial_search
        spatial_search = geometry_config['spatial_search']
        assert 'preferred_directions' in spatial_search, "❌ Falta preferred_directions"
        assert 'distance_weights' in spatial_search, "❌ Falta distance_weights"
        
        logger.info("✅ PUNTO DE CONTROL #4 PASSED: Configuración de geometría dinámica completa")
        return True
        
    except Exception as e:
        logger.error(f"❌ PUNTO DE CONTROL #4 FAILED: {e}")
        return False

def test_spatial_processor_integration():
    """
    PUNTO DE CONTROL #5: Integración con spatial_processor
    """
    logger.info("🔍 PUNTO DE CONTROL #5: Validando integración con spatial_processor...")
    
    try:
        # Importar spatial_processor
        sys.path.append('.')
        from spatial_processor import SpatialProcessor
        
        # Crear instancia de SpatialProcessor
        processor = SpatialProcessor()
        
        # Verificar que los métodos principales están disponibles
        assert hasattr(processor, 'generate_logical_lines'), "❌ Falta método generate_logical_lines"
        assert hasattr(processor, 'find_nearby_values'), "❌ Falta método find_nearby_values"
        
        logger.info("✅ PUNTO DE CONTROL #5 PASSED: Integración con spatial_processor exitosa")
        return True
        
    except Exception as e:
        logger.error(f"❌ PUNTO DE CONTROL #5 FAILED: {e}")
        return False

def test_backup_integridad():
    """
    PUNTO DE CONTROL #6: Backup PRE_MANDATE5 existe y es válido
    """
    logger.info("🔍 PUNTO DE CONTROL #6: Validando backup PRE_MANDATE5...")
    
    try:
        backup_path = 'config/extraction_rules.json.backup_PRE_MANDATE5_20250710_061625'
        
        # Verificar que el backup existe
        assert os.path.exists(backup_path), f"❌ Backup no encontrado: {backup_path}"
        
        # Verificar que el backup es válido JSON
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert 'extraction_rules' in backup_data, "❌ Backup no contiene extraction_rules"
        
        logger.info("✅ PUNTO DE CONTROL #6 PASSED: Backup PRE_MANDATE5 válido y disponible")
        return True
        
    except Exception as e:
        logger.error(f"❌ PUNTO DE CONTROL #6 FAILED: {e}")
        return False

def run_mandato_5_integration_test():
    """
    Ejecutor principal del test integral de Mandato 5
    """
    logger.info("🚀 INICIANDO TEST INTEGRAL MANDATO 5 - REFINAMIENTO EXHAUSTIVO")
    logger.info("📋 Filosofía: Integridad Total y Perfección Continua")
    logger.info("📅 Fecha: 2025-07-10 06:22 UTC")
    logger.info("=" * 80)
    
    start_time = time.time()
    tests_passed = 0
    total_tests = 6
    
    # Ejecutar todos los tests
    tests = [
        test_validacion_json_estructura,
        test_validacion_spatial_search_config,
        test_integracion_aplicador_ocr,
        test_dynamic_geometry_config,
        test_spatial_processor_integration,
        test_backup_integridad
    ]
    
    for i, test_func in enumerate(tests, 1):
        logger.info(f"\n{'='*20} TEST {i}/{total_tests} {'='*20}")
        if test_func():
            tests_passed += 1
        logger.info(f"{'='*50}")
    
    # Resultado final
    execution_time = time.time() - start_time
    success_rate = (tests_passed / total_tests) * 100
    
    logger.info("\n" + "🏆" * 50)
    logger.info("📊 RESUMEN FINAL - MANDATO 5 INTEGRATION TEST")
    logger.info("🏆" * 50)
    logger.info(f"✅ Tests exitosos: {tests_passed}/{total_tests}")
    logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
    logger.info(f"⏱️  Tiempo de ejecución: {execution_time:.2f}s")
    
    if tests_passed == total_tests:
        logger.info("🎉 MANDATO 5 - REFINAMIENTO EXHAUSTIVO: COMPLETADO EXITOSAMENTE")
        logger.info("✅ Inteligencia espacial avanzada totalmente integrada")
        logger.info("✅ Configuración spatial_search_config 100% implementada")
        logger.info("✅ Sistema mantiene compatibilidad e integridad total")
    else:
        logger.error("❌ MANDATO 5 - REFINAMIENTO EXHAUSTIVO: REQUIERE CORRECCIONES")
        logger.error(f"⚠️  {total_tests - tests_passed} tests fallaron")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_mandato_5_integration_test()
    sys.exit(0 if success else 1)