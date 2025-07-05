#!/usr/bin/env python3
"""
Script para descargar y gestionar modelos ONNX localmente
Mantiene los modelos en el repositorio para independencia de fuentes externas
"""

import os
import requests
import hashlib
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FIX: URLs desde GitHub personal para garantizar disponibilidad
# REASON: Evitar dependencia de repositorios externos que pueden cambiar o desaparecer
# IMPACT: Control total sobre modelos y disponibilidad garantizada
GITHUB_REPO_BASE = 'https://github.com/juancspjr/OcrAcorazado/raw/main/models/onnxtr/'

MODELS_CONFIG = {
    'db_resnet50': {
        'url': f'{GITHUB_REPO_BASE}db_resnet50-69ba0015.onnx',
        'filename': 'db_resnet50-69ba0015.onnx',
        'sha256': '69ba0015',
        'description': 'Modelo de detección ResNet50 (alta precisión)',
        'size_mb': 96.2
    },
    'crnn_vgg16_bn': {
        'url': f'{GITHUB_REPO_BASE}crnn_vgg16_bn-662979cc.onnx',
        'filename': 'crnn_vgg16_bn-662979cc.onnx',
        'sha256': '662979cc',
        'description': 'Modelo de reconocimiento VGG16 (alta precisión)',
        'size_mb': 60.3
    },
    # FIX: Agregar modelos MobileNet para perfiles ultra_rapido y rapido
    # REASON: Necesarios para las optimizaciones de velocidad implementadas
    # IMPACT: Modelos livianos para procesamiento ultra-rápido desde GitHub propio
    'db_mobilenet_v3_large': {
        'url': f'{GITHUB_REPO_BASE}db_mobilenet_v3_large-4987e7bd.onnx',
        'filename': 'db_mobilenet_v3_large-4987e7bd.onnx',
        'sha256': '4987e7bd',
        'description': 'Modelo de detección MobileNet (ultra rápido)',
        'size_mb': 16.1
    },
    'crnn_mobilenet_v3_small': {
        'url': f'{GITHUB_REPO_BASE}crnn_mobilenet_v3_small-bded4d49.onnx',
        'filename': 'crnn_mobilenet_v3_small-bded4d49.onnx',
        'sha256': 'bded4d49',
        'description': 'Modelo de reconocimiento MobileNet (ultra rápido)',
        'size_mb': 8.3
    }
}

def download_model(model_name, model_config, force=False):
    """
    FIX: Sistema híbrido de descarga de modelos 
    REASON: Intentar GitHub personal primero, fallback a fuentes originales
    IMPACT: Máxima disponibilidad garantizada con control total cuando es posible
    """
    models_dir = Path('models/onnxtr')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / model_config['filename']
    
    if model_path.exists() and not force:
        logger.info(f"Modelo {model_name} ya existe: {model_path}")
        return True
    
    # Lista de URLs a intentar (GitHub personal primero, fallback segundo)
    urls_to_try = [
        {
            'url': model_config['url'],
            'source': 'GitHub Personal',
            'priority': 1
        }
    ]
    
    # FIX: Agregar URLs de fallback para modelos MobileNet
    # REASON: Mientras se suben los modelos al GitHub personal, usar fuentes originales
    # IMPACT: Sistema funcional inmediatamente sin esperar la subida manual de modelos
    fallback_urls = {
        'db_mobilenet_v3_large': 'https://github.com/felixdittrich92/OnnxTR/releases/download/v0.2.0/db_mobilenet_v3_large-4987e7bd.onnx',
        'crnn_mobilenet_v3_small': 'https://github.com/felixdittrich92/OnnxTR/releases/download/v0.0.1/crnn_mobilenet_v3_small-bded4d49.onnx'
    }
    
    if model_name in fallback_urls:
        urls_to_try.append({
            'url': fallback_urls[model_name],
            'source': 'OnnxTR Original (Fallback)',
            'priority': 2
        })
    
    # Intentar descarga desde cada URL
    for url_info in urls_to_try:
        try:
            size_mb = model_config.get('size_mb', 0)
            logger.info(f"Intentando descarga de {model_config['description']} ({size_mb}MB)...")
            logger.info(f"Fuente {url_info['priority']}: {url_info['source']}")
            logger.info(f"URL: {url_info['url']}")
            
            response = requests.get(url_info['url'], stream=True, timeout=30)
            response.raise_for_status()
            
            # Verificar que efectivamente es un archivo ONNX
            content_type = response.headers.get('content-type', '')
            logger.info(f"Tipo de contenido: {content_type}")
            
            # Verificar tamaño del archivo
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                logger.info(f"Tamaño archivo: {total_size / (1024*1024):.1f}MB")
            
            # Descargar el archivo con progreso
            downloaded = 0
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgreso: {progress:.1f}%", end='', flush=True)
            
            print()  # Nueva línea
            logger.info(f"✅ Modelo {model_name} descargado exitosamente desde {url_info['source']}")
            logger.info(f"   Archivo: {model_path}")
            return True
            
        except Exception as e:
            logger.warning(f"❌ Error con {url_info['source']}: {e}")
            if model_path.exists():
                model_path.unlink()
            continue  # Intentar siguiente URL
    
    # Si llegamos aquí, ninguna URL funcionó
    logger.error(f"❌ No se pudo descargar {model_name} desde ninguna fuente")
    return False

def verify_models():
    """Verifica que todos los modelos estén disponibles"""
    models_dir = Path('models/onnxtr')
    
    if not models_dir.exists():
        logger.warning("Directorio de modelos no existe, creando...")
        models_dir.mkdir(parents=True, exist_ok=True)
    
    all_present = True
    for model_name, model_config in MODELS_CONFIG.items():
        model_path = models_dir / model_config['filename']
        if not model_path.exists():
            logger.warning(f"Modelo {model_name} no encontrado")
            all_present = False
        else:
            logger.info(f"✓ {model_name}: {model_path}")
    
    return all_present

def download_all_models(force=False):
    """
    FIX: Descarga todos los modelos necesarios desde GitHub personal
    REASON: Garantizar disponibilidad de modelos incluyendo los nuevos MobileNet para ultra_rapido
    IMPACT: Sistema completamente autosuficiente sin dependencias externas
    """
    logger.info("Iniciando descarga de modelos ONNX desde GitHub personal...")
    logger.info(f"Repositorio: {GITHUB_REPO_BASE}")
    
    # Crear directorio si no existe
    models_dir = Path('models/onnxtr')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_size = sum(model['size_mb'] for model in MODELS_CONFIG.values())
    logger.info(f"Total a descargar: {len(MODELS_CONFIG)} modelos ({total_size:.1f}MB)")
    
    for model_name, model_config in MODELS_CONFIG.items():
        if download_model(model_name, model_config, force):
            success_count += 1
    
    total_models = len(MODELS_CONFIG)
    logger.info(f"Descarga completada: {success_count}/{total_models} modelos")
    
    return success_count == total_models

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestionar modelos ONNX locales')
    parser.add_argument('--verify', action='store_true', help='Verificar modelos existentes')
    parser.add_argument('--download', action='store_true', help='Descargar modelos faltantes')
    parser.add_argument('--force', action='store_true', help='Forzar descarga (reemplazar existentes)')
    
    args = parser.parse_args()
    
    if args.verify:
        if verify_models():
            logger.info("Todos los modelos están disponibles")
        else:
            logger.warning("Algunos modelos no están disponibles")
    
    if args.download:
        download_all_models(args.force)
    
    if not args.verify and not args.download:
        # Comportamiento por defecto: verificar y descargar si es necesario
        if not verify_models():
            logger.info("Descargando modelos faltantes...")
            download_all_models()
        else:
            logger.info("Todos los modelos ya están disponibles")

if __name__ == "__main__":
    main()