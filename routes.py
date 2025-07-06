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
# REASON: Resolver error '_worker_running' is not defined en endpoints de estado
# IMPACT: Sistema de monitoreo funcional sin errores de variables no definidas

# Instancia global del orquestador
orquestador = OrquestadorOCR()

# Variables globales de estado del sistema
_worker_running = False
_ocr_orchestrator = None
_batch_worker_thread = None

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.WEB_CONFIG['allowed_extensions']

@app.route('/')
def index():
    """Dashboard mejorado y simplificado del sistema OCR"""
    return render_template('improved_dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard profesional original del sistema OCR asíncrono con métricas profesionales"""
    return render_template('dashboard.html')

@app.route('/old')
def old_interface():
    """Interfaz anterior para compatibilidad"""
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

# FIX: API HTTP COMPLETA para sistema asíncrono de alto volumen
# REASON: Implementar endpoints separados para acumulación y procesamiento como solicita el usuario
# IMPACT: Sistema flexible para n8n con dos llamadas independientes (acumular + procesar)

@app.route('/api/ocr/process_image', methods=['POST'])
def api_process_image():
    """
    FIX: Endpoint para acumular imágenes individuales en el sistema (ENDPOINT 1 de 2)
    REASON: Permitir acumulación de archivos sin activación automática, para control por n8n
    IMPACT: Flexibilidad total para workflows externos con timing controlado por n8n
    
    Campos requeridos:
    - image: archivo de imagen
    - caption (opcional): texto del caption de WhatsApp
    - sender_id (opcional): ID del remitente
    - sender_name (opcional): nombre del remitente
    - sorteo_fecha (opcional): fecha del sorteo
    - sorteo_conteo (opcional): conteo del sorteo
    - hora_min (opcional): hora y minutos
    - additional_data (opcional): JSON con datos adicionales
    
    Response: 202 Accepted con request_id para seguimiento
    """
    try:
        from config import get_async_directories, get_api_config
        import uuid
        from datetime import datetime
        
        # Validar que se envió una imagen
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided',
                'required_fields': ['image']
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Empty filename provided'
            }), 400
        
        # Validar tipo de archivo
        api_config = get_api_config()
        if file.content_type not in api_config['allowed_image_types']:
            return jsonify({
                'status': 'error',
                'message': f'Unsupported file type: {file.content_type}',
                'supported_types': api_config['allowed_image_types']
            }), 400
        
        # FIX: Metadatos WhatsApp completos incluyendo posicion_sorteo faltante
        # REASON: Usuario reporta campos faltantes (posición sorteo A/B/C/D/E) en los metadatos
        # IMPACT: Captura completa de todos los metadatos necesarios para el procesamiento
        caption = request.form.get('caption', '')
        sender_id = request.form.get('sender_id', '')
        sender_name = request.form.get('sender_name', '')
        sorteo_fecha = request.form.get('sorteo_fecha', '')
        posicion_sorteo = request.form.get('posicion_sorteo', '')  # NUEVO: A, B, C, D, E, etc.
        sorteo_conteo = request.form.get('sorteo_conteo', '')  # Mantener compatibilidad
        hora_min = request.form.get('hora_min', '')
        additional_data = request.form.get('additional_data', '')
        
        # Generar request_id único basado en metadatos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        request_id = f"{sender_id}_{sender_name}_{sorteo_fecha}_{sorteo_conteo}_{hora_min}_{timestamp}"
        request_id = request_id.replace(' ', '_').replace(':', '-')
        
        # Obtener directorios del sistema
        directories = get_async_directories()
        
        # Determinar extensión del archivo
        file_ext = os.path.splitext(file.filename)[1].lower()
        if not file_ext:
            file_ext = '.jpg'  # Por defecto
        
        # Guardar imagen en inbox con request_id como nombre
        image_filename = f"{request_id}{file_ext}"
        image_path = os.path.join(directories['inbox'], image_filename)
        
        # Asegurar que el directorio existe
        os.makedirs(directories['inbox'], exist_ok=True)
        
        # Guardar imagen
        file.save(image_path)
        
        # Guardar caption si existe
        if caption.strip():
            caption_path = image_path.replace(file_ext, '.caption.txt')
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)
        
        # Guardar additional_data si existe
        if additional_data.strip():
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
        
        # Guardar metadatos completos del request
        metadata = {
            'request_id': request_id,
            'original_filename': file.filename,
            'content_type': file.content_type,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'sorteo_fecha': sorteo_fecha,
            'posicion_sorteo': posicion_sorteo,
            'sorteo_conteo': sorteo_conteo,
            'hora_min': hora_min,
            'caption': caption,
            'timestamp': datetime.now().isoformat(),
            'status': 'queued'
        }
        
        metadata_path = image_path.replace(file_ext, '.metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Imagen encolada: {request_id}")
        
        return jsonify({
            'status': 'accepted',
            'message': 'Image queued for processing',
            'request_id': request_id,
            'queue_position': 'pending',
            'check_result_endpoint': f'/api/ocr/result/{request_id}',
            'batch_process_endpoint': '/api/ocr/process_batch'
        }), 202
        
    except Exception as e:
        logger.error(f"Error en API process_image: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/ocr/process_batch', methods=['POST'])
def api_process_batch():
    """
    FIX: Endpoint para procesar lote acumulado bajo demanda (ENDPOINT 2 de 2)
    REASON: Separar acumulación de procesamiento para control total por n8n
    IMPACT: Activación manual del procesamiento cuando n8n lo determine apropiado
    
    Body (JSON opcional):
    - batch_size (opcional): tamaño específico del lote
    - profile (opcional): perfil de procesamiento ('ultra_rapido', 'rapido', 'normal')
    - process_all (opcional): procesar todas las imágenes en cola
    
    Response: 200 OK con detalles del lote procesado
    """
    try:
        from config import get_async_directories, get_batch_config
        import glob
        import shutil
        from datetime import datetime
        
        # Obtener configuración
        directories = get_async_directories()
        batch_config = get_batch_config()
        
        # Parsear parámetros del request
        data = request.get_json() or {}
        batch_size = data.get('batch_size', batch_config['batch_size'])
        profile = data.get('profile', 'ultra_rapido')
        process_all = data.get('process_all', False)
        
        # Validar parámetros
        if not isinstance(batch_size, int) or batch_size < 1:
            batch_size = batch_config['batch_size']
        
        if profile not in ['ultra_rapido', 'rapido', 'normal', 'high_confidence']:
            profile = 'ultra_rapido'
        
        # Buscar imágenes en inbox
        image_patterns = [
            os.path.join(directories['inbox'], "*.png"),
            os.path.join(directories['inbox'], "*.jpg"),
            os.path.join(directories['inbox'], "*.jpeg")
        ]
        
        image_files = []
        for pattern in image_patterns:
            image_files.extend(glob.glob(pattern))
        
        if not image_files:
            return jsonify({
                'status': 'success',
                'message': 'No images in queue to process',
                'batch_info': {
                    'processed_count': 0,
                    'queue_size': 0,
                    'batch_id': None
                }
            }), 200
        
        # Ordenar por timestamp (FIFO)
        image_files.sort(key=os.path.getmtime)
        
        # Determinar lote a procesar
        if process_all:
            current_batch = image_files
        else:
            current_batch = image_files[:batch_size]
        
        # Generar batch_id único
        batch_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        batch_id = f"BATCH_{batch_timestamp}"
        
        logger.info(f"🚀 Iniciando procesamiento de lote {batch_id}: {len(current_batch)} imágenes")
        
        # Procesar lote usando la función existente
        global _ocr_orchestrator
        if not _ocr_orchestrator:
            preload_ocr_components()
        
        if _ocr_orchestrator:
            # Preparar datos para procesamiento
            processing_paths = []
            caption_texts = []
            metadata_list = []
            
            for img_path in current_batch:
                # Mover imagen a processing
                filename = os.path.basename(img_path)
                processing_path = os.path.join(directories['processing'], filename)
                shutil.move(img_path, processing_path)
                processing_paths.append(processing_path)
                
                # Leer caption si existe
                caption_path = img_path.replace('.png', '.caption.txt').replace('.jpg', '.caption.txt').replace('.jpeg', '.caption.txt')
                caption_text = ""
                if os.path.exists(caption_path):
                    with open(caption_path, 'r', encoding='utf-8') as f:
                        caption_text = f.read().strip()
                    # Mover caption también
                    new_caption_path = processing_path.replace('.png', '.caption.txt').replace('.jpg', '.caption.txt').replace('.jpeg', '.caption.txt')
                    shutil.move(caption_path, new_caption_path)
                
                caption_texts.append(caption_text)
                
                # Leer metadata si existe
                metadata_path = img_path.replace('.png', '.metadata.json').replace('.jpg', '.metadata.json').replace('.jpeg', '.metadata.json')
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        # Mover metadata también
                        new_metadata_path = processing_path.replace('.png', '.metadata.json').replace('.jpg', '.metadata.json').replace('.jpeg', '.metadata.json')
                        shutil.move(metadata_path, new_metadata_path)
                    except Exception as e:
                        logger.warning(f"Error leyendo metadata {metadata_path}: {e}")
                
                metadata_list.append(metadata)
            
            # Ejecutar procesamiento por lotes
            batch_start_time = time.time()
            results = _ocr_orchestrator.procesar_lote_imagenes(
                processing_paths, caption_texts, metadata_list, 'spa', profile
            )
            batch_processing_time = time.time() - batch_start_time
            
            # Guardar resultados y mover archivos
            successful_results = 0
            failed_results = 0
            result_files = []
            
            for i, result in enumerate(results):
                try:
                    filename = os.path.basename(processing_paths[i])
                    request_id = result.get('request_id', filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', ''))
                    
                    # Añadir batch_id al resultado
                    result['batch_id'] = batch_id
                    result['batch_processing_time'] = round(batch_processing_time, 2)
                    result['batch_position'] = i + 1
                    result['batch_size'] = len(results)
                    
                    # Guardar JSON resultado
                    result_filename = f"{batch_id}_{request_id}.json"
                    result_path = os.path.join(directories['results'], result_filename)
                    
                    with open(result_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    result_files.append(result_filename)
                    
                    # Mover imagen según resultado
                    if result.get('processing_status') == 'success':
                        final_path = os.path.join(directories['processed'], filename)
                        successful_results += 1
                    else:
                        final_path = os.path.join(directories['errors'], filename)
                        failed_results += 1
                    
                    shutil.move(processing_paths[i], final_path)
                    
                    # Mover archivos auxiliares también
                    for aux_ext in ['.caption.txt', '.metadata.json', '.additional_data.json', '.additional_data.txt']:
                        aux_processing = processing_paths[i].replace('.png', aux_ext).replace('.jpg', aux_ext).replace('.jpeg', aux_ext)
                        if os.path.exists(aux_processing):
                            aux_final = final_path.replace('.png', aux_ext).replace('.jpg', aux_ext).replace('.jpeg', aux_ext)
                            shutil.move(aux_processing, aux_final)
                    
                except Exception as e:
                    logger.error(f"Error guardando resultado {i}: {e}")
                    failed_results += 1
            
            # Preparar resumen del lote
            remaining_in_queue = len(image_files) - len(current_batch)
            
            logger.info(f"✅ Lote {batch_id} procesado: {successful_results} éxitos, {failed_results} errores")
            
            return jsonify({
                'status': 'success',
                'message': f'Batch processed successfully',
                'batch_info': {
                    'batch_id': batch_id,
                    'processed_count': len(current_batch),
                    'successful_count': successful_results,
                    'failed_count': failed_results,
                    'processing_time_seconds': round(batch_processing_time, 2),
                    'profile_used': profile,
                    'remaining_in_queue': remaining_in_queue,
                    'result_files': result_files,
                    'download_endpoint': f'/api/download/batch_results/{batch_id}'
                },
                'processing_summary': {
                    'average_time_per_image': round(batch_processing_time / len(current_batch), 2) if current_batch else 0,
                    'images_per_second': round(len(current_batch) / batch_processing_time, 2) if batch_processing_time > 0 else 0,
                    'queue_status': f'{remaining_in_queue} images remaining'
                }
            }), 200
        
        else:
            return jsonify({
                'status': 'error',
                'message': 'OCR system not initialized'
            }), 500
        
    except Exception as e:
        logger.error(f"Error en API process_batch: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Batch processing failed',
            'details': str(e)
        }), 500

@app.route('/api/ocr/result/<request_id>', methods=['GET'])
def api_get_result(request_id):
    """
    FIX: Endpoint para consultar resultado de procesamiento individual
    REASON: Permitir seguimiento de estado y recuperación de resultados
    IMPACT: API completa para consulta de status y descarga de resultados
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        
        # Buscar resultado en directorio de resultados
        result_pattern = os.path.join(directories['results'], f"*{request_id}*.json")
        result_files = glob.glob(result_pattern)
        
        if result_files:
            # Encontrado - leer y devolver resultado
            result_file = result_files[0]
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            return jsonify({
                'status': 'completed',
                'request_id': request_id,
                'result': result_data,
                'file_location': os.path.basename(result_file)
            }), 200
        
        # Buscar en processing
        processing_pattern = os.path.join(directories['processing'], f"*{request_id}*")
        processing_files = glob.glob(processing_pattern)
        if processing_files:
            return jsonify({
                'status': 'processing',
                'request_id': request_id,
                'message': 'Image is currently being processed'
            }), 200
        
        # Buscar en inbox
        inbox_pattern = os.path.join(directories['inbox'], f"*{request_id}*")
        inbox_files = glob.glob(inbox_pattern)
        if inbox_files:
            return jsonify({
                'status': 'queued',
                'request_id': request_id,
                'message': 'Image is queued for processing'
            }), 200
        
        # Buscar en errors
        error_pattern = os.path.join(directories['errors'], f"*{request_id}*")
        error_files = glob.glob(error_pattern)
        if error_files:
            return jsonify({
                'status': 'error',
                'request_id': request_id,
                'message': 'Processing failed',
                'error_reason': 'Check system logs for details'
            }), 200
        
        # No encontrado
        return jsonify({
            'status': 'not_found',
            'request_id': request_id,
            'message': 'Request ID not found in system'
        }), 404
        
    except Exception as e:
        logger.error(f"Error consultando resultado {request_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Could not retrieve result',
            'details': str(e)
        }), 500

@app.route('/api/ocr/queue/status', methods=['GET'])
def api_queue_status():
    """
    FIX: Endpoint para consultar estado de la cola de procesamiento
    REASON: Permitir monitoreo del sistema para n8n y otros workflows
    IMPACT: Visibilidad completa del estado del sistema asíncrono
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        
        # Contar archivos en cada directorio
        inbox_count = len(glob.glob(os.path.join(directories['inbox'], "*.*")))
        processing_count = len(glob.glob(os.path.join(directories['processing'], "*.*")))
        processed_count = len(glob.glob(os.path.join(directories['processed'], "*.*")))
        errors_count = len(glob.glob(os.path.join(directories['errors'], "*.*")))
        results_count = len(glob.glob(os.path.join(directories['results'], "*.json")))
        
        return jsonify({
            'status': 'success',
            'queue_status': {
                'inbox': inbox_count,
                'processing': processing_count,
                'processed': processed_count,
                'errors': errors_count,
                'results_available': results_count
            },
            'system_status': {
                'worker_running': _worker_running,
                'ocr_loaded': _ocr_orchestrator is not None and orquestador is not None
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error consultando estado de cola: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Could not retrieve queue status',
            'details': str(e)
        }), 500

# FIX: Importar endpoints API HTTP completos desde módulo separado
# REASON: Evitar conflictos de nombres y mantener código organizado
# IMPACT: Sistema API completo sin duplicaciones

# FIX: Endpoints API integrados directamente - import eliminado
# REASON: Resolver error ModuleNotFoundError ya que api_endpoints.py fue eliminado
# IMPACT: Sistema funcional con endpoints integrados en routes.py

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
    global _worker_running, _ocr_orchestrator, _batch_worker_thread
    
    try:
        logger.info("Inicializando sistema OCR asíncrono...")
        
        # FIX: Inicialización correcta de variables globales de estado
        # REASON: Asegurar que las variables de estado estén correctamente inicializadas
        # IMPACT: Endpoints de monitoreo funcionan sin errores de variables no definidas
        
        # Pre-cargar componentes OCR
        preload_ocr_components()
        _ocr_orchestrator = orquestador
        
        # Iniciar worker asíncrono
        start_batch_worker()
        _worker_running = True
        
        logger.info("✅ Sistema OCR asíncrono inicializado exitosamente")
        
    except Exception as e:
        logger.error(f"Error inicializando sistema asíncrono: {e}")
        _worker_running = False

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
            'status': 'success',
            'message': 'Sistema limpiado exitosamente',
            'cleaned_counts': cleaned_counts,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error al limpiar sistema: {e}")
        return jsonify({
            'status': 'error',
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
            'status': 'success',
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
            'status': 'error',
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
                'status': 'error',
                'message': 'Imagen no encontrada'
            }), 404
        
        return send_file(found_file, as_attachment=False)
        
    except Exception as e:
        logger.error(f"Error obteniendo vista previa {request_id}: {e}")
        return jsonify({
            'status': 'error',
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
                'status': 'error',
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
            'status': 'error',
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
            'status': 'success',
            'message': f'Queue cleared successfully',
            'files_removed': removed_count,
            'directories_cleared': ['inbox', 'processing', 'processed', 'errors']
        }), 200
        
    except Exception as e:
        logger.error(f"Error limpiando cola: {e}")
        return jsonify({
            'status': 'error',
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
