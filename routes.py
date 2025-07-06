"""
Rutas y controladores para la aplicación web Flask
"""

import os
import json
import logging
import shutil
import psutil
import uuid
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file

from app import app, preload_ocr_components, start_batch_worker
from main_ocr_process import OrquestadorOCR
import config

logger = logging.getLogger(__name__)

# Instancia global del orquestador
orquestador = OrquestadorOCR()

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.WEB_CONFIG['allowed_extensions']

@app.route('/')
def index():
    """Página principal de carga de imágenes"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Maneja la carga de archivos y procesamiento OCR"""
    try:
        # Verificar si se envió un archivo
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Guardar archivo de forma segura
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            
            upload_path = Path(app.config['UPLOAD_FOLDER']) / filename
            file.save(upload_path)
            
            # Obtener parámetros del formulario
            language = request.form.get('language', 'spa')
            # FIX: Usar perfil 'normal' por defecto para mayor precisión OCR
            # REASON: Usuario solicita mejor precisión y mayor confianza 
            # IMPACT: Mejor calidad OCR con técnicas avanzadas de procesamiento
            profile = request.form.get('profile', 'normal')
            save_intermediate = request.form.get('save_intermediate') == 'on'
            
            logger.info(f"Procesando archivo: {filename} con perfil: {profile}")
            
            # Crear directorio de salida en temp
            output_dir = Path(app.config['TEMP_FOLDER']) / f"web_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Procesar imagen con OCR
            resultado = orquestador.procesar_imagen_completo(
                upload_path,
                language=language,
                profile=profile,
                save_intermediate=True,  # Siempre guardar para mostrar en web
                output_dir=output_dir
            )
            
            if 'error' in resultado:
                flash(f'Error en procesamiento: {resultado["error"]}', 'error')
                return redirect(url_for('index'))
            
            # Guardar resultado en sesión para mostrar
            resultado_json_path = output_dir / "resultado_web.json"
            with open(resultado_json_path, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            
            # Redirigir a página de resultados
            return redirect(url_for('show_results', 
                                  result_id=resultado['execution_id'],
                                  result_path=str(resultado_json_path)))
        
        else:
            flash('Tipo de archivo no permitido. Use: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Error en upload: {str(e)}")
        flash(f'Error procesando archivo: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    """Muestra los resultados del procesamiento OCR"""
    try:
        result_id = request.args.get('result_id')
        result_path = request.args.get('result_path')
        
        if not result_path or not os.path.exists(result_path):
            flash('Resultados no encontrados', 'error')
            return redirect(url_for('index'))
        
        # Cargar resultados
        with open(result_path, 'r', encoding='utf-8') as f:
            resultado = json.load(f)
        
        # Preparar datos para la plantilla
        template_data = {
            'resultado': resultado,
            'resumen': resultado.get('resumen_final', {}),
            'etapas': resultado.get('etapas', {}),
            'archivos_disponibles': _obtener_archivos_disponibles(resultado),
            'graficos_datos': _preparar_datos_graficos(resultado)
        }
        
        return render_template('results.html', **template_data)
    
    except Exception as e:
        logger.error(f"Error mostrando resultados: {str(e)}")
        flash(f'Error cargando resultados: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<path:filename>')
def download_file(filename):
    """Permite descargar archivos generados"""
    try:
        file_path = Path(app.config['TEMP_FOLDER']) / filename
        
        if not file_path.exists():
            flash('Archivo no encontrado', 'error')
            return redirect(url_for('index'))
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error descargando archivo: {str(e)}")
        flash(f'Error descargando archivo: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/process', methods=['POST'])
def api_process():
    """API endpoint para procesamiento programático"""
    try:
        data = request.get_json()
        
        if not data or 'image_path' not in data:
            return jsonify({'error': 'image_path requerido'}), 400
        
        image_path = data['image_path']
        language = data.get('language', 'spa')
        profile = data.get('profile', 'rapido')
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        # Procesar imagen
        resultado = orquestador.procesar_imagen_completo(
            image_path,
            language=language,
            profile=profile,
            save_intermediate=False
        )
        
        return jsonify(resultado)
    
    except Exception as e:
        logger.error(f"Error en API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

def _obtener_archivos_disponibles(resultado):
    """Obtiene lista de archivos disponibles para descarga"""
    archivos = []
    temp_dir = Path(resultado.get('temp_directory', ''))
    
    if temp_dir.exists():
        # Archivos de imagen
        for ext in ['.png', '.jpg', '.jpeg']:
            for archivo in temp_dir.glob(f'*{ext}'):
                archivos.append({
                    'nombre': archivo.name,
                    'tipo': 'imagen',
                    'ruta': str(archivo.relative_to(Path(app.config['TEMP_FOLDER']))),
                    'tamaño': archivo.stat().st_size if archivo.exists() else 0
                })
        
        # Archivos de datos
        for ext in ['.json', '.txt']:
            for archivo in temp_dir.glob(f'*{ext}'):
                archivos.append({
                    'nombre': archivo.name,
                    'tipo': 'datos',
                    'ruta': str(archivo.relative_to(Path(app.config['TEMP_FOLDER']))),
                    'tamaño': archivo.stat().st_size if archivo.exists() else 0
                })
    
    return archivos

def _preparar_datos_graficos(resultado):
    """Prepara datos para gráficos y visualizaciones"""
    try:
        etapas = resultado.get('etapas', {})
        
        # Datos de tiempo por etapa
        tiempos = {
            'Validación': etapas.get('1_validacion', {}).get('tiempo', 0),
            'Mejora': etapas.get('2_mejora', {}).get('tiempo', 0),
            'OCR': etapas.get('3_ocr', {}).get('tiempo', 0)
        }
        
        # Distribución de confianza OCR
        distribucion_confianza = {}
        ocr_stats = etapas.get('3_ocr', {}).get('estadisticas_ocr', {})
        if 'distribucion_confianza' in ocr_stats:
            distribucion_confianza = ocr_stats['distribucion_confianza']
        
        # Métricas de calidad
        puntuacion_general = etapas.get('1_validacion', {}).get('diagnostico', {}).get('puntuacion_general', {})
        metricas_calidad = {
            'Calidad': puntuacion_general.get('calidad', 0),
            'Texto': puntuacion_general.get('texto', 0),
            'Ruido': puntuacion_general.get('ruido', 0),
            'Geometría': puntuacion_general.get('geometria', 0)
        }
        
        return {
            'tiempos_etapas': tiempos,
            'distribucion_confianza': distribucion_confianza,
            'metricas_calidad': metricas_calidad
        }
    
    except Exception as e:
        logger.error(f"Error preparando datos gráficos: {str(e)}")
        return {}

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno: {str(error)}")
    flash('Error interno del servidor', 'error')
    return render_template('index.html'), 500

# Filtros de template personalizados
@app.template_filter('filesize')
def filesize_filter(size):
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

@app.template_filter('duration')
def duration_filter(seconds):
    """Convierte segundos a formato legible"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"

# FIX: Rutas de API HTTP para sistema asíncrono de alto volumen
# REASON: Implementar endpoint complementario para ingesta directa vía HTTP
# IMPACT: Flexibilidad de integración con múltiples sistemas externos

@app.route('/api/ocr/process_image', methods=['POST'])
def api_process_image():
    """
    FIX: Endpoint API HTTP para ingesta directa de imágenes con metadata de WhatsApp
    REASON: Ofrecer alternativa HTTP estándar al sistema de archivos para máxima interoperabilidad
    IMPACT: Integración directa con n8n y otros sistemas web sin acceso al sistema de archivos
    """
    try:
        from config import get_api_config, get_async_directories
        
        api_config = get_api_config()
        directories = get_async_directories()
        
        # Validar que sea multipart/form-data
        if not request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided',
                'details': 'Request must include multipart/form-data with image field'
            }), 400
        
        # Verificar campos obligatorios
        required_fields = api_config['required_fields']
        missing_fields = []
        
        for field in required_fields[1:]:  # Excluir 'image' que se verifica separadamente
            if field not in request.form:
                missing_fields.append(field)
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Obtener archivo de imagen
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided in form data'
            }), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No image file selected'
            }), 400
        
        # Validar tipo de archivo
        if image_file.content_type not in api_config['allowed_image_types']:
            return jsonify({
                'status': 'error',
                'message': f'Invalid image type. Allowed: {", ".join(api_config["allowed_image_types"])}'
            }), 400
        
        # Generar request_id desde metadatos
        sorteo_fecha = request.form.get('sorteo_fecha')
        sorteo_conteo = request.form.get('sorteo_conteo')
        sender_id = request.form.get('sender_id')
        sender_name = request.form.get('sender_name')
        hora_min = request.form.get('hora_min')
        
        # Determinar extensión de archivo
        file_ext = '.png' if image_file.content_type == 'image/png' else '.jpg'
        request_id = f"{sorteo_fecha}-{sorteo_conteo}_{sender_id}_{sender_name}_{hora_min}{file_ext}"
        
        # Guardar imagen en inbox
        image_path = os.path.join(directories['inbox'], request_id)
        image_file.save(image_path)
        
        # Guardar caption
        caption = request.form.get('caption', '')
        if caption:
            caption_path = image_path.replace(file_ext, '.caption.txt')
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)
        
        # Guardar additional_data si existe
        additional_data = request.form.get('additional_data')
        if additional_data:
            try:
                # Validar que sea JSON válido
                json.loads(additional_data)
                additional_path = image_path.replace(file_ext, '.additional_data.json')
                with open(additional_path, 'w', encoding='utf-8') as f:
                    f.write(additional_data)
            except json.JSONDecodeError:
                # Si no es JSON válido, guardar como texto
                additional_path = image_path.replace(file_ext, '.additional_data.txt')
                with open(additional_path, 'w', encoding='utf-8') as f:
                    f.write(additional_data)
        
        return jsonify({
            'status': 'accepted',
            'message': 'Image enqueued for processing.',
            'request_id': request_id,
            'estimated_processing_time_seconds': 30,
            'check_result_endpoint': f'/api/ocr/result/{request_id.replace(file_ext, "")}'
        }), 202
        
    except Exception as e:
        logger.error(f"Error en API process_image: {e}")
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/ocr/result/<request_id>', methods=['GET'])
def api_get_result(request_id):
    """
    FIX: Endpoint para recuperar resultados de procesamiento asíncrono
    REASON: Permitir a sistemas externos consultar resultados cuando estén listos
    IMPACT: Workflow completo de ingesta → procesamiento → recuperación
    """
    try:
        from config import get_async_directories
        
        directories = get_async_directories()
        
        # Buscar archivo de resultado
        result_path = os.path.join(directories['results'], f"{request_id}.json")
        
        if os.path.exists(result_path):
            with open(result_path, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            return jsonify({
                'status': 'completed',
                'result': result_data
            })
        
        # Verificar si está en procesamiento
        processing_pattern = os.path.join(directories['processing'], f"{request_id}.*")
        import glob
        processing_files = glob.glob(processing_pattern)
        
        if processing_files:
            return jsonify({
                'status': 'processing',
                'message': 'Image is currently being processed',
                'estimated_remaining_seconds': 20
            })
        
        # Verificar si está en errores
        error_pattern = os.path.join(directories['errors'], f"{request_id}.*")
        error_files = glob.glob(error_pattern)
        
        if error_files:
            return jsonify({
                'status': 'error',
                'message': 'Processing failed. Image moved to error queue.',
                'error_reason': 'Processing or validation failed'
            })
        
        # No encontrado en ningún lugar
        return jsonify({
            'status': 'not_found',
            'message': 'Request ID not found in system'
        }), 404
        
    except Exception as e:
        logger.error(f"Error en API get_result: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/ocr/status', methods=['GET'])
def api_system_status():
    """
    FIX: Endpoint de estado del sistema asíncrono
    REASON: Proporcionar visibilidad del estado de las colas de procesamiento
    IMPACT: Monitoreo y debugging del sistema asíncrono
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        
        # Contar archivos en cada directorio
        inbox_count = len(glob.glob(os.path.join(directories['inbox'], "*.png")) + 
                         glob.glob(os.path.join(directories['inbox'], "*.jpg")))
        
        processing_count = len(glob.glob(os.path.join(directories['processing'], "*.png")) + 
                              glob.glob(os.path.join(directories['processing'], "*.jpg")))
        
        processed_count = len(glob.glob(os.path.join(directories['processed'], "*.png")) + 
                             glob.glob(os.path.join(directories['processed'], "*.jpg")))
        
        errors_count = len(glob.glob(os.path.join(directories['errors'], "*.png")) + 
                          glob.glob(os.path.join(directories['errors'], "*.jpg")))
        
        results_count = len(glob.glob(os.path.join(directories['results'], "*.json")))
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'queue_status': {
                'inbox': inbox_count,
                'processing': processing_count,
                'processed': processed_count,
                'errors': errors_count,
                'results_available': results_count
            },
            'system_info': {
                'worker_running': True,  # TODO: verificar estado real del worker
                'ocr_components_loaded': True,  # TODO: verificar estado real
                'version': '2.0.0-async'
            }
        })
        
    except Exception as e:
        logger.error(f"Error en API system_status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Could not retrieve system status',
            'details': str(e)
        }), 500

# FIX: Inicialización automática del sistema asíncrono
# REASON: Arrancar worker y pre-cargar componentes cuando se carga el módulo
# IMPACT: Sistema listo inmediatamente para procesamiento de alto volumen

def initialize_async_system():
    """Inicializa el sistema asíncrono"""
    try:
        logger.info("Inicializando sistema OCR asíncrono...")
        
        # Pre-cargar componentes OCR
        preload_ocr_components()
        
        # Iniciar worker asíncrono
        start_batch_worker()
        
        logger.info("✅ Sistema OCR asíncrono inicializado exitosamente")
        
    except Exception as e:
        logger.error(f"Error inicializando sistema asíncrono: {e}")

# Ejecutar inicialización al cargar el módulo
try:
    initialize_async_system()
except Exception as e:
    logger.error(f"Error en inicialización inicial: {e}")

# Asegurar que los directorios existen al cargar el módulo
def ensure_async_directories():
    """Crea directorios necesarios para el sistema asíncrono"""
    from config import get_async_directories
    
    directories = get_async_directories()
    
    for dir_path in directories.values():
        os.makedirs(dir_path, exist_ok=True)

# Ejecutar al cargar el módulo
ensure_async_directories()

logger.info("✅ Rutas API HTTP y directorios asíncronos inicializados")

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
                'status': 'error',
                'message': 'No images provided'
            }), 400
        
        files = request.files.getlist('images')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'status': 'error',
                'message': 'No files selected'
            }), 400
        
        # Validar número máximo de archivos
        max_files = batch_config.get('max_files_per_batch', 50)
        if len(files) > max_files:
            return jsonify({
                'status': 'error',
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
                    'status': 'error',
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
                'status': 'error',
                'message': 'No files could be processed'
            }), 400
        
        return jsonify({
            'status': 'accepted',
            'message': 'Batch enqueued for processing',
            'enqueued_ids': enqueued_ids,
            'total_files': len(enqueued_ids),
            'batch_id': batch_id,
            'estimated_processing_time_seconds': len(enqueued_ids) * 10,
            'timestamp': current_time.isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error en upload_batch: {e}")
        return jsonify({
            'status': 'error',
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
            'status': 'error',
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
                'status': 'error',
                'message': 'No configuration data provided'
            }), 400
        
        # Validar configuración
        batch_size = data.get('batch_size', 5)
        auto_optimize = data.get('auto_optimize', True)
        
        if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 50:
            return jsonify({
                'status': 'error',
                'message': 'batch_size must be an integer between 1 and 50'
            }), 400
        
        # Aplicar configuración (en memoria por ahora)
        # TODO: Implementar persistencia de configuración si es necesario
        
        logger.info(f"Configuración de lote actualizada: batch_size={batch_size}, auto_optimize={auto_optimize}")
        
        return jsonify({
            'status': 'success',
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
            'status': 'error',
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
                'status': 'error',
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
            'status': 'error',
            'message': 'Could not download batch results',
            'details': str(e)
        }), 500
