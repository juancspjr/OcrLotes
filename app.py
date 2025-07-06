"""
Aplicación Flask para el sistema OCR con interfaz web
"""

import os
import logging
import threading
import time
import json
import shutil
from datetime import datetime
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "fallback-secret-key-for-replit-dev"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuración de la aplicación
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB máximo
    UPLOAD_FOLDER='uploads',
    TEMP_FOLDER='temp'
)

# FIX: Pre-carga de componentes OCR para sistema asíncrono
# REASON: Inicializar modelos ONNX una vez al arranque para evitar latencia
# IMPACT: Worker asíncrono listo inmediatamente sin delay de inicialización
_ocr_components_loaded = False
_ocr_orchestrator = None
_worker_thread = None
_worker_running = False

def preload_ocr_components():
    """Pre-carga componentes OCR en memoria para worker asíncrono"""
    global _ocr_components_loaded, _ocr_orchestrator
    
    if not _ocr_components_loaded:
        try:
            logger.info("Pre-cargando componentes OCR para sistema asíncrono...")
            from main_ocr_process import OrquestadorOCR
            
            _ocr_orchestrator = OrquestadorOCR()
            
            # Warm-up de modelos críticos
            _ocr_orchestrator.aplicador._warmup_common_models()
            
            _ocr_components_loaded = True
            logger.info("✅ Componentes OCR pre-cargados exitosamente")
            
        except Exception as e:
            logger.error(f"Error pre-cargando componentes OCR: {e}")

def batch_processing_worker():
    """
    FIX: Worker asíncrono de procesamiento por lotes en hilo separado
    REASON: Procesar imágenes continuamente sin bloquear servidor Flask
    IMPACT: Sistema verdaderamente asíncrono que maneja colas de alto volumen
    """
    global _worker_running, _ocr_orchestrator
    
    from config import get_batch_config, get_async_directories
    import glob
    import json
    import shutil
    from datetime import datetime
    
    batch_config = get_batch_config()
    directories = get_async_directories()
    
    logger.info("🚀 Worker de procesamiento por lotes iniciado")
    
    while _worker_running:
        try:
            # Verificar si hay imágenes en inbox
            inbox_pattern = os.path.join(directories['inbox'], "*.png") + " " + \
                           os.path.join(directories['inbox'], "*.jpg")
            
            image_files = []
            for pattern in [os.path.join(directories['inbox'], "*.png"),
                           os.path.join(directories['inbox'], "*.jpg"),
                           os.path.join(directories['inbox'], "*.jpeg")]:
                image_files.extend(glob.glob(pattern))
            
            # FIX: DESHABILITADO procesamiento automático de imágenes en cola
            # REASON: Usuario reporta procesamiento no deseado tras 1 minuto de espera
            # IMPACT: Sistema requiere activación manual explícita vía botón o API
            
            # Solo monitorear estado, NO procesar automáticamente
            # if image_files:
            #     logger.info(f"Imágenes en cola: {len(image_files)} - esperando activación manual")
            
            # Esperar antes del siguiente ciclo de monitoreo
            time.sleep(batch_config['polling_interval_seconds'])
            
        except Exception as e:
            logger.error(f"Error en worker de lotes: {e}")
            time.sleep(10)  # Esperar más en caso de error

def process_batch(image_paths, directories):
    """Procesa un lote de imágenes"""
    global _ocr_orchestrator
    
    try:
        # Mover imágenes a processing
        processing_paths = []
        caption_texts = []
        metadata_list = []
        
        for img_path in image_paths:
            # Generar rutas de procesamiento
            filename = os.path.basename(img_path)
            processing_path = os.path.join(directories['processing'], filename)
            
            # Mover imagen
            shutil.move(img_path, processing_path)
            processing_paths.append(processing_path)
            
            # Leer caption si existe
            caption_path = img_path.replace('.png', '.caption.txt').replace('.jpg', '.caption.txt')
            caption_text = ""
            if os.path.exists(caption_path):
                with open(caption_path, 'r', encoding='utf-8') as f:
                    caption_text = f.read().strip()
                # Mover caption también
                new_caption_path = processing_path.replace('.png', '.caption.txt').replace('.jpg', '.caption.txt')
                shutil.move(caption_path, new_caption_path)
            
            caption_texts.append(caption_text)
            
            # Extraer metadata del nombre de archivo
            metadata = extract_metadata_from_filename(filename)
            metadata_list.append(metadata)
        
        # Procesar lote con orquestador
        if _ocr_orchestrator:
            results = _ocr_orchestrator.procesar_lote_imagenes(
                processing_paths, caption_texts, metadata_list, 'spa', 'ultra_rapido'
            )
            
            # Guardar resultados y mover archivos
            for i, result in enumerate(results):
                try:
                    filename = os.path.basename(processing_paths[i])
                    request_id = result.get('request_id', filename)
                    
                    # FIX: Guardar JSON resultado con conversión de tipos NumPy y manejo robusto
                    # REASON: Usuario reporta que los JSONs no se guardan o tienen errores de serialización
                    # IMPACT: Garantiza guardado correcto de todos los resultados JSON con coordenadas
                    result_filename = request_id.replace('.png', '.json').replace('.jpg', '.json').replace('.jpeg', '.json')
                    result_path = os.path.join(directories['results'], result_filename)
                    
                    # Convertir tipos NumPy antes de guardar JSON
                    if _ocr_orchestrator and hasattr(_ocr_orchestrator.aplicador, '_convert_numpy_types'):
                        result_converted = _ocr_orchestrator.aplicador._convert_numpy_types(result)
                    else:
                        result_converted = result
                    
                    # Añadir información adicional para debug en español
                    result_converted['info_guardado'] = {
                        'archivo_guardado': result_filename,
                        'timestamp_guardado': json.dumps(datetime.now().isoformat()),
                        'coordenadas_incluidas': 'coordenadas_disponibles' in result_converted,
                        'palabras_con_coordenadas': result_converted.get('coordenadas_disponibles', 0)
                    }
                    
                    with open(result_path, 'w', encoding='utf-8') as f:
                        json.dump(result_converted, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"✅ JSON guardado exitosamente: {result_filename} ({result_converted.get('coordenadas_disponibles', 0)} coordenadas)")
                    
                    # Mover imagen según resultado
                    if result.get('processing_status') == 'success':
                        final_path = os.path.join(directories['processed'], filename)
                    else:
                        final_path = os.path.join(directories['errors'], filename)
                    
                    shutil.move(processing_paths[i], final_path)
                    
                    # Mover caption también si existe
                    caption_processing = processing_paths[i].replace('.png', '.caption.txt').replace('.jpg', '.caption.txt')
                    if os.path.exists(caption_processing):
                        caption_final = final_path.replace('.png', '.caption.txt').replace('.jpg', '.caption.txt')
                        shutil.move(caption_processing, caption_final)
                    
                except Exception as e:
                    logger.error(f"Error guardando resultado {i}: {e}")
        
        logger.info(f"✅ Lote de {len(processing_paths)} imágenes procesado exitosamente")
        
    except Exception as e:
        logger.error(f"Error procesando lote: {e}")

def extract_metadata_from_filename(filename):
    """Extrae metadata del nombre de archivo formato WhatsApp"""
    import re
    
    # Patrón: 20250620-A_214056942235719@lid_Juanc_17-31.png
    pattern = r'(\d{8})-([A-Z])_([^_]+)_([^_]+)_(\d{2}-\d{2})'
    match = re.match(pattern, filename)
    
    if match:
        return {
            'sorteo_fecha': match.group(1),
            'sorteo_conteo': match.group(2),
            'sender_id': match.group(3),
            'sender_name': match.group(4),
            'hora_min': match.group(5)
        }
    
    return {
        'sorteo_fecha': '20250101',
        'sorteo_conteo': 'A',
        'sender_id': 'unknown',
        'sender_name': 'Unknown',
        'hora_min': '00-00'
    }

def start_batch_worker():
    """Inicia el worker asíncrono"""
    global _worker_thread, _worker_running
    
    if not _worker_running and batch_config.get('enable_batch_processing', True):
        _worker_running = True
        _worker_thread = threading.Thread(target=batch_processing_worker, daemon=True)
        _worker_thread.start()
        logger.info("Worker asíncrono iniciado")

def stop_batch_worker():
    """Detiene el worker asíncrono"""
    global _worker_running
    _worker_running = False
    logger.info("Worker asíncrono detenido")

# Importar configuraciones y rutas
from config import get_batch_config
batch_config = get_batch_config()

# Importar rutas (incluye las nuevas rutas de API)
import routes

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
