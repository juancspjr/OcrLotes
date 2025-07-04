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

# URLs y configuración de modelos
MODELS_CONFIG = {
    'db_resnet50': {
        'url': 'https://github.com/felixdittrich92/OnnxTR/releases/download/v0.0.1/db_resnet50-69ba0015.onnx',
        'filename': 'db_resnet50-69ba0015.onnx',
        'sha256': '69ba0015',  # Identificador del archivo
        'description': 'Modelo de detección de texto'
    },
    'crnn_vgg16_bn': {
        'url': 'https://github.com/felixdittrich92/OnnxTR/releases/download/v0.0.1/crnn_vgg16_bn-662979cc.onnx',
        'filename': 'crnn_vgg16_bn-662979cc.onnx',
        'sha256': '662979cc',  # Identificador del archivo
        'description': 'Modelo de reconocimiento de caracteres'
    }
}

def download_model(model_name, model_config, force=False):
    """Descarga un modelo ONNX si no existe localmente"""
    models_dir = Path('models/onnxtr')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / model_config['filename']
    
    if model_path.exists() and not force:
        logger.info(f"Modelo {model_name} ya existe: {model_path}")
        return True
    
    try:
        logger.info(f"Descargando {model_config['description']}...")
        logger.info(f"URL: {model_config['url']}")
        
        response = requests.get(model_config['url'], stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
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
        logger.info(f"Modelo {model_name} descargado exitosamente: {model_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error descargando {model_name}: {e}")
        if model_path.exists():
            model_path.unlink()
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
    """Descarga todos los modelos necesarios"""
    logger.info("Iniciando descarga de modelos ONNX...")
    
    success_count = 0
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