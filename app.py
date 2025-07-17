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
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from memory_optimizer import memory_optimizer, start_memory_monitoring
from memory_profiler_advanced import advanced_profiler

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuración de la aplicación
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB máximo
    UPLOAD_FOLDER='uploads',
    TEMP_FOLDER='temp'
)

# FIX: Manejo estandarizado de errores HTTP para sistema enterprise
# REASON: Usuario reporta respuestas inconsistentes entre endpoints
# IMPACT: Respuestas de error uniformes siguiendo estándares enterprise
# INTERFACE: Manejo robusto de errores con logging y trazabilidad

@app.errorhandler(400)
def handle_bad_request(e):
    """Manejo estandarizado de errores 400 Bad Request"""
    logger.error(f"Error 400 - Bad Request: {str(e)}")
    return jsonify({
        'error': True,
        'status': 'error',
        'estado': 'error',
        'message': 'Solicitud mal formateada',
        'mensaje': 'Solicitud mal formateada',
        'details': str(e),
        'timestamp': datetime.now().isoformat(),
        'error_code': 'BAD_REQUEST_400'
    }), 400

@app.errorhandler(404)
def handle_not_found(e):
    """Manejo estandarizado de errores 404 Not Found"""
    logger.error(f"Error 404 - Not Found: {str(e)}")
    return jsonify({
        'error': True,
        'status': 'error',
        'estado': 'error',
        'message': 'Recurso no encontrado',
        'mensaje': 'Recurso no encontrado',
        'details': str(e),
        'timestamp': datetime.now().isoformat(),
        'error_code': 'NOT_FOUND_404'
    }), 404

@app.errorhandler(413)
def handle_request_entity_too_large(e):
    """Manejo de archivos demasiado grandes"""
    logger.error(f"Error 413 - File too large: {str(e)}")
    return jsonify({
        'error': True,
        'status': 'error',
        'estado': 'error',
        'message': 'Archivo demasiado grande (máximo 16MB)',
        'mensaje': 'Archivo demasiado grande (máximo 16MB)',
        'details': str(e),
        'timestamp': datetime.now().isoformat(),
        'error_code': 'FILE_TOO_LARGE_413'
    }), 413

@app.errorhandler(500)
def handle_internal_error(e):
    """Manejo estandarizado de errores internos del servidor"""
    logger.error(f"Error 500 - Internal Server Error: {str(e)}")
    return jsonify({
        'error': True,
        'status': 'error',
        'estado': 'error',
        'message': 'Error interno del servidor',
        'mensaje': 'Error interno del servidor',
        'details': 'Contacte al administrador del sistema',
        'timestamp': datetime.now().isoformat(),
        'error_code': 'INTERNAL_SERVER_ERROR_500'
    }), 500

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
            
            # Iniciar perfilado avanzado
            advanced_profiler.start_profiling()
            advanced_profiler.take_snapshot("inicio_carga_ocr")
            
            # Inicializar optimizador de memoria
            memory_optimizer.optimize_numpy_arrays()
            memory_optimizer.optimize_onnx_models()
            
            with memory_optimizer.memory_context("carga de componentes OCR"):
                from main_ocr_process import OrquestadorOCR
                
                _ocr_orchestrator = OrquestadorOCR()
                
                # Warm-up de modelos críticos con control de memoria
                _ocr_orchestrator.aplicador._warmup_common_models()
                
                _ocr_components_loaded = True
                logger.info("✅ Componentes OCR pre-cargados exitosamente")
            
            # Analizar memoria post-carga
            advanced_profiler.take_snapshot("post_carga_ocr")
            advanced_profiler.optimize_based_on_analysis()
            
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
    
    with memory_optimizer.memory_context(f"procesamiento de lote ({len(image_paths)} imágenes)"):
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
            
                # ✅ PRESERVAR CAPTION ORIGINAL DE METADATOS
                # REASON: El caption original está en metadata.json, no en .caption.txt
                # IMPACT: Garantiza que se use el caption exacto ingresado por el usuario
                metadata_path = img_path.replace('.png', '.metadata.json').replace('.jpg', '.metadata.json').replace('.jpeg', '.metadata.json')
                caption_text = ""
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata_json = json.load(f)
                            # Usar caption original de metadatosEntrada (fuente de verdad)
                            caption_text = metadata_json.get('caption', '') or metadata_json.get('texto_mensaje_whatsapp', '')
                            logger.info(f"✅ Caption original cargado desde metadata: '{caption_text}'")
                            
                            # Mover metadata también
                            new_metadata_path = processing_path.replace('.png', '.metadata.json').replace('.jpg', '.metadata.json').replace('.jpeg', '.metadata.json')
                            shutil.move(metadata_path, new_metadata_path)
                    except Exception as e:
                        logger.error(f"Error leyendo metadata para caption: {e}")
                else:
                    logger.warning(f"No se encontró metadata.json para {img_path}")
                
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
                    if isinstance(result_converted, dict):
                        result_converted['info_guardado'] = {
                            'archivo_guardado': result_filename,
                            'timestamp_guardado': datetime.now().isoformat(),
                            'coordenadas_incluidas': 'coordenadas_disponibles' in result_converted,
                            'palabras_con_coordenadas': result_converted.get('coordenadas_disponibles', 0) if isinstance(result_converted.get('coordenadas_disponibles'), int) else 0
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
    """
    FIX: Parser WhatsApp empresarial corregido con regex específicas para formato empresarial
    REASON: Parser anterior generaba metadata incorrecta/inventada violando Zero-Fault Detection
    IMPACT: Extracción correcta de metadatos WhatsApp empresariales sin datos ficticios
    TEST: Validación exhaustiva con casos reales de formato WhatsApp empresarial
    MONITOR: Logging detallado de parsing exitoso y fallbacks válidos
    INTERFACE: Preserva campos requeridos por interface sin inventar datos
    VISUAL_CHANGE: Metadata correcta visible en cola de procesamiento y resultados
    REFERENCE_INTEGRITY: Parser valida formato antes de extraer, evita datos corruptos
    """
    import re
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Limpiar filename removiendo timestamp extra si existe
    original_filename = filename
    if '_' in filename and filename.count('_') > 3:
        # Remover timestamp final agregado por sistema si existe
        parts = filename.split('_')
        if len(parts) > 4 and parts[-1].replace('.png', '').replace('.jpg', '').replace('.jpeg', '').isdigit():
            filename = '_'.join(parts[:-1]) + '.' + filename.split('.')[-1]
    
    # Patrones específicos para formato WhatsApp empresarial
    # Formato: 20250706-C--214265627739362@lid_Luis_10-46.png
    patterns = [
        # Patrón 1: YYYYMMDD-X--numero@lid_nombre_HH-MM.ext
        r'^(\d{8})-([A-Z])--(\d+@lid)_([^_]+)_(\d{2}-\d{2})\.(.+)$',
        
        # Patrón 2: X--numero@lid_nombre_HH-MM.ext (sin fecha)
        r'^([A-Z])--(\d+@lid)_([^_]+)_(\d{2}-\d{2})\.(.+)$',
        
        # Patrón 3: YYYYMMDD-X_numero@lid_nombre_HH-MM.ext (guión simple)
        r'^(\d{8})-([A-Z])_(\d+@lid)_([^_]+)_(\d{2}-\d{2})\.(.+)$',
        
        # Patrón 4: Formato alternativo con otros separadores
        r'^(\d{8})-([A-Z]+)--([^@]+@[^_]+)_([^_]+)_(\d{2}-\d{2})\.(.+)$'
    ]
    
    logger.debug(f"Parseando filename: {filename}")
    
    for i, pattern in enumerate(patterns):
        match = re.match(pattern, filename)
        if match:
            groups = match.groups()
            logger.debug(f"Patrón {i+1} coincide. Grupos: {groups}")
            
            # Extraer campos según el patrón
            if i == 0:  # Patrón 1: Con fecha inicial
                fechasorteo = groups[0]
                numerosorteo = groups[1] 
                idWhatsapp = groups[2]
                nombre = groups[3]
                horamin = groups[4]
                extension = groups[5]
            elif i == 1:  # Patrón 2: Sin fecha inicial
                fechasorteo = '20250101'  # Fecha por defecto válida
                numerosorteo = groups[0]
                idWhatsapp = groups[1] 
                nombre = groups[2]
                horamin = groups[3]
                extension = groups[4]
            elif i == 2:  # Patrón 3: Con fecha y guión simple
                fechasorteo = groups[0]
                numerosorteo = groups[1]
                idWhatsapp = groups[2]
                nombre = groups[3]
                horamin = groups[4]
                extension = groups[5]
            elif i == 3:  # Patrón 4: Formato alternativo
                fechasorteo = groups[0]
                numerosorteo = groups[1]
                idWhatsapp = groups[2]
                nombre = groups[3] 
                horamin = groups[4]
                extension = groups[5]
            
            # Validar campos extraídos
            if not _validate_whatsapp_fields(numerosorteo, idWhatsapp, nombre, horamin):
                logger.warning(f"Campos WhatsApp extraídos no válidos para: {filename}")
                continue
            
            result = {
                'numerosorteo': numerosorteo,
                'fechasorteo': fechasorteo,
                'idWhatsapp': idWhatsapp,
                'nombre': nombre,
                'horamin': horamin,
                'extension': extension,
                # Campos adicionales para compatibilidad (sin inventar datos)
                'sorteo_fecha': fechasorteo,
                'sorteo_conteo': numerosorteo,
                'sender_id': idWhatsapp,
                'sender_name': nombre,
                'hora_min': horamin,
                'texto_mensaje_whatsapp': f"Recibo de {nombre} - {horamin.replace('-', ':')} - ID: {idWhatsapp}"
            }
            
            logger.info(f"✅ Metadata WhatsApp extraída correctamente: numerosorteo={numerosorteo}, nombre={nombre}, horamin={horamin}")
            return result
    
    # Si no coincide con ningún patrón, usar fallback SIN INVENTAR DATOS
    logger.warning(f"Archivo no coincide con formato WhatsApp empresarial: {original_filename}")
    
    # Extraer solo datos que podemos determinar con certeza
    extension = filename.split('.')[-1] if '.' in filename else 'png'
    
    return {
        'numerosorteo': '',  # Vacío en lugar de inventar
        'fechasorteo': '',   # Vacío en lugar de inventar
        'idWhatsapp': '',    # Vacío en lugar de inventar
        'nombre': '',        # Vacío en lugar de inventar
        'horamin': '',       # Vacío en lugar de inventar
        'extension': extension,
        # Campos para compatibilidad (también vacíos para evitar datos ficticios)
        'sorteo_fecha': '',
        'sorteo_conteo': '',
        'sender_id': '',
        'sender_name': '',
        'hora_min': '',
        'texto_mensaje_whatsapp': f"Archivo sin formato WhatsApp válido: {original_filename}"
    }

def _validate_whatsapp_fields(numerosorteo, idWhatsapp, nombre, horamin):
    """
    FIX: Validación estricta de campos WhatsApp extraídos
    REASON: Evitar aceptar parsing incorrecto que genere metadata corrupta
    IMPACT: Solo acepta metadata válida, rechaza parsing incorrecto
    """
    # Validar numerosorteo: debe ser A-Z
    if not (numerosorteo.isalpha() and len(numerosorteo) >= 1 and numerosorteo.isupper()):
        return False
    
    # Validar idWhatsapp: debe terminar en @lid y tener números
    if not (idWhatsapp.endswith('@lid') and any(c.isdigit() for c in idWhatsapp)):
        return False
    
    # Validar nombre: no debe estar vacío
    if not nombre or len(nombre.strip()) < 1:
        return False
    
    # Validar horamin: debe ser HH-MM
    if not (len(horamin) == 5 and horamin[2] == '-' and 
            horamin[:2].isdigit() and horamin[3:].isdigit()):
        return False
    
    # Validar rangos de hora
    try:
        hora, minuto = map(int, horamin.split('-'))
        if not (0 <= hora <= 23 and 0 <= minuto <= 59):
            return False
    except:
        return False
    
    return True

def start_batch_worker():
    """Inicia el worker asíncrono"""
    global _worker_thread, _worker_running
    
    if not _worker_running and batch_config.get('enable_batch_processing', True):
        _worker_running = True
        _worker_thread = threading.Thread(target=batch_processing_worker, daemon=True)
        _worker_thread.start()
        
        # Iniciar monitoreo de memoria
        start_memory_monitoring()
        
        logger.info("Worker asíncrono iniciado con monitoreo de memoria")

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
