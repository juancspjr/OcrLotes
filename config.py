"""
Configuración global del sistema OCR de bajos recursos
Contiene todas las constantes, rutas y configuraciones centralizadas
"""

import os
from pathlib import Path

# Rutas base del proyecto
BASE_DIR = Path(__file__).parent.absolute()
TEMP_DIR = BASE_DIR / "temp"
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

# Crear directorios si no existen
TEMP_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# FIX: Configuración optimizada de Tesseract OCR para máxima confianza
# REASON: Incrementar confianza OCR y asegurar texto negro óptimo
# IMPACT: Mejora significativa en precision y confianza de extracción
TESSERACT_CONFIG = {
    'default': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.- -c tessedit_char_blacklist= -c preserve_interword_spaces=1',
    'high_confidence': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.- -c preserve_interword_spaces=1 -c tessedit_preserve_min_wd_len=2 -c tessedit_preserve_row_whitespace=1 -c tessedit_preserve_blk_wd_gap=1',
    'screenshot_optimized': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.- -c textord_really_old_xheight=1 -c textord_min_xheight=10 -c preserve_interword_spaces=1 -c tessedit_preserve_min_wd_len=1',
    'dual_pass_optimized': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.-_@#$%&+=[]{}|\\/<>?! -c preserve_interword_spaces=1 -c tessedit_preserve_row_whitespace=1 -c tessedit_preserve_blk_wd_gap=1 -c tessedit_preserve_min_wd_len=1',
    # FIX: Configuraciones ELITE para single-pass optimizado
    # REASON: Implementa configuraciones especializadas para imagen binaria perfecta
    # IMPACT: OCR ultra-eficiente aprovechando calidad ELITE (245-255 fondo, 0-10 texto)
    'elite_binary': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.-_@#$%&+=[]{}|\\/<>?! -c preserve_interword_spaces=1 -c tessedit_do_invert=0 -c classify_bln_numeric_mode=1',
    'elite_screenshot': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/.-_@#$%&+=[]{}|\\/<>?! -c preserve_interword_spaces=1 -c tessedit_do_invert=0 -c classify_bln_numeric_mode=1 -c textord_really_old_xheight=1',
    'digits': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,*/-',
    'alphanumeric': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()*/-'
}

# FIX: Configuración de confianza y calidad OCR mejorada
# REASON: Aumentar confianza OCR como solicita el usuario
# IMPACT: Texto extraído con mayor precisión y confianza
OCR_CONFIDENCE_CONFIG = {
    'min_confidence_threshold': 60,  # FIX: Incrementado de 30 a 60
    'high_confidence_threshold': 80,  # Para marcar como alta confianza
    'word_confidence_threshold': 70,  # Confianza mínima por palabra
    'line_confidence_threshold': 75,  # Confianza mínima por línea
    'text_color_preference': 'black_on_white',  # FIX: Priorizar texto negro
    'preprocessing_for_confidence': True  # Preprocesamiento específico para confianza
}

# Perfiles de rendimiento con filosofía de conservación extrema
PERFORMANCE_PROFILES = {
    'ultra_rapido': {
        'name': 'Ultra Rápido',
        'description': 'Mínimo procesamiento, máxima velocidad',
        'gaussian_blur_kernel': 3,
        'bilateral_filter': False,
        'morphology_operations': False,
        'adaptive_threshold': True,
        'deskew': False,  # Nunca para screenshots
        'noise_removal_iterations': 0,  # Eliminado para capturas digitales
        'sharpening': False,
        'intelligent_preprocessing': True  # Habilitado por defecto
    },
    'rapido': {
        'name': 'Rápido',
        'description': 'Balance entre velocidad y calidad con conservación extrema',
        'gaussian_blur_kernel': 3,
        'bilateral_filter': 'conditional',  # Solo si es necesario
        'morphology_operations': True,
        'adaptive_threshold': True,
        'deskew': 'conditional',  # Solo para documentos escaneados
        'noise_removal_iterations': 0,  # Eliminado para capturas digitales
        'sharpening': 'conditional',  # Solo si es necesario
        'intelligent_preprocessing': True
    },
    'normal': {
        'name': 'Normal',
        'description': 'Máxima precisión OCR con filosofía de conservación extrema',
        'gaussian_blur_kernel': 5,
        'bilateral_filter': 'conditional',
        'morphology_operations': True,
        'adaptive_threshold': True,
        'deskew': False,  # FIX: ELIMINADO - Causa falsa inclinación en screenshots
        'noise_removal_iterations': 0,  # Eliminado para capturas digitales
        'sharpening': 'adaptive',  # FIX: Nitidez adaptativa para mejor definición
        'intelligent_preprocessing': True,
        'advanced_binarization': True,  # FIX: Binarización avanzada mejorada
        'contrast_enhancement': 'adaptive',  # FIX: Mejora de contraste adaptativo
        'character_conservation': 'extreme'  # FIX: Máxima conservación de caracteres
    }
}

# FIX: Configuración para detección inteligente de tipo de imagen
# REASON: Implementar la filosofía de conservación extrema
# IMPACT: Reduce pasos innecesarios y preserva calidad del texto
IMAGE_TYPE_DETECTION = {
    'screenshot_indicators': {
        'min_width': 800,
        'min_height': 600,
        'aspect_ratio_min': 1.3,  # Pantallas típicamente horizontales
        'resolution_threshold': 480000,  # 800x600 mínimo
        'ui_elements_threshold': 0.1  # Presencia de elementos de UI
    },
    'document_scan_indicators': {
        'skew_threshold': 2.0,  # Grados de inclinación
        'noise_level_threshold': 15,
        'edge_irregularity': 0.3
    },
    'dark_background_threshold': 127,  # Media de intensidad
    'inversion_confidence_threshold': 0.6  # Confianza para inversión
}

# Umbrales para validación de imagen
IMAGE_QUALITY_THRESHOLDS = {
    'min_resolution': (100, 100),
    'max_resolution': (4000, 4000),
    'min_contrast': 20,
    'max_blur_variance': 50,
    'min_brightness': 30,
    'max_brightness': 225,
    'noise_threshold': 0.3,
    'text_density_min': 0.1
}

# FIX: Configuración avanzada de preprocesamiento con conservación extrema  
# REASON: Implementar nuevas técnicas más allá del simple upscaling
# IMPACT: Mejora significativa en calidad OCR y confianza de extracción
PREPROCESSING_CONFIG = {
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
    
    # FIX: Nuevas técnicas avanzadas de mejora más allá del upscaling
    'advanced_techniques': {
        'clahe_enabled': True,  # Histogram equalization adaptativo
        'clahe_clip_limit': 2.0,
        'clahe_tile_grid_size': (8, 8),
        'unsharp_mask_enabled': True,  # Unsharp masking para nitidez
        'unsharp_mask_strength': 1.5,
        'unsharp_mask_radius': 1.0,
        'edge_enhancement_enabled': True,  # Realce de bordes
        'gamma_correction_enabled': True,  # Corrección gamma adaptativa
        'gamma_range': (0.8, 1.2),
        'denoising_wavelet': True,  # Denoising con wavelets
        'structure_preservation': True  # Preservación de estructura
    },
    
    # FIX: Binarización avanzada mejorada
    'advanced_binarization': {
        'otsu_enabled': True,
        'adaptive_mean_enabled': True,
        'adaptive_gaussian_enabled': True,
        'multi_threshold_enabled': True,
        'local_threshold_enabled': True,
        'sauvola_enabled': True,  # Algoritmo Sauvola para documentos
        'niblack_enabled': True   # Algoritmo Niblack para texto fino
    },
    
    # FIX: Nuevos parámetros para binarización ELITE
    # REASON: Implementa estrategia de fondo blanco uniforme (245-255) y texto negro nítido (0-10)
    # IMPACT: Calidad OCR superior con una sola pasada
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
    
    # FIX: Parámetros para unificación avanzada de fondos heterogéneos
    # REASON: Implementa nueva estrategia de fondos múltiples y nitidez absoluta
    # IMPACT: Maneja imágenes con distintos tipos de fondo, unificándolos perfectamente
    'unificacion_fondos_avanzada': {
        'analisis_local_ventana': 50,  # Tamaño ventana para análisis local
        'umbral_variacion_fondo': 20,  # Umbral para detectar variaciones de fondo
        'metodo_binarizacion_local': 'sauvola_niblack_adaptativo',
        'factor_k_niblack': -0.2,
        'factor_k_sauvola': 0.34,
        'ventana_local_min': 15,
        'ventana_local_max': 51,
        'nitidez_absoluta_enabled': True,
        'nitidez_kernel_strength': 2.5,
        'relleno_inteligente_enabled': True,
        'unificacion_threshold': 5  # Diferencia máxima permitida en fondo unificado
    },
    
    # FIX: Configuración para análisis de componentes conectados (CCA)
    # REASON: Implementa purificación inteligente eliminando elementos no-textuales
    # IMPACT: OCR más limpio y eficiente sin interferencias
    'analisis_componentes_conectados': {
        'min_area_char': 10,  # Área mínima para considerar como carácter
        'max_area_char': 5000,  # Área máxima para considerar como carácter
        'min_aspect_ratio': 0.1,  # Relación de aspecto mínima
        'max_aspect_ratio': 10.0,  # Relación de aspecto máxima
        'min_solidity': 0.2,  # Solidez mínima (área/área_convex_hull)
        'eliminar_lineas_geometricas': True,
        'eliminar_rectangulos_grandes': True,
        'preservar_subrayados': True,
        'preservar_tachados': True
    }
}

# Patrones de expresiones regulares para documentos financieros
FINANCIAL_PATTERNS = {
    'amount': r'(?:Bs\.?\s*|BsS\.?\s*|USD\.?\s*|\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)',
    'date': r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    'time': r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)',
    'reference': r'(?:REF\.?\s*|REFERENCIA\.?\s*|#\s*)([A-Z0-9\-]{6,20})',
    'account': r'(?:CUENTA\.?\s*|CTA\.?\s*|ACCOUNT\.?\s*)([0-9\-]{10,20})',
    'rif': r'([VEJPG]\-\d{8}\-\d)',
    'cedula': r'([VE]\-?\d{7,8})',
    'phone': r'(\+?58\s?4\d{2}\s?\d{3}\s?\d{2}\s?\d{2}|\d{4}\s?\d{3}\s?\d{4})'
}

# Configuración de archivos temporales
TEMP_FILE_CONFIG = {
    'prefix': 'ocr_process_',
    'image_format': 'png',
    'keep_temp_files': False,  # Cambiar a True para depuración
    'max_temp_age_hours': 24
}

# Configuración del servidor web
WEB_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'max_content_length': 16 * 1024 * 1024,  # 16MB máximo
    'allowed_extensions': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
}

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'ocr_system.log'
}

# Métricas de calidad de OCR
OCR_QUALITY_THRESHOLDS = {
    'min_confidence': 30,
    'good_confidence': 70,
    'excellent_confidence': 90,
    'min_word_length': 2,
    'min_text_density': 0.05
}

# Configuración de idiomas soportados
SUPPORTED_LANGUAGES = {
    'spa': 'Español',
    'eng': 'Inglés',
    'spa+eng': 'Español + Inglés'
}

# Valores por defecto
DEFAULTS = {
    'language': 'spa',
    'performance_profile': 'rapido',
    'save_intermediate': False,
    'output_format': 'json'
}
