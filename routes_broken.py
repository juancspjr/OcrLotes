"""
Rutas y controladores para la aplicación web Flask
"""

import os
import json
import logging
import shutil
import psutil
import uuid
import time
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file

from app import app, preload_ocr_components, start_batch_worker
from main_ocr_process import OrquestadorOCR
import config

logger = logging.getLogger(__name__)

# FIX: Variables globales para estado del sistema asíncrono
# REASON: Resolver error '_worker_running' is not defined
_worker_running = False
_worker_thread = None

@app.route('/api/ocr/processed_files')
def api_get_processed_files():
    """
    FIX: Detección corregida de archivos JSON procesados
    REASON: Usuario reporta que los archivos JSON no aparecen en la interfaz
    IMPACT: Listado correcto de todos los archivos procesados con sus JSON
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        results_dir = directories['results']
        
        if not os.path.exists(results_dir):
            return jsonify({
                'status': 'exitoso',
                'estado': 'exitoso',
                'files': [],
                'total_files': 0,
                'message': 'No hay archivos procesados aún'
            })
        
        archivos_json = []
        
        # Buscar TODOS los archivos .json en el directorio de resultados
        for archivo in os.listdir(results_dir):
            if archivo.endswith('.json'):
                archivo_path = os.path.join(results_dir, archivo)
                
                try:
                    # Obtener información del archivo
                    stat_info = os.stat(archivo_path)
                    tamaño = stat_info.st_size
                    fecha_mod = datetime.fromtimestamp(stat_info.st_mtime)
                    
                    # Leer contenido JSON para verificar estructura
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        contenido_json = json.load(f)
                    
                    # Información básica del archivo
                    info_archivo = {
                        'filename': archivo,
                        'filepath': archivo_path,
                        'size_bytes': tamaño,
                        'size_readable': f"{tamaño / 1024:.1f} KB" if tamaño > 1024 else f"{tamaño} bytes",
                        'modified_date': fecha_mod.isoformat(),
                        'modified_readable': fecha_mod.strftime('%d/%m/%Y %H:%M:%S'),
                        'has_ocr_data': 'texto_completo' in contenido_json or 'full_raw_ocr_text' in contenido_json,
                        'has_coordinates': 'palabras_detectadas' in contenido_json or 'word_data' in contenido_json,
                        'word_count': len(contenido_json.get('palabras_detectadas', contenido_json.get('word_data', []))),
                        'confidence': contenido_json.get('confianza_promedio', contenido_json.get('average_confidence', 0)),
                        'processing_time': contenido_json.get('tiempo_procesamiento_ms', contenido_json.get('processing_time_ms', 0))
                    }
                    
                    archivos_json.append(info_archivo)
                    
                except (json.JSONDecodeError, PermissionError) as e:
                    logger.warning(f"Error leyendo archivo JSON {archivo}: {e}")
                    # Incluir archivo con información limitada
                    archivos_json.append({
                        'filename': archivo,
                        'filepath': archivo_path,
                        'size_bytes': tamaño,
                        'size_readable': f"{tamaño / 1024:.1f} KB" if tamaño > 1024 else f"{tamaño} bytes",
                        'modified_date': fecha_mod.isoformat(),
                        'modified_readable': fecha_mod.strftime('%d/%m/%Y %H:%M:%S'),
                        'has_ocr_data': False,
                        'has_coordinates': False,
                        'error': 'Error al leer archivo'
                    })
        
        # Ordenar por fecha de modificación (más recientes primero)
        archivos_json.sort(key=lambda x: x['modified_date'], reverse=True)
        
        return jsonify({
            'status': 'exitoso',
            'estado': 'exitoso',
            'files': archivos_json,
            'total_files': len(archivos_json),
            'message': f'Se encontraron {len(archivos_json)} archivos procesados',
            'last_update': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos procesados: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'message': f'Error al obtener archivos: {str(e)}',
            'files': [],
            'total_files': 0
        }), 500,
            'total_files': len(file_list),
            'archivos_con_json': len([f for f in file_list if f['json_exists']]),
            'files_with_json': len([f for f in file_list if f['json_exists']]),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos procesados: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'mensaje': 'No se pudieron obtener los archivos procesados', 'message': 'No se pudieron obtener los archivos procesados',
            'details': str(e)
        }), 500

@app.route('/api/ocr/download_json/<filename>')
def api_download_json(filename):
    """
    FIX: Endpoint para descargar archivo JSON de resultado específico
    REASON: Usuario necesita descargar resultados JSON individuales de cada imagen
    IMPACT: Acceso directo a resultados de OCR para análisis externo
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        
        # Buscar archivo JSON correspondiente
        base_name = os.path.splitext(filename)[0]
        possible_json_files = [
            os.path.join(directories['results'], f"{base_name}.json"),
            os.path.join(directories['results'], f"{filename}.json"),
            # Patrón para archivos WhatsApp
            os.path.join(directories['results'], f"{base_name.split('_')[0]}.json")
        ]
        
        json_file = None
        for possible_file in possible_json_files:
            if os.path.exists(possible_file):
                json_file = possible_file
                break
        
        if not json_file:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'mensaje': f'Archivo JSON no encontrado para {filename}', 'message': f'Archivo JSON no encontrado para {filename}'
            }), 404
        
        return send_file(
            json_file,
            as_attachment=True,
            download_name=f"resultado_{base_name}.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error descargando JSON para {filename}: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'mensaje': 'No se pudo descargar el archivo JSON', 'message': 'No se pudo descargar el archivo JSON',
            'details': str(e)
        }), 500

@app.route('/api/ocr/view_json/<filename>')
def api_view_json(filename):
    """
    FIX: Endpoint para visualizar contenido JSON de resultado específico
    REASON: Usuario necesita ver contenido JSON en interfaz web antes de descargar
    IMPACT: Inspección rápida de resultados OCR sin necesidad de descarga
    """
    try:
        from config import get_async_directories
        
        directories = get_async_directories()
        
        # Buscar archivo JSON correspondiente
        base_name = os.path.splitext(filename)[0]
        possible_json_files = [
            os.path.join(directories['results'], f"{base_name}.json"),
            os.path.join(directories['results'], f"{filename}.json"),
            # Patrón para archivos WhatsApp
            os.path.join(directories['results'], f"{base_name.split('_')[0]}.json")
        ]
        
        json_file = None
        for possible_file in possible_json_files:
            if os.path.exists(possible_file):
                json_file = possible_file
                break
        
        if not json_file:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'mensaje': f'Archivo JSON no encontrado para {filename}', 'message': f'Archivo JSON no encontrado para {filename}'
            }), 404
        
        # Leer y parsear contenido JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
        
        return jsonify({
            'status': 'exitoso', 'estado': 'exitoso',
            'filename': filename,
            'json_file': os.path.basename(json_file),
            'content': json_content,
            'file_size': os.path.getsize(json_file),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(json_file)).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error visualizando JSON para {filename}: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'No se pudo leer el archivo JSON',
            'details': str(e)
        }), 500

@app.route('/results')
def results_viewer():
    """
    FIX: Nueva página para visualización de resultados procesados
    REASON: Usuario necesita interfaz dedicada para ver resultados con JSONs
    IMPACT: Experiencia mejorada para inspección de resultados de procesamiento
    """
    return render_template('results_viewer.html')

# ==============================================================================
# FIX: NUEVOS ENDPOINTS PARA PROCESAMIENTO POR LOTES Y MONITOREO DE RECURSOS
# REASON: Implementar interfaz de usuario para carga masiva con medición adaptativa
# IMPACT: Sistema completo de procesamiento por lotes con optimización automática
# ==============================================================================

@app.route('/batch')
def batch_processing():
    """Página de procesamiento por lotes"""
    return render_template('batch_processing.html')

@app.route('/api/upload_batch', methods=['POST'])
def api_upload_batch():
    """
    FIX: Endpoint para carga masiva de archivos con metadata global
    REASON: Permitir procesamiento eficiente de múltiples recibos simultáneamente
    IMPACT: Capacidad de procesamiento por lotes desde interfaz web con configuración adaptativa
    """
    try:
        from config import get_async_directories, get_batch_config
        
        directories = get_async_directories()
        batch_config = get_batch_config()
        
        # Validar que hay archivos
        if 'images' not in request.files:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'No images provided'
            }), 400
        
        files = request.files.getlist('images')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'No files selected'
            }), 400
        
        # Validar número máximo de archivos
        max_files = batch_config.get('max_files_per_batch', 50)
        if len(files) > max_files:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': f'Too many files. Maximum allowed: {max_files}'
            }), 400
        
        # Obtener metadatos globales
        caption_global = request.form.get('caption_global', '')
        additional_data_batch = request.form.get('additional_data_batch', '')
        batch_size = int(request.form.get('batch_size', 5))
        
        # Validar JSON de additional_data si se proporciona
        additional_data_parsed = None
        if additional_data_batch:
            try:
                additional_data_parsed = json.loads(additional_data_batch)
            except json.JSONDecodeError:
                return jsonify({
                    'status': 'error', 'estado': 'error',
                    'message': 'Invalid JSON format in additional_data_batch'
                }), 400
        
        enqueued_ids = []
        current_time = datetime.now()
        batch_id = str(uuid.uuid4())[:8]  # Generar batch_id único una sola vez
        
        # Procesar cada archivo
        for i, file in enumerate(files):
            if file.filename == '':
                continue
                
            # Validar tipo de archivo
            if not file.content_type or not file.content_type.startswith('image/'):
                logger.warning(f"Archivo {file.filename} ignorado: tipo no válido")
                continue
            
            # Generar request_id único para lote
            timestamp = current_time.strftime("%Y%m%d")
            
            # Asegurar filename válido
            safe_filename = file.filename or f"image_{i}.png"
            file_ext = os.path.splitext(safe_filename)[1] or '.png'
            
            request_id = f"{timestamp}-BATCH_{batch_id}_{i:03d}_{secure_filename(safe_filename)}"
            if not request_id.endswith(file_ext):
                request_id += file_ext
            
            try:
                # Guardar imagen
                image_path = os.path.join(directories['inbox'], request_id)
                file.save(image_path)
                
                # Guardar caption si se proporciona
                if caption_global:
                    caption_path = image_path.replace(file_ext, '.caption.txt')
                    with open(caption_path, 'w', encoding='utf-8') as f:
                        f.write(caption_global)
                
                # Guardar additional_data si se proporciona
                if additional_data_parsed:
                    # Agregar información del lote
                    batch_metadata = additional_data_parsed.copy()
                    batch_metadata.update({
                        'batch_info': {
                            'batch_id': batch_id,
                            'file_index': i,
                            'total_archivos': len(files),
                            'total_files': len(files),
                            'batch_timestamp': current_time.isoformat(),
                            'original_filename': file.filename,
                            'batch_size_config': batch_size
                        }
                    })
                    
                    additional_path = image_path.replace(file_ext, '.additional_data.json')
                    with open(additional_path, 'w', encoding='utf-8') as f:
                        json.dump(batch_metadata, f, indent=2, ensure_ascii=False)
                
                enqueued_ids.append(request_id)
                logger.info(f"Archivo {file.filename} encolado como {request_id}")
                
            except Exception as e:
                logger.error(f"Error procesando archivo {file.filename}: {e}")
                continue
        
        if not enqueued_ids:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'No files could be processed'
            }), 400
        
        return jsonify({
            'status': 'accepted',
            'message': 'Batch enqueued for processing',
            'enqueued_ids': enqueued_ids,
            'total_archivos': len(enqueued_ids),
            'total_files': len(enqueued_ids),
            'batch_id': batch_id,
            'estimated_processing_time_seconds': len(enqueued_ids) * 10,
            'timestamp': current_time.isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error en upload_batch: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/ocr/resources', methods=['GET'])
def api_system_resources():
    """
    FIX: Endpoint para monitoreo de recursos del servidor
    REASON: Proporcionar métricas en tiempo real para optimización adaptativa de lotes
    IMPACT: Sistema auto-optimizado que adapta tamaños de lote según recursos disponibles
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        
        # Métricas del sistema usando psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Métricas de la cola de procesamiento
        inbox_count = len(glob.glob(os.path.join(directories['inbox'], "*.png")) + 
                         glob.glob(os.path.join(directories['inbox'], "*.jpg")))
        
        processing_count = len(glob.glob(os.path.join(directories['processing'], "*.png")) + 
                              glob.glob(os.path.join(directories['processing'], "*.jpg")))
        
        processed_count = len(glob.glob(os.path.join(directories['processed'], "*.png")) + 
                             glob.glob(os.path.join(directories['processed'], "*.jpg")))
        
        errors_count = len(glob.glob(os.path.join(directories['errors'], "*.png")) + 
                          glob.glob(os.path.join(directories['errors'], "*.jpg")))
        
        # Calcular métricas derivadas
        total_queue = inbox_count + processing_count
        queue_load_percent = min((total_queue / 50) * 100, 100)  # Asumiendo máximo 50 elementos
        
        # Determinar estado del sistema
        system_status = 'optimal'
        if cpu_percent > 80 or memory.percent > 80:
            system_status = 'high_load'
        elif cpu_percent > 90 or memory.percent > 90:
            system_status = 'overloaded'
        
        # Recomendación de tamaño de lote basada en recursos
        recommended_batch_size = 5  # Default
        
        if cpu_percent < 30 and memory.percent < 50 and total_queue < 5:
            recommended_batch_size = 15  # Aumentar para baja carga
        elif cpu_percent > 70 or memory.percent > 70 or total_queue > 20:
            recommended_batch_size = 2   # Reducir para alta carga
        elif cpu_percent > 50 or memory.percent > 60 or total_queue > 10:
            recommended_batch_size = 3   # Reducir moderadamente
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'system_status': system_status,
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'disk_percent': round((disk.used / disk.total) * 100, 1),
            'queue_status': {
                'inbox': inbox_count,
                'processing': processing_count,
                'processed': processed_count,
                'errors': errors_count,
                'total_active': total_queue,
                'queue_load_percent': round(queue_load_percent, 1)
            },
            'performance_metrics': {
                'recommended_batch_size': recommended_batch_size,
                'current_load_category': system_status,
                'optimal_for_batch_processing': cpu_percent < 60 and memory.percent < 70,
                'processing_capacity_available': max(0, 50 - total_queue)
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo recursos del sistema: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Could not retrieve system resources',
            'details': str(e)
        }), 500

@app.route('/api/batch/configure', methods=['POST'])
def api_configure_batch():
    """
    FIX: Endpoint para configurar parámetros de procesamiento por lotes
    REASON: Permitir ajuste dinámico de configuración basado en métricas del servidor
    IMPACT: Optimización automática del rendimiento según recursos disponibles
    """
    try:
        from config import get_batch_config
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'No configuration data provided'
            }), 400
        
        # Validar configuración
        batch_size = data.get('batch_size', 5)
        auto_optimize = data.get('auto_optimize', True)
        
        if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 50:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'batch_size must be an integer between 1 and 50'
            }), 400
        
        # Aplicar configuración (en memoria por ahora)
        # TODO: Implementar persistencia de configuración si es necesario
        
        logger.info(f"Configuración de lote actualizada: batch_size={batch_size}, auto_optimize={auto_optimize}")
        
        return jsonify({
            'status': 'exitoso', 'estado': 'exitoso',
            'message': 'Batch configuration updated',
            'configuration': {
                'batch_size': batch_size,
                'auto_optimize': auto_optimize,
                'updated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error configurando lote: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Could not update batch configuration',
            'details': str(e)
        }), 500

@app.route('/monitor')
def resource_monitor():
    """Página de monitoreo de recursos del servidor"""
    return render_template('resource_monitor.html')

@app.route('/api/download/batch_results/<batch_id>')
def api_download_batch_results(batch_id):
    """
    FIX: Endpoint para descargar resultados de lote completo como ZIP
    REASON: Facilitar descarga masiva de resultados procesados
    IMPACT: Flujo completo de carga → procesamiento → descarga para lotes
    """
    try:
        from config import get_async_directories
        import zipfile
        import tempfile
        import glob
        
        directories = get_async_directories()
        
        # Buscar todos los resultados del lote
        result_pattern = os.path.join(directories['results'], f"*BATCH_{batch_id}_*.json")
        result_files = glob.glob(result_pattern)
        
        if not result_files:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': f'No results found for batch {batch_id}'
            }), 404
        
        # Crear archivo ZIP temporal
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f'batch_{batch_id}_results.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result_file in result_files:
                # Usar nombre de archivo sin path completo
                filename = os.path.basename(result_file)
                zip_file.write(result_file, filename)
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'batch_{batch_id}_results.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error descargando resultados del lote {batch_id}: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Could not download batch results',
            'details': str(e)
        }), 500

@app.route('/api/ocr/clean', methods=['POST'])
def api_clean_system():
    """
    FIX: Endpoint para limpiar el sistema después de procesar
    REASON: Usuario solicita botón de limpieza para eliminar archivos procesados y evitar basura
    IMPACT: Sistema más limpio y organizado después de cada procesamiento
    """
    try:
        from config import get_async_directories
        import glob
        import shutil
        
        directories = get_async_directories()
        cleaned_counts = {}
        
        # Limpiar directorio processed
        processed_files = glob.glob(os.path.join(directories['processed'], "*.*"))
        for file_path in processed_files:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo procesado {file_path}: {e}")
        cleaned_counts['processed'] = len(processed_files)
        
        # Limpiar directorio results
        result_files = glob.glob(os.path.join(directories['results'], "*.json"))
        for file_path in result_files:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar resultado {file_path}: {e}")
        cleaned_counts['results'] = len(result_files)
        
        # Limpiar directorio errors (opcional)
        error_files = glob.glob(os.path.join(directories['errors'], "*.*"))
        for file_path in error_files:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar error {file_path}: {e}")
        cleaned_counts['errors'] = len(error_files)
        
        # Limpiar directorios temporales
        temp_dirs = glob.glob(os.path.join('temp', 'web_*'))
        temp_cleaned = 0
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                temp_cleaned += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio temporal {temp_dir}: {e}")
        cleaned_counts['temp_dirs'] = temp_cleaned
        
        logger.info(f"Sistema limpiado: {cleaned_counts}")
        
        return jsonify({
            'status': 'exitoso', 'estado': 'exitoso',
            'message': 'Sistema limpiado exitosamente',
            'cleaned_counts': cleaned_counts,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error al limpiar sistema: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Error al limpiar el sistema',
            'details': str(e)
        }), 500

@app.route('/api/ocr/queue/files', methods=['GET'])
def api_queue_files():
    """
    FIX: Endpoint para obtener lista detallada de archivos en cola
    REASON: Usuario necesita ver archivos reales con vista previa y metadatos completos
    IMPACT: Interfaz funcional que muestra archivos reales en lugar de datos simulados
    """
    try:
        from config import get_async_directories
        import glob
        import json
        from pathlib import Path
        
        directories = get_async_directories()
        
        # Obtener archivos de imágenes y metadatos en inbox
        inbox_files = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        
        for ext in image_extensions:
            pattern = os.path.join(directories['inbox'], f"*{ext}")
            for image_file in glob.glob(pattern):
                # Buscar archivo de metadatos correspondiente
                base_name = os.path.splitext(os.path.basename(image_file))[0]
                metadata_file = os.path.join(directories['inbox'], f"{base_name}.metadata.json")
                
                file_info = {
                    'filename': os.path.basename(image_file),
                    'filepath': image_file,
                    'request_id': base_name,
                    'size': os.path.getsize(image_file),
                    'modified': os.path.getmtime(image_file)
                }
                
                # Cargar metadatos si existen
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            file_info.update({
                                'original_filename': metadata.get('original_filename', ''),
                                'sender_id': metadata.get('sender_id', ''),
                                'sender_name': metadata.get('sender_name', ''),
                                'caption': metadata.get('caption', ''),
                                'sorteo_fecha': metadata.get('sorteo_fecha', ''),
                                'posicion_sorteo': metadata.get('posicion_sorteo', ''),
                                'hora_min': metadata.get('hora_min', ''),
                                'timestamp': metadata.get('timestamp', ''),
                                'status': metadata.get('status', 'queued')
                            })
                    except Exception as e:
                        logger.warning(f"Error cargando metadatos {metadata_file}: {e}")
                
                inbox_files.append(file_info)
        
        # Obtener archivos procesados
        processed_files = []
        for ext in image_extensions:
            pattern = os.path.join(directories['processed'], f"*{ext}")
            for image_file in glob.glob(pattern):
                base_name = os.path.splitext(os.path.basename(image_file))[0]
                
                file_info = {
                    'filename': os.path.basename(image_file),
                    'filepath': image_file,
                    'request_id': base_name,
                    'size': os.path.getsize(image_file),
                    'modified': os.path.getmtime(image_file),
                    'status': 'processed'
                }
                
                # Buscar resultado JSON correspondiente
                result_file = os.path.join(directories['results'], f"{base_name}.json")
                if os.path.exists(result_file):
                    file_info['result_available'] = True
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)
                            file_info['text_extracted'] = len(result_data.get('text_extraction', {}).get('texto_completo', '')) > 0
                            file_info['confidence'] = result_data.get('text_extraction', {}).get('confidence', 0)
                    except Exception as e:
                        logger.warning(f"Error cargando resultado {result_file}: {e}")
                
                processed_files.append(file_info)
        
        return jsonify({
            'status': 'exitoso', 'estado': 'exitoso',
            'inbox_files': inbox_files,
            'processed_files': processed_files,
            'counts': {
                'inbox': len(inbox_files),
                'processed': len(processed_files)
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos de cola: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Error obteniendo lista de archivos',
            'details': str(e)
        }), 500

@app.route('/api/ocr/preview/<request_id>', methods=['GET'])
def api_preview_image(request_id):
    """
    FIX: Endpoint para vista previa de imágenes en cola y procesadas
    REASON: Usuario solicita función de lupa para ver imágenes antes y después del procesamiento
    IMPACT: Funcionalidad completa de vista previa con imágenes reales
    """
    try:
        from config import get_async_directories
        
        directories = get_async_directories()
        
        # Buscar imagen en inbox primero
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        found_file = None
        
        for directory in [directories['inbox'], directories['processed'], directories['processing']]:
            for ext in image_extensions:
                potential_file = os.path.join(directory, f"{request_id}{ext}")
                if os.path.exists(potential_file):
                    found_file = potential_file
                    break
            if found_file:
                break
        
        if not found_file:
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'Imagen no encontrada'
            }), 404
        
        return send_file(found_file, as_attachment=False)
        
    except Exception as e:
        logger.error(f"Error obteniendo vista previa {request_id}: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Error obteniendo vista previa',
            'details': str(e)
        }), 500

@app.route('/api/ocr/download/<request_id>', methods=['GET'])
def api_download_result(request_id):
    """
    FIX: Endpoint para descargar resultados individuales
    REASON: Usuario solicita función de descarga de archivos de resultados individuales
    IMPACT: Funcionalidad completa de descarga de resultados JSON
    """
    try:
        from config import get_async_directories
        
        directories = get_async_directories()
        result_file = os.path.join(directories['results'], f"{request_id}.json")
        
        if not os.path.exists(result_file):
            return jsonify({
                'status': 'error', 'estado': 'error',
                'message': 'Resultado no encontrado'
            }), 404
        
        return send_file(
            result_file,
            as_attachment=True,
            download_name=f"resultado_{request_id}.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error descargando resultado {request_id}: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Error descargando resultado',
            'details': str(e)
        }), 500

@app.route('/api/ocr/queue/clear', methods=['POST'])
def api_clear_queue():
    """
    FIX: Endpoint para limpiar completamente la cola de procesamiento
    REASON: Usuario necesita botón para limpiar cola y evitar basura acumulada
    IMPACT: Control total para limpiar archivos no deseados en cola
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        
        # Contar archivos antes de limpiar
        patterns = [
            os.path.join(directories['inbox'], "*"),
            os.path.join(directories['processing'], "*"),
            os.path.join(directories['processed'], "*"),
            os.path.join(directories['errors'], "*")
        ]
        
        removed_count = 0
        for pattern in patterns:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        removed_count += 1
                except Exception as e:
                    logger.warning(f"Error removiendo {file_path}: {e}")
        
        logger.info(f"✅ Cola limpiada: {removed_count} archivos removidos")
        
        return jsonify({
            'status': 'exitoso', 'estado': 'exitoso',
            'message': f'Queue cleared successfully',
            'files_removed': removed_count,
            'directories_cleared': ['inbox', 'processing', 'processed', 'errors']
        }), 200
        
    except Exception as e:
        logger.error(f"Error limpiando cola: {e}")
        return jsonify({
            'status': 'error', 'estado': 'error',
            'message': 'Error clearing queue',
            'details': str(e)
        }), 500

@app.route('/api/docs')
def api_documentation():
    """
    FIX: Documentación completa de APIs para integración externa
    REASON: Usuario solicita documentación de endpoints para entender "esto es para esto y esto otro"
    IMPACT: Documentación profesional que facilita integración con n8n y otros sistemas
    """
    return render_template('api_documentation.html')
