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

# Configuración de Tesseract OCR
TESSERACT_CONFIG = {
    'default': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()- ',
    'digits': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,',
    'alphanumeric': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
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
        'description': 'Máxima calidad con filosofía de conservación extrema',
        'gaussian_blur_kernel': 5,
        'bilateral_filter': 'conditional',
        'morphology_operations': True,
        'adaptive_threshold': True,
        'deskew': 'conditional',
        'noise_removal_iterations': 0,  # Eliminado para capturas digitales
        'sharpening': 'conditional',
        'intelligent_preprocessing': True
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

# Configuración de preprocesamiento
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
    'sharpening_kernel': [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]
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
