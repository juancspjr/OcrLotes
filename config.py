"""
Configuración global optimizada del sistema OCR de bajos recursos
Optimizaciones: lazy loading, configuración modular, uso eficiente de memoria
"""

import os
from pathlib import Path
from functools import lru_cache

# =====================================================================
# CONFIGURACIÓN CORE (carga inmediata, ligera)
# =====================================================================

# Rutas base del proyecto
BASE_DIR = Path(__file__).parent.absolute()
TEMP_DIR = BASE_DIR / "temp"
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

# Crear directorios si no existen
TEMP_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Configuración básica de OCR (ligera)
OCR_BASIC_CONFIG = {
    'min_confidence_threshold': 60,
    'high_confidence_threshold': 80,
    'default_language': 'spa',
    'default_profile': 'rapido'
}

# Configuración del servidor web (esencial)
WEB_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'max_content_length': 16 * 1024 * 1024,  # 16MB máximo
    'allowed_extensions': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
}

# Configuración de archivos temporales (básica)
TEMP_FILE_CONFIG = {
    'prefix': 'ocr_process_',
    'image_format': 'png',
    'keep_temp_files': False,
    'max_temp_age_hours': 24
}

# Umbrales básicos para validación de imagen
IMAGE_QUALITY_THRESHOLDS = {
    'min_resolution': (100, 100),
    'max_resolution': (4000, 4000),
    'min_contrast': 20,
    'min_brightness': 30,
    'max_brightness': 225
}

# Valores por defecto
DEFAULTS = {
    'language': 'spa',
    'performance_profile': 'rapido',
    'save_intermediate': False,
    'output_format': 'json'
}

# =====================================================================
# CONFIGURACIÓN PESADA (carga lazy cuando se necesita)
# =====================================================================

# FIX: Lazy loading para configuraciones pesadas
# REASON: Evitar cargar configuraciones complejas al inicio
# IMPACT: Reduce tiempo de startup y uso de memoria inicial

@lru_cache(maxsize=1)
def get_tesseract_config():
    """Obtiene configuración de Tesseract de forma lazy"""
    return {
        'default': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.- -c tessedit_char_blacklist= -c preserve_interword_spaces=1',
        'high_confidence': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.- -c preserve_interword_spaces=1 -c tessedit_preserve_min_wd_len=2 -c tessedit_preserve_row_whitespace=1 -c tessedit_preserve_blk_wd_gap=1',
        'screenshot_optimized': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.- -c textord_really_old_xheight=1 -c textord_min_xheight=10 -c preserve_interword_spaces=1 -c tessedit_preserve_min_wd_len=1',
        'dual_pass_optimized': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.-_@#$%&+=[]{}|\\/<>?! -c preserve_interword_spaces=1 -c tessedit_preserve_row_whitespace=1 -c tessedit_preserve_blk_wd_gap=1 -c tessedit_preserve_min_wd_len=1',
        'elite_binary': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.-_@#$%&+=[]{}|\\/<>?! -c preserve_interword_spaces=1 -c tessedit_do_invert=0 -c classify_bln_numeric_mode=1',
        'elite_screenshot': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.-_@#$%&+=[]{}|\\/<>?! -c preserve_interword_spaces=1 -c tessedit_do_invert=0 -c classify_bln_numeric_mode=1 -c textord_really_old_xheight=1',
        'digits': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,*/-',
        'alphanumeric': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/-'
    }

@lru_cache(maxsize=1)
def get_performance_profiles():
    """Obtiene perfiles de rendimiento de forma lazy"""
    return {
        'ultra_rapido': {
            'name': 'Ultra Rápido',
            'description': 'Mínimo procesamiento, máxima velocidad',
            'gaussian_blur_kernel': 3,
            'bilateral_filter': False,
            'morphology_operations': False,
            'adaptive_threshold': True,
            'deskew': False,
            'noise_removal_iterations': 0,
            'sharpening': False,
            'intelligent_preprocessing': True
        },
        'rapido': {
            'name': 'Rápido',
            'description': 'Balance entre velocidad y calidad con conservación extrema',
            'gaussian_blur_kernel': 3,
            'bilateral_filter': 'conditional',
            'morphology_operations': True,
            'adaptive_threshold': True,
            'deskew': 'conditional',
            'noise_removal_iterations': 0,
            'sharpening': 'conditional',
            'intelligent_preprocessing': True
        },
        'normal': {
            'name': 'Normal',
            'description': 'Máxima precisión OCR con filosofía de conservación extrema',
            'gaussian_blur_kernel': 5,
            'bilateral_filter': 'conditional',
            'morphology_operations': True,
            'adaptive_threshold': True,
            'deskew': False,
            'noise_removal_iterations': 0,
            'sharpening': 'adaptive',
            'intelligent_preprocessing': True,
            'advanced_binarization': True,
            'contrast_enhancement': 'adaptive',
            'character_conservation': 'extreme'
        }
    }

@lru_cache(maxsize=1)
def get_preprocessing_config():
    """Obtiene configuración de preprocesamiento de forma lazy"""
    return {
        'resize_max_dimension': 2000,
        'gaussian_blur_range': (3, 7),
        'bilateral_filter_params': {'d': 9, 'sigmaColor': 75, 'sigmaSpace': 75},
        'morphology_kernel_size': (3, 3),
        'adaptive_threshold_params': {
            'maxValue': 255,
            'adaptiveMethod': 'ADAPTIVE_THRESH_GAUSSIAN_C',
            'thresholdType': 'THRESH_BINARY',
            'blockSize': 11,
            'C': 2
        },
        'deskew_angle_range': (-45, 45),
        'sharpening_kernel': [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]],
        
        # Técnicas avanzadas de mejora
        'advanced_techniques': {
            'clahe_enabled': True,
            'clahe_clip_limit': 2.0,
            'clahe_tile_grid_size': (8, 8),
            'unsharp_mask_enabled': True,
            'unsharp_mask_strength': 1.5,
            'unsharp_mask_radius': 1.0,
            'edge_enhancement_enabled': True,
            'gamma_correction_enabled': True,
            'gamma_range': (0.8, 1.2),
            'denoising_wavelet': True,
            'structure_preservation': True
        },
        
        # Binarización avanzada mejorada
        'advanced_binarization': {
            'otsu_enabled': True,
            'adaptive_mean_enabled': True,
            'adaptive_gaussian_enabled': True,
            'multi_threshold_enabled': True,
            'local_threshold_enabled': True,
            'sauvola_enabled': True,
            'niblack_enabled': True
        },
        
        # Binarización ELITE
        'binarizacion_elite': {
            'fondo_blanco_min': 245,
            'fondo_blanco_max': 255,
            'texto_negro_min': 0,
            'texto_negro_max': 10,
            'umbral_otsu_factor': 1.0,
            'ventana_sauvola': 25,
            'k_sauvola': 0.2,
            'metodos_disponibles': ['otsu', 'sauvola', 'adaptive_mean', 'adaptive_gaussian']
        },
        
        # Unificación avanzada de fondos heterogéneos
        'unificacion_fondos_avanzada': {
            'analisis_local_ventana': 50,
            'umbral_variacion_fondo': 20,
            'metodo_binarizacion_local': 'sauvola_niblack_adaptativo',
            'factor_k_niblack': -0.2,
            'factor_k_sauvola': 0.34,
            'ventana_local_min': 15,
            'ventana_local_max': 51,
            'nitidez_absoluta_enabled': True,
            'nitidez_kernel_strength': 2.5,
            'relleno_inteligente_enabled': True,
            'unificacion_threshold': 5
        },
        
        # Análisis de componentes conectados (CCA)
        'analisis_componentes_conectados': {
            'min_area_char': 10,
            'max_area_char': 5000,
            'min_aspect_ratio': 0.1,
            'max_aspect_ratio': 10.0,
            'min_solidity': 0.2,
            'eliminar_lineas_geometricas': True,
            'eliminar_rectangulos_grandes': True,
            'preservar_subrayados': True,
            'preservar_tachados': True
        }
    }

@lru_cache(maxsize=1)
def get_image_detection_config():
    """Obtiene configuración de detección de imagen de forma lazy"""
    return {
        'screenshot_indicators': {
            'min_width': 800,
            'min_height': 600,
            'aspect_ratio_min': 1.3,
            'resolution_threshold': 480000,
            'ui_elements_threshold': 0.1
        },
        'document_scan_indicators': {
            'skew_threshold': 2.0,
            'noise_level_threshold': 15,
            'edge_irregularity': 0.3
        },
        'dark_background_threshold': 127,
        'inversion_confidence_threshold': 0.6
    }

@lru_cache(maxsize=1)
def get_financial_patterns():
    """Obtiene patrones financieros de forma lazy"""
    return {
        'amount': r'(?:Bs\.?\s*|BsS\.?\s*|USD\.?\s*|\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)',
        'date': r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        'time': r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)',
        'reference': r'(?:REF\.?\s*|REFERENCIA\.?\s*|#\s*)([A-Z0-9\-]{6,20})',
        'account': r'(?:CUENTA\.?\s*|CTA\.?\s*|ACCOUNT\.?\s*)([0-9\-]{10,20})',
        'rif': r'([VEJPG]\-\d{8}\-\d)',
        'cedula': r'([VE]\-?\d{7,8})',
        'phone': r'(\+?58\s?4\d{2}\s?\d{3}\s?\d{2}\s?\d{2}|\d{4}\s?\d{3}\s?\d{4})'
    }

@lru_cache(maxsize=1)
def get_ocr_confidence_config():
    """Obtiene configuración de confianza OCR de forma lazy"""
    return {
        'min_confidence_threshold': 60,
        'high_confidence_threshold': 80,
        'word_confidence_threshold': 70,
        'line_confidence_threshold': 75,
        'text_color_preference': 'black_on_white',
        'preprocessing_for_confidence': True
    }

@lru_cache(maxsize=1)
def get_supported_languages():
    """Obtiene idiomas soportados de forma lazy"""
    return {
        'spa': 'Español',
        'eng': 'Inglés',
        'spa+eng': 'Español + Inglés'
    }

@lru_cache(maxsize=1)
def get_logging_config():
    """Obtiene configuración de logging de forma lazy"""
    return {
        'level': 'INFO',  # Cambiado de DEBUG para mejor rendimiento
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'filename': 'ocr_system.log'
    }

@lru_cache(maxsize=1)
def get_ocr_quality_thresholds():
    """Obtiene umbrales de calidad OCR de forma lazy"""
    return {
        'min_confidence': 30,
        'good_confidence': 70,
        'excellent_confidence': 90,
        'min_word_length': 2,
        'min_text_density': 0.05
    }

# =====================================================================
# FUNCIONES DE COMPATIBILIDAD (para mantener API existente)
# =====================================================================

# FIX: Propiedades lazy para mantener compatibilidad con código existente
# REASON: Evitar romper imports existentes mientras optimizamos
# IMPACT: Transición suave a configuración lazy

@property
def TESSERACT_CONFIG():
    return get_tesseract_config()

@property  
def PERFORMANCE_PROFILES():
    return get_performance_profiles()

@property
def PREPROCESSING_CONFIG():
    return get_preprocessing_config()

@property
def IMAGE_TYPE_DETECTION():
    return get_image_detection_config()

@property
def FINANCIAL_PATTERNS():
    return get_financial_patterns()

@property
def OCR_CONFIDENCE_CONFIG():
    return get_ocr_confidence_config()

@property
def SUPPORTED_LANGUAGES():
    return get_supported_languages()

@property
def LOGGING_CONFIG():
    return get_logging_config()

@property
def OCR_QUALITY_THRESHOLDS():
    return get_ocr_quality_thresholds()

# FIX: Backward compatibility - crear variables globales que apuntan a las funciones
# REASON: Mantener compatibilidad con código existente que usa estas variables
# IMPACT: No rompe código existente pero beneficia de lazy loading
TESSERACT_CONFIG = get_tesseract_config()
PERFORMANCE_PROFILES = get_performance_profiles() 
PREPROCESSING_CONFIG = get_preprocessing_config()
IMAGE_TYPE_DETECTION = get_image_detection_config()
FINANCIAL_PATTERNS = get_financial_patterns()
OCR_CONFIDENCE_CONFIG = get_ocr_confidence_config()
SUPPORTED_LANGUAGES = get_supported_languages()
LOGGING_CONFIG = get_logging_config()
OCR_QUALITY_THRESHOLDS = get_ocr_quality_thresholds()

# =====================================================================
# UTILIDADES DE RENDIMIENTO
# =====================================================================

def clear_config_cache():
    """Limpia el cache de configuración (útil para testing)"""
    get_tesseract_config.cache_clear()
    get_performance_profiles.cache_clear()
    get_preprocessing_config.cache_clear()
    get_image_detection_config.cache_clear()
    get_financial_patterns.cache_clear()
    get_ocr_confidence_config.cache_clear()
    get_supported_languages.cache_clear()
    get_logging_config.cache_clear()
    get_ocr_quality_thresholds.cache_clear()

def get_config_memory_usage():
    """Obtiene información sobre el uso de memoria del config"""
    import sys
    cache_info = {
        'tesseract': get_tesseract_config.cache_info(),
        'performance': get_performance_profiles.cache_info(),
        'preprocessing': get_preprocessing_config.cache_info(),
        'detection': get_image_detection_config.cache_info(),
        'patterns': get_financial_patterns.cache_info(),
        'confidence': get_ocr_confidence_config.cache_info(),
        'languages': get_supported_languages.cache_info(),
        'logging': get_logging_config.cache_info(),
        'quality': get_ocr_quality_thresholds.cache_info()
    }
    
    # Calcular tamaño aproximado del módulo
    module_size = sys.getsizeof(globals())
    
    return {
        'cache_info': cache_info,
        'module_size_bytes': module_size,
        'module_size_mb': round(module_size / 1024 / 1024, 2)
    }
