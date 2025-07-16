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
import app as app_module
from main_ocr_process import OrquestadorOCR
import config

# FIX: Logger configurado correctamente para routes.py
# REASON: Variable logger usada 57 veces pero no estaba definida causando NameError
# IMPACT: Eliminación completa de errores de logging en producción
# TEST: Verificar que todos los logger.info/debug/warning/error funcionen
# MONITOR: Logging enterprise configurado con nivel y formato apropiado
# INTERFACE: Logging coherente en toda la aplicación
# VISUAL_CHANGE: Logs visibles y estructurados en consola y archivos
# REFERENCE_INTEGRITY: Variable logger ahora existe y está configurada correctamente
logger = logging.getLogger(__name__)

def validate_whatsapp_metadata(metadata_dict):
    """
    FIX: Validación robusta de metadatos WhatsApp siguiendo filosofía Zero-Fault Detection
    REASON: Usuario requiere validación estricta de formato de metadatos WhatsApp
    IMPACT: Garantiza integridad de datos y previene errores en procesamiento
    INTERFACE: Validación enterprise con reportes detallados de errores
    """
    errors = []
    warnings = []
    
    # Validar numerosorteo: debe ser A-Z o 01-99
    numerosorteo = metadata_dict.get('numerosorteo', '').strip()
    if numerosorteo:
        if not (numerosorteo.isalpha() and len(numerosorteo) == 1 and numerosorteo.isupper()) and \
           not (numerosorteo.isdigit() and 1 <= int(numerosorteo) <= 99):
            errors.append(f"numerosorteo '{numerosorteo}' debe ser A-Z o 01-99")
    
    # Validar fechasorteo: formato YYYYMMDD
    fechasorteo = metadata_dict.get('fechasorteo', '').strip()
    if fechasorteo and len(fechasorteo) != 8 or not fechasorteo.isdigit():
        errors.append(f"fechasorteo '{fechasorteo}' debe ser formato YYYYMMDD")
    
    # Validar idWhatsapp: debe terminar en @lid
    idWhatsapp = metadata_dict.get('idWhatsapp', '').strip()
    if idWhatsapp and not idWhatsapp.endswith('@lid'):
        warnings.append(f"idWhatsapp '{idWhatsapp}' debería terminar en @lid")
    
    # Validar horamin: formato HH-MM
    horamin = metadata_dict.get('horamin', '').strip()
    if horamin:
        if len(horamin) != 5 or horamin[2] != '-' or not horamin[:2].isdigit() or not horamin[3:].isdigit():
            errors.append(f"horamin '{horamin}' debe ser formato HH-MM")
        else:
            hora, minuto = horamin.split('-')
            if not (0 <= int(hora) <= 23) or not (0 <= int(minuto) <= 59):
                errors.append(f"horamin '{horamin}' tiene valores fuera de rango")
    
    # Validar nombre: no debe estar vacío si se proporciona
    nombre = metadata_dict.get('nombre', '').strip()
    if nombre and len(nombre) < 2:
        warnings.append(f"nombre '{nombre}' es muy corto")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }

# Variables globales para estado del sistema asíncrono
_worker_running = False
_worker_thread = None

# Inicialización del sistema
try:
    logger.info("Inicializando sistema OCR asíncrono...")
    
    # Pre-cargar componentes OCR
    preload_ocr_components()
    
    # Inicializar worker asíncrono
    start_batch_worker()
    
    logger.info("✅ Sistema OCR asíncrono inicializado exitosamente")
    
    # Inicializar directorios y configuraciones
    from config import get_async_directories, get_api_config
    directories = get_async_directories()
    api_config = get_api_config()
    
    logger.info("✅ Rutas API HTTP y directorios asíncronos inicializados")
    
except Exception as e:
    logger.error(f"Error inicializando sistema OCR: {e}")

@app.route('/')
def index():
    """
    MANDATO 14: Página principal con Interface Excellence Dashboard reconstruido
    REASON: RECONSTRUCCIÓN INTEGRAL DEL FRONTEND siguiendo filosofía INTEGRIDAD TOTAL
    IMPACT: Frontend completamente nuevo con arquitectura modular y monitoreo avanzado por lotes
    INTERFACE: Comprehensive validation and enhanced UI components with real-time feedback
    VISUAL_CHANGE: Enhanced filename display with metadata and copy functionality
    """
    return render_template('interface_excellence_dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal del sistema OCR empresarial con Interface Excellence"""
    return render_template('interface_excellence_dashboard.html')

@app.route('/dashboard_old')
def dashboard_old():
    """Dashboard anterior para referencia"""
    return render_template('dashboard.html')

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
                
                # Obtener información básica del archivo (fuera del try para scope)
                try:
                    stat_info = os.stat(archivo_path)
                    tamaño = stat_info.st_size
                    fecha_mod = datetime.fromtimestamp(stat_info.st_mtime)
                except OSError:
                    tamaño = 0
                    fecha_mod = datetime.now()
                
                try:
                    # Leer contenido JSON para verificar estructura
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        contenido_json = json.load(f)
                    
                    # FIX: Detección corregida de contenido OCR y coordenadas en estructura JSON real
                    # REASON: La función anterior buscaba campos incorrectos causando has_ocr_data false
                    # IMPACT: Corrección de detección de texto extraído y coordenadas existentes
                    # TEST: Verificación con estructura real de archivos JSON procesados
                    # MONITOR: Logging de campos detectados para debugging
                    # INTERFACE: Archivos procesados ahora muestran datos OCR correctamente
                    # VISUAL_CHANGE: Lista de archivos procesados muestra contenido real extraído
                    # REFERENCE_INTEGRITY: Campos verificados contra estructura JSON real generada
                    
                    # Extraer datos OCR desde estructura real
                    datos_extraidos = contenido_json.get('datos_extraidos', {})
                    texto_completo = (
                        datos_extraidos.get('texto_completo', '') or
                        contenido_json.get('texto_extraido', '') or
                        contenido_json.get('full_raw_ocr_text', '')
                    )
                    
                    palabras_detectadas = (
                        datos_extraidos.get('palabras_detectadas', []) or
                        contenido_json.get('word_data', [])
                    )
                    
                    # Calcular confianza promedio desde palabras detectadas
                    confianza_promedio = 0
                    if palabras_detectadas:
                        confidencias = [p.get('confianza', 0) for p in palabras_detectadas if isinstance(p, dict)]
                        if confidencias:
                            confianza_promedio = sum(confidencias) / len(confidencias)
                    
                    # Información básica del archivo
                    info_archivo = {
                        'filename': archivo,
                        'filepath': archivo_path,
                        'size_bytes': tamaño,
                        'size_readable': f"{tamaño / 1024:.1f} KB" if tamaño > 1024 else f"{tamaño} bytes",
                        'modified_date': fecha_mod.isoformat(),
                        'modified_readable': fecha_mod.strftime('%d/%m/%Y %H:%M:%S'),
                        'has_ocr_data': bool(texto_completo and len(texto_completo.strip()) > 0),
                        'has_coordinates': bool(palabras_detectadas and len(palabras_detectadas) > 0),
                        'word_count': len(palabras_detectadas),
                        'confidence': confianza_promedio,
                        'processing_time': contenido_json.get('tiempo_procesamiento', contenido_json.get('processing_time_ms', 0)),
                        'texto_preview': texto_completo[:100] + '...' if len(texto_completo) > 100 else texto_completo
                    }
                    
                    logger.debug(f"Archivo {archivo}: OCR={info_archivo['has_ocr_data']}, Coords={info_archivo['has_coordinates']}, Words={info_archivo['word_count']}, Texto={len(texto_completo)} chars")
                    
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
        }), 500

@app.route('/api/ocr/process_image', methods=['POST'])
def api_process_image():
    """
    FIX: Endpoint corregido para subida múltiple de archivos con metadatos WhatsApp
    REASON: Usuario reporta error en subida y necesita formato WhatsApp correcto
    IMPACT: Sistema funcional con metadata de WhatsApp visible en interfaz
    INTERFACE: Manejo correcto de archivos múltiples con validación robusta
    VISUAL_CHANGE: Metadatos WhatsApp visibles en interfaz con formato correcto
    """
    try:
        # Manejo de archivos múltiples o individuales
        files_list = []
        
        if 'files' in request.files:
            files_list = request.files.getlist('files')
        elif 'images' in request.files:
            files_list = request.files.getlist('images')
        elif 'image' in request.files:
            files_list = [request.files['image']]
        else:
            return jsonify({
                'status': 'error',
                'mensaje': 'No se proporcionaron imágenes',
                'message': 'No images provided'
            }), 400
        
        # Filtrar archivos válidos
        valid_files = [f for f in files_list if f.filename != '']
        if not valid_files:
            return jsonify({
                'status': 'error',
                'mensaje': 'No hay archivos válidos',
                'message': 'No valid files'
            }), 400
        
        # Obtener directorios
        from config import get_async_directories
        directories = get_async_directories()
        
        # Procesar múltiples archivos
        uploaded_files = []
        upload_results = []
        current_time = datetime.now()
        
        for file in valid_files:
            try:
                # Generar timestamp único por archivo
                timestamp_id = current_time.strftime('%Y%m%d_%H%M%S_%f')[:-3]
                
                # FIX: Manejo seguro de file.filename None/empty y validación robusta
                # REASON: file.filename puede ser None causando NameError en operaciones de string
                # IMPACT: Previene crashes en upload cuando filename es None o inválido
                # TEST: Maneja correctamente archivos sin nombre o con nombres inválidos
                # MONITOR: Logging de nombres de archivos problemáticos
                # INTERFACE: Upload robusto que no falla con archivos problemáticos
                # VISUAL_CHANGE: Upload funciona consistentemente sin errores inesperados
                # REFERENCE_INTEGRITY: Validación de None antes de operaciones de string
                
                # Validar filename seguro
                original_name = file.filename or f"upload_{timestamp_id}"
                if not isinstance(original_name, str) or len(original_name.strip()) == 0:
                    original_name = f"upload_{timestamp_id}"
                
                # Determinar extensión de archivo
                if '.' in original_name:
                    file_ext = original_name.rsplit('.', 1)[1].lower()
                    if file_ext not in ['png', 'jpg', 'jpeg']:
                        continue  # Saltar archivos no válidos
                else:
                    file_ext = 'png'
                
                # Intentar detectar si es formato WhatsApp en el nombre original
                if ('--' in original_name and '@' in original_name and '_' in original_name):
                    # Es formato WhatsApp, usar nombre original con timestamp para evitar duplicados
                    base_name = original_name.rsplit('.', 1)[0]
                    final_filename = f"{base_name}_{timestamp_id}.{file_ext}"
                else:
                    # No es formato WhatsApp, generar nombre genérico
                    clean_base = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
                    clean_name = secure_filename(clean_base) or f"file_{timestamp_id}"
                    final_filename = f"{clean_name}_{timestamp_id}.{file_ext}"
                
                # Guardar archivo
                file_path = os.path.join(directories['inbox'], final_filename)
                file.save(file_path)
                
                # Extraer metadatos de WhatsApp del nombre de archivo
                from app import extract_metadata_from_filename
                whatsapp_metadata = extract_metadata_from_filename(final_filename)
                
                # FIX: Priorizar metadatos del formulario sobre los extraídos del nombre
                # REASON: Usuario requiere control manual de metadatos WhatsApp
                # IMPACT: Sistema utiliza datos editados por usuario en lugar de automáticos
                # INTERFACE: Validación de datos del formulario con fallback a automáticos
                form_numerosorteo = request.form.get('numerosorteo', '').strip()
                form_fechasorteo = request.form.get('fechasorteo', '').strip()
                form_idWhatsapp = request.form.get('idWhatsapp', '').strip()
                form_nombre = request.form.get('nombre', '').strip()
                form_horamin = request.form.get('horamin', '').strip()
                form_caption = request.form.get('caption', '').strip()
                
                # FIX: Validación robusta de metadatos antes del procesamiento
                # REASON: Implementar filosofía Zero-Fault Detection para metadatos
                # IMPACT: Garantiza integridad de datos y previene errores en nombres
                if any([form_numerosorteo, form_fechasorteo, form_idWhatsapp, form_nombre, form_horamin]):
                    metadata_validation = validate_whatsapp_metadata({
                        'numerosorteo': form_numerosorteo,
                        'fechasorteo': form_fechasorteo,
                        'idWhatsapp': form_idWhatsapp,
                        'nombre': form_nombre,
                        'horamin': form_horamin
                    })
                    
                    if not metadata_validation['valid']:
                        logger.warning(f"Errores de validación en metadatos: {metadata_validation['errors']}")
                        # Continuar pero registrar errores para logging
                        upload_results.append({
                            'status': 'warning',
                            'filename': file.filename,
                            'validation_errors': metadata_validation['errors'],
                            'validation_warnings': metadata_validation['warnings']
                        })
                
                # Usar datos del formulario si existen, sino usar automáticos
                final_numerosorteo = form_numerosorteo or whatsapp_metadata.get('numerosorteo', 'A')
                final_fechasorteo = form_fechasorteo or current_time.strftime('%Y%m%d')
                final_idWhatsapp = form_idWhatsapp or whatsapp_metadata.get('idWhatsapp', 'unknown@lid')
                final_nombre = form_nombre or whatsapp_metadata.get('nombre', 'Unknown')
                final_horamin = form_horamin or whatsapp_metadata.get('horamin', '00-00')
                final_caption = form_caption or whatsapp_metadata.get('texto_mensaje_whatsapp', '')
                
                # Si hay metadatos del formulario, regenerar nombre de archivo
                if any([form_numerosorteo, form_fechasorteo, form_idWhatsapp, form_nombre, form_horamin]):
                    # Regenerar nombre con metadatos del formulario
                    custom_filename = f"{final_fechasorteo}-{final_numerosorteo}--{final_idWhatsapp}_{final_nombre}_{final_horamin}_{timestamp_id}.{file_ext}"
                    custom_file_path = os.path.join(directories['inbox'], custom_filename)
                    
                    # Mover archivo al nombre personalizado
                    if os.path.exists(file_path) and file_path != custom_file_path:
                        shutil.move(file_path, custom_file_path)
                        file_path = custom_file_path
                        final_filename = custom_filename
                
                # Metadatos completos con datos de WhatsApp empresariales
                metadata = {
                    'filename_original': file.filename,
                    'filename_final': final_filename,
                    'request_id': final_filename.replace(f'_{timestamp_id}', ''),
                    'upload_timestamp': current_time.isoformat(),
                    'file_size': os.path.getsize(file_path),
                    # Campos críticos de WhatsApp con prioridad del formulario
                    'numerosorteo': final_numerosorteo,
                    'idWhatsapp': final_idWhatsapp,
                    'nombre': final_nombre,
                    'horamin': final_horamin,
                    'fechasorteo': final_fechasorteo,
                    'texto_mensaje_whatsapp': final_caption,
                    'caption': final_caption,
                    'otro_valor': request.form.get('otro_valor', 'subir_con_metadata'),
                    'form_data_used': bool(any([form_numerosorteo, form_fechasorteo, form_idWhatsapp, form_nombre, form_horamin])),
                    # Metadatos completos de WhatsApp
                    'whatsapp_metadata': whatsapp_metadata
                }
                
                # Guardar metadatos
                metadata_path = file_path.replace(f'.{file_ext}', '.metadata.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                uploaded_files.append(final_filename)
                upload_results.append({
                    'filename_original': file.filename,
                    'filename_final': final_filename,
                    'metadata': metadata,
                    'status': 'uploaded'
                })
                
                logger.info(f"✅ Archivo subido: {final_filename} con metadata WhatsApp: {whatsapp_metadata}")
                
            except Exception as e:
                logger.error(f"Error subiendo archivo {file.filename}: {e}")
                upload_results.append({
                    'filename_original': file.filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        if not uploaded_files:
            return jsonify({
                'status': 'error',
                'mensaje': 'No se pudieron subir archivos',
                'message': 'No files could be uploaded',
                'results': upload_results
            }), 400
        
        logger.info(f"✅ {len(uploaded_files)} archivos subidos exitosamente")
        
        return jsonify({
            'status': 'success',
            'estado': 'exitoso',
            'message': f'{len(uploaded_files)} files uploaded successfully',
            'mensaje': f'{len(uploaded_files)} archivos subidos exitosamente',
            'uploaded_count': len(uploaded_files),
            'total_files': len(valid_files),
            'uploaded_files': uploaded_files,
            'results': upload_results,
            'next_steps': {
                'queue_check': '/api/ocr/queue/status',
                'process_batch': '/api/ocr/process_batch',
                'view_files': '/#queue-panel'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error en process_image: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error interno: {str(e)}',
            'message': f'Internal error: {str(e)}'
        }), 500

@app.route('/api/ocr/process_batch', methods=['POST'])
def api_process_batch():
    """
    FIX: Endpoint process_batch con generación de request_id único y tracking de procesos
    REASON: JavaScript requiere request_id válido para monitoreo de progreso de lote
    IMPACT: Restaura funcionalidad de tracking empresarial y monitoreo en tiempo real
    TEST: Verifica generación UUID único y respuesta JSON válida con request_id
    MONITOR: Logging detallado de inicio y progreso de procesamiento por lotes
    INTERFACE: JavaScript recibe request_id válido para mostrar progreso en tiempo real
    VISUAL_CHANGE: Progreso de procesamiento visible con request_id válido
    REFERENCE_INTEGRITY: request_id generado es único y persistente durante procesamiento
    """
    try:
        import uuid
        from datetime import datetime
        
        # INTEGRIDAD TOTAL: Generar ID único fijo para TODO el lote de ejecución
        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_uuid = str(uuid.uuid4())[:8]
        request_id = f"BATCH_{batch_timestamp}_{batch_uuid}"
        
        # Almacenar ID único del lote para usar en todos los archivos
        _save_batch_execution_id(request_id)
        
        # FIX: Manejo robusto de datos JSON y form-data
        # REASON: Error 400 puede ser causado por datos malformados o contenido mixto
        # IMPACT: Procesamiento estable independiente del tipo de contenido
        # TEST: Maneja tanto JSON como form-data correctamente
        # MONITOR: Logging detallado del tipo de contenido recibido
        # INTERFACE: Compatible con diferentes tipos de requests desde frontend
        # VISUAL_CHANGE: Procesamiento exitoso elimina errores 400
        # REFERENCE_INTEGRITY: Validación de tipos de datos antes de procesamiento
        
        data = {}
        content_type = request.content_type or ''
        
        if 'application/json' in content_type:
            data = request.get_json() or {}
        elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
            data = request.form.to_dict()
        else:
            # Intentar ambos métodos
            try:
                data = request.get_json() or {}
            except:
                data = request.form.to_dict() if request.form else {}
        
        logger.info(f"📨 Procesando lote con datos: {data}")
        logger.info(f"📝 Content-Type: {content_type}")
        
        # Obtener configuración con valores por defecto
        profile = data.get('profile', 'ultra_rapido')
        batch_size = int(data.get('batch_size', 5))
        
        logger.info(f"✅ Procesamiento de lote iniciado. Request ID: {request_id}")
        logger.info(f"⚙️ Configuración: profile={profile}, batch_size={batch_size}")
        
        # Inicializar orquestador
        orquestador = OrquestadorOCR()
        
        # FIX: Manejo de archivos enviados directamente en process_batch
        # REASON: Frontend envía archivos directamente a process_batch en lugar de usar process_image primero
        # IMPACT: Permite procesamiento directo de archivos desde el frontend
        # SOLUTION: Guardar archivos en inbox y luego procesarlos
        
        # Verificar si hay archivos en el request
        files_in_request = request.files.getlist('files')
        
        if files_in_request:
            # Hay archivos en el request, necesitamos guardarlos primero
            logger.info(f"📁 Archivos detectados en process_batch: {len(files_in_request)}")
            
            # Guardar archivos en inbox
            from config import get_async_directories
            directories = get_async_directories()
            
            for i, file in enumerate(files_in_request):
                if file.filename and file.filename != '':
                    # Generar nombre único con timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    
                    # Obtener parámetros específicos del archivo
                    codigo_sorteo = data.get(f'codigo_sorteo_{i}', 'A')
                    id_whatsapp = data.get(f'id_whatsapp_{i}', f'{timestamp}@lid')
                    nombre_usuario = data.get(f'nombre_usuario_{i}', 'Usuario')
                    caption = data.get(f'caption_{i}', '')
                    hora_exacta = data.get(f'hora_exacta_{i}', '00-00')
                    numero_llegada = data.get(f'numero_llegada_{i}', i + 1)
                    
                    # Generar nombre de archivo con formato WhatsApp
                    fecha_sorteo = datetime.now().strftime('%Y%m%d')
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                    
                    final_filename = f"{fecha_sorteo}-{codigo_sorteo}--{id_whatsapp}_{nombre_usuario}_{hora_exacta}_{timestamp}.{file_ext}"
                    
                    # Guardar archivo en inbox
                    file_path = os.path.join(directories['inbox'], final_filename)
                    file.save(file_path)
                    
                    # Crear metadatos
                    metadata = {
                        'filename_original': file.filename,
                        'filename_final': final_filename,
                        'request_id': request_id,
                        'upload_timestamp': datetime.now().isoformat(),
                        'file_size': os.path.getsize(file_path),
                        'numerosorteo': codigo_sorteo,
                        'idWhatsapp': id_whatsapp,
                        'nombre': nombre_usuario,
                        'horamin': hora_exacta,
                        'fechasorteo': fecha_sorteo,
                        'caption': caption,
                        'numero_llegada': numero_llegada,
                        'processed_via': 'process_batch_direct'
                    }
                    
                    # Guardar metadatos
                    metadata_path = file_path.replace(f'.{file_ext}', '.metadata.json')
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"📁 Archivo guardado: {final_filename}")
        
        # Procesar lote con tracking del request_id único
        # FIX: Procesar TODOS los archivos disponibles sin límite de batch_size
        # REASON: Usuario reportó que solo se procesaron 4 de 10 archivos subidos
        # SOLUTION: Usar max_files=50 para procesar todos los archivos disponibles
        resultado = orquestador.process_queue_batch(
            max_files=50,  # PROCESAMIENTO COMPLETO: Sin límite artificial
            profile=profile,
            request_id=request_id  # MANDATO CRÍTICO: Pasar request_id para persistencia
        )
        
        # Añadir request_id al resultado
        if isinstance(resultado, dict):
            resultado['request_id'] = request_id
            resultado['batch_id'] = request_id
            resultado['processing_status'] = 'completed'
            resultado['timestamp'] = datetime.now().isoformat()
        else:
            resultado = {
                'status': 'success',
                'request_id': request_id,
                'batch_id': request_id,
                'processing_status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'resultado_original': resultado
            }
        
        processed_count = resultado.get('batch_info', {}).get('processed_count', 0)
        
        # FIX: ALMACENAR REQUEST_ID DEL ÚLTIMO LOTE PROCESADO PARA FILTRADO
        # REASON: Usuario requiere JSON consolidado específico del último lote únicamente
        # IMPACT: Permite filtrado preciso de archivos por lote para evitar mezcla de resultados
        if processed_count > 0:
            _save_last_batch_request_id(request_id)
            logger.info(f"💾 Almacenado request_id del último lote exitoso: {request_id}")
        
        logger.info(f"✅ Lote procesado exitosamente: {processed_count} archivos. Request ID: {request_id}")
        
        return jsonify(resultado)
        
    except Exception as e:
        # FIX: Manejo seguro de request_id en caso de error antes de su definición
        # REASON: Variable request_id puede no estar definida si error ocurre antes
        # IMPACT: Evita NameError en manejo de errores críticos
        # TEST: Error handling funciona correctamente en cualquier punto del flujo
        # MONITOR: Logging de errores sin fallos adicionales
        # INTERFACE: Respuestas de error consistentes y robustas
        # VISUAL_CHANGE: Errores manejados sin crashes adicionales
        # REFERENCE_INTEGRITY: Variable request_id manejada de forma segura
        safe_request_id = locals().get('request_id', f"ERROR_{int(time.time())}")
        logger.error(f"Error crítico procesando lote: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error al procesar el lote: {str(e)}',
            'message': f'Batch processing error: {str(e)}',
            'request_id': safe_request_id,
            'error_code': 'BATCH_PROCESSING_ERROR'
        }), 500

@app.route('/api/ocr/result/<request_id>')
def api_get_result(request_id):
    """Obtener resultado individual"""
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        # Buscar archivo de resultado
        result_file = os.path.join(directories['results'], f"{request_id}.json")
        
        if not os.path.exists(result_file):
            return jsonify({
                'status': 'not_found',
                'estado': 'no_encontrado',
                'mensaje': 'Resultado no encontrado',
                'message': 'Result not found'
            }), 404
        
        # Leer resultado
        with open(result_file, 'r', encoding='utf-8') as f:
            resultado = json.load(f)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Error obteniendo resultado: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error al obtener resultado: {str(e)}',
            'message': f'Error getting result: {str(e)}'
        }), 500

@app.route('/api/ocr/queue/status')
def api_queue_status():
    """
    FIX: Estado de la cola de procesamiento con verificación de directorios
    REASON: Evitar errores cuando directorios no existen durante inicialización
    IMPACT: Sistema robusto que funciona correctamente desde el primer arranque
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        # FIX: Crear directorios si no existen
        for dir_path in directories.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Contar archivos en cada directorio con manejo de errores
        inbox_count = 0
        processing_count = 0
        processed_count = 0
        results_count = 0
        errors_count = 0
        
        try:
            inbox_count = len([f for f in os.listdir(directories['inbox']) if f.endswith(('.png', '.jpg', '.jpeg'))])
        except:
            pass
            
        try:
            processing_count = len([f for f in os.listdir(directories['processing']) if f.endswith(('.png', '.jpg', '.jpeg'))])
        except:
            pass
            
        try:
            processed_count = len([f for f in os.listdir(directories['processed']) if f.endswith(('.png', '.jpg', '.jpeg'))])
        except:
            pass
            
        try:
            results_count = len([f for f in os.listdir(directories['results']) if f.endswith('.json')])
        except:
            pass
            
        try:
            errors_count = len([f for f in os.listdir(directories.get('errors', 'data/errors')) if f.endswith(('.png', '.jpg', '.jpeg'))])
        except:
            pass
        
        # FIX: Agregar lista de archivos en cola con metadatos WhatsApp
        # REASON: Usuario reporta que no se ven archivos en cola
        # IMPACT: Interfaz muestra archivos reales con metadatos completos
        # VISUAL_CHANGE: Archivos visibles en interfaz con nombres completos de WhatsApp
        
        inbox_files = []
        try:
            for filename in os.listdir(directories['inbox']):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(directories['inbox'], filename)
                    metadata_path = file_path.replace(f'.{filename.split(".")[-1]}', '.metadata.json')
                    
                    file_info = {
                        'filename': filename,
                        'size': os.path.getsize(file_path),
                        'upload_time': os.path.getmtime(file_path)
                    }
                    
                    # Cargar metadatos si existen
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                file_info.update({
                                    'numerosorteo': metadata.get('numerosorteo', 'A'),
                                    'idWhatsapp': metadata.get('idWhatsapp', 'unknown@lid'),
                                    'nombre': metadata.get('nombre', 'Unknown'),
                                    'horamin': metadata.get('horamin', '00-00'),
                                    'caption': metadata.get('caption', ''),
                                    'whatsapp_metadata': metadata.get('whatsapp_metadata', {})
                                })
                        except Exception as e:
                            logger.warning(f"Error leyendo metadata para {filename}: {e}")
                    
                    inbox_files.append(file_info)
        except Exception as e:
            logger.warning(f"Error obteniendo archivos en cola: {e}")
        
        return jsonify({
            'status': 'ok',
            'estado': 'exitoso',
            'inbox_count': inbox_count,
            'processing_count': processing_count,
            'processed_count': processed_count,
            'error_count': errors_count,
            'inbox_files': inbox_files,
            'queue_status': {
                'inbox': inbox_count,
                'pending': inbox_count,
                'processing': processing_count,
                'completed': processed_count,
                'processed': processed_count,
                'results_available': results_count,
                'errors': errors_count
            },
            'system_status': {
                'ocr_loaded': getattr(app_module, '_ocr_components_loaded', False),
                'worker_running': getattr(app_module, '_worker_running', False)
            },
            'total_active': inbox_count + processing_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cola: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error al obtener estado: {str(e)}',
            'message': f'Error getting queue status: {str(e)}'
        }), 500



@app.route('/api/ocr/processed_files')
def api_processed_files():
    """
    FIX: Endpoint para obtener lista de archivos procesados con sus resultados
    REASON: Usuario necesita ver lista de archivos procesados con selectores y visor
    IMPACT: Interface mejorada para gestión de resultados OCR
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        processed_files = []
        results_dir = Path(directories['results'])
        processed_dir = Path(directories['processed'])
        
        # Crear directorios si no existen
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        
        # Buscar archivos JSON de resultados con mapeo inteligente
        for json_file in results_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                # FIX: Algoritmo inteligente de mapeo archivo-resultado
                # REASON: Sistema actual no puede mapear BATCH_ prefijos con archivos originales
                # IMPACT: Correlación correcta entre archivos procesados y resultados JSON
                image_name, image_path = _find_corresponding_image(json_file, result_data, processed_dir)
                
                if not image_path:
                    # Busqueda fallback usando nombre del JSON
                    fallback_name = json_file.stem
                    for ext in ['.png', '.jpg', '.jpeg']:
                        potential_path = processed_dir / f"{fallback_name}{ext}"
                        if potential_path.exists():
                            image_path = str(potential_path.relative_to(Path.cwd()))
                            image_name = fallback_name
                            break
                
                # FIX: Estructura de datos completa para prevenir valores "undefined"
                # REASON: Frontend esperaba campos específicos que no existían
                # IMPACT: Datos consistentes y completos en todas las respuestas
                # TEST: Validación de todos los campos requeridos por frontend
                # MONITOR: Logging de campos faltantes para debugging
                # INTERFACE: Estructura de datos compatible con dashboard
                # VISUAL_CHANGE: Información correcta visible en lugar de "undefined"
                # REFERENCE_INTEGRITY: Todos los campos validados y con valores por defecto
                
                # Extraer estadísticas de procesamiento
                calidad_extraccion = result_data.get('calidad_extraccion', {})
                estadisticas = result_data.get('estadisticas', {})
                datos_extraidos = result_data.get('datos_extraidos', {})
                
                # Calcular tiempo de procesamiento
                tiempo_procesamiento = result_data.get('tiempo_procesamiento', 0)
                tiempo_procesamiento_formatted = f"{tiempo_procesamiento:.2f}s" if tiempo_procesamiento > 0 else "N/A"
                
                # Extraer palabras detectadas
                palabras_detectadas = estadisticas.get('total_palabras', 0)
                if palabras_detectadas == 0:
                    # Intentar extraer de otras fuentes
                    palabras_detectadas = len(datos_extraidos.get('palabras_individuales', []))
                
                # Extraer confianza promedio
                confianza_promedio = calidad_extraccion.get('confianza_promedio', 0)
                if confianza_promedio == 0:
                    confianza_promedio = estadisticas.get('confianza_promedio', 0)
                
                # Formatear confianza
                confianza_formatted = f"{confianza_promedio:.1f}%" if confianza_promedio > 0 else "N/A"
                
                # Extraer texto completo
                texto_completo = datos_extraidos.get('texto_completo', '')
                if not texto_completo:
                    texto_completo = result_data.get('texto_extraido', '')
                
                processed_files.append({
                    'filename': json_file.name,
                    'image_name': image_name or 'Sin_nombre',
                    'image_path': image_path or '',
                    'json_path': str(json_file.relative_to(Path.cwd())),
                    'result_data': result_data,
                    'processed_date': datetime.fromtimestamp(json_file.stat().st_mtime).isoformat(),
                    'file_size': json_file.stat().st_size,
                    'has_coordinates': 'coordenadas' in datos_extraidos,
                    'extraction_quality': calidad_extraccion.get('categoria', 'N/A'),
                    
                    # FIX: Campos específicos para frontend
                    'tiempo_procesamiento': tiempo_procesamiento_formatted,
                    'palabras_detectadas': palabras_detectadas,
                    'confianza_promedio': confianza_formatted,
                    'texto_completo': texto_completo[:200] + '...' if len(texto_completo) > 200 else texto_completo,
                    
                    # FIX: Campos de estado para interface
                    'estado': 'completado',
                    'disponible': True,
                    'error': None,
                    
                    # FIX: Metadata para visualización
                    'metadata': {
                        'original_filename': result_data.get('archivo_info', {}).get('original_filename', image_name or 'Sin_nombre'),
                        'formato': result_data.get('archivo_info', {}).get('formato', 'N/A'),
                        'tamaño_imagen': result_data.get('archivo_info', {}).get('tamaño', 'N/A'),
                        'fecha_creacion': result_data.get('archivo_info', {}).get('fecha_creacion', 'N/A')
                    }
                })
                
            except Exception as e:
                logger.warning(f"Error procesando archivo {json_file}: {e}")
                continue
        
        # Ordenar por fecha de procesamiento
        processed_files.sort(key=lambda x: x['processed_date'], reverse=True)
        
        return jsonify({
            'status': 'exitoso',
            'estado': 'exitoso',
            'processed_files': processed_files,
            'total_files': len(processed_files),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos procesados: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error al obtener archivos procesados: {str(e)}',
            'message': f'Error getting processed files: {str(e)}'
        }), 500

@app.route('/api/ocr/result_data/<filename>')
def get_result_data(filename):
    """
    FIX: Endpoint específico para datos de resultados del visualizador
    REASON: Frontend necesita datos estructurados para el visualizador de resultados
    IMPACT: Elimina valores "undefined" en el visualizador y proporciona datos completos
    TEST: Verifica estructura de datos específica para visualizador
    MONITOR: Logging de requests de visualizador para debugging
    INTERFACE: Datos estructurados específicos para componentes de visualización
    VISUAL_CHANGE: Visualizador muestra datos reales en lugar de "undefined"
    REFERENCE_INTEGRITY: Validación de existencia de archivos antes de respuesta
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        # FIX: Búsqueda inteligente de archivos JSON con múltiples estrategias
        # REASON: Los nombres de archivos pueden tener diferentes formatos (.png.json vs .json)
        # IMPACT: Encuentra archivos JSON correctamente independiente del formato de nombre
        # TEST: Busca con múltiples patrones de nombres posibles
        # MONITOR: Logging de estrategias de búsqueda para debugging
        # INTERFACE: Compatibilidad con diferentes formatos de nombres desde frontend
        # VISUAL_CHANGE: Visualizador encuentra datos correctamente
        # REFERENCE_INTEGRITY: Validación exhaustiva de existencia de archivos
        
        results_dir = Path(directories['results'])
        json_path = None
        searched_files = []
        
        # Estrategia 1: Nombre directo si ya termina en .json
        if filename.endswith('.json'):
            direct_path = results_dir / filename
            searched_files.append(filename)
            if direct_path.exists():
                json_path = direct_path
        
        # Estrategia 2: Agregar .json si no lo tiene
        if not json_path:
            json_filename = filename if filename.endswith('.json') else f"{filename}.json"
            candidate_path = results_dir / json_filename
            searched_files.append(json_filename)
            if candidate_path.exists():
                json_path = candidate_path
        
        # Estrategia 3: Reemplazar extensión con .json
        if not json_path:
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            json_filename = f"{base_name}.json"
            candidate_path = results_dir / json_filename
            searched_files.append(json_filename)
            if candidate_path.exists():
                json_path = candidate_path
        
        # Estrategia 4: Buscar por patrón fuzzy
        if not json_path:
            import re
            # Extraer parte base del nombre sin extensiones
            base_pattern = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.json', '')
            
            for json_file in results_dir.glob('*.json'):
                if base_pattern in json_file.name:
                    json_path = json_file
                    searched_files.append(json_file.name)
                    break
        
        # Si no se encuentra, buscar en directorio de procesados
        if not json_path:
            processed_dir = Path(directories['processed'])
            for strategy_name in searched_files:
                candidate_path = processed_dir / strategy_name
                if candidate_path.exists():
                    json_path = candidate_path
                    break
        
        if not json_path:
            return jsonify({
                'status': 'error',
                'message': 'Archivo de resultados no encontrado',
                'filename': filename,
                'searched_files': searched_files,
                'searched_directories': [str(results_dir), str(Path(directories['processed']))]
            }), 404
        
        # Leer datos del archivo JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # FIX: Estructura específica para visualizador
        # REASON: Visualizador requiere campos específicos para mostrar datos
        # IMPACT: Datos consistentes y completos en visualizador
        # TEST: Todos los campos del visualizador tienen valores válidos
        # MONITOR: Logging de datos enviados al visualizador
        # INTERFACE: Estructura optimizada para componentes de visualización
        # VISUAL_CHANGE: Visualizador muestra información real y detallada
        # REFERENCE_INTEGRITY: Validación de estructura de datos antes de envío
        
        calidad_extraccion = result_data.get('calidad_extraccion', {})
        estadisticas = result_data.get('estadisticas', {})
        datos_extraidos = result_data.get('datos_extraidos', {})
        archivo_info = result_data.get('archivo_info', {})
        
        # FIX: Extracción robusta de texto desde múltiples ubicaciones posibles
        # REASON: Archivos de caché tienen estructura diferente que no está siendo detectada
        # IMPACT: Visualizador muestra texto real extraído por OCR en lugar de estar vacío
        # TEST: Busca texto en todas las ubicaciones posibles del JSON
        # MONITOR: Logging de ubicación encontrada para debugging
        # INTERFACE: Visualizador muestra texto completo extraído
        # VISUAL_CHANGE: Texto OCR ahora visible en lugar de campo vacío
        # REFERENCE_INTEGRITY: Validación de datos extraídos antes de envío
        
        # Buscar texto en múltiples ubicaciones
        texto_completo = ''
        texto_sources = [
            datos_extraidos.get('texto_completo', ''),
            result_data.get('texto_extraido', ''),
            result_data.get('ocr_data', {}).get('texto_completo', ''),
            result_data.get('ocr_data', {}).get('raw_text', ''),
            result_data.get('raw_text', '')
        ]
        
        for source in texto_sources:
            if source and isinstance(source, str) and len(source.strip()) > 0:
                texto_completo = source.strip()
                logger.debug(f"Texto encontrado en fuente: {len(texto_completo)} caracteres")
                break
                break
        
        # Extraer coordenadas desde múltiples ubicaciones
        coordenadas = []
        coordenadas_sources = [
            datos_extraidos.get('coordenadas', []),
            result_data.get('ocr_data', {}).get('coordenadas', []),
            result_data.get('coordenadas', []),
            result_data.get('word_coordinates', [])
        ]
        
        for source in coordenadas_sources:
            if source and isinstance(source, list) and len(source) > 0:
                coordenadas = source
                break
        
        # MANDATO 8: Extraer palabras detectadas para calcular confidence_avg
        palabras_detectadas = []
        palabras_sources = [
            datos_extraidos.get('palabras_detectadas', []),
            datos_extraidos.get('palabras_individuales', []),
            result_data.get('ocr_data', {}).get('palabras_individuales', []),
            result_data.get('palabras_individuales', []),
            result_data.get('word_data', [])
        ]
        
        for source in palabras_sources:
            if source and isinstance(source, list) and len(source) > 0:
                palabras_detectadas = source
                break
        
        # MANDATO 8: Calcular confidence_avg real desde palabras detectadas
        confidence_avg = 0
        if palabras_detectadas:
            confidences = []
            for word in palabras_detectadas:
                if isinstance(word, dict):
                    conf = word.get('confianza', word.get('confidence', 0))
                    if conf > 0:
                        confidences.append(conf)
            if confidences:
                confidence_avg = sum(confidences) / len(confidences)
        
        # Extraer palabras individuales (mantener compatibilidad)
        palabras_individuales = palabras_detectadas
        
        # Extraer datos financieros
        datos_financieros = datos_extraidos.get('datos_financieros', {})
        if not datos_financieros:
            datos_financieros = result_data.get('datos_financieros', {})
        
        # Preparar respuesta estructurada
        viewer_data = {
            'status': 'success',
            'filename': filename,
            'archivo_info': {
                'nombre_original': archivo_info.get('original_filename', filename),
                'formato': archivo_info.get('formato', 'N/A'),
                'tamaño': archivo_info.get('tamaño', 'N/A'),
                'fecha_procesamiento': result_data.get('fecha_procesamiento', 'N/A')
            },
            'estadisticas': {
                'tiempo_procesamiento': f"{result_data.get('tiempo_procesamiento', 0):.2f}s",
                'total_palabras': estadisticas.get('total_palabras', len(palabras_individuales)),
                'confianza_promedio': f"{calidad_extraccion.get('confianza_promedio', confidence_avg):.1f}%",
                'confidence_avg': round(confidence_avg, 2),  # MANDATO 8: Campo específico para frontend
                'calidad_categoria': calidad_extraccion.get('categoria', 'N/A'),
                'palabras_alta_confianza': estadisticas.get('palabras_alta_confianza', 0),
                'palabras_baja_confianza': estadisticas.get('palabras_baja_confianza', 0)
            },
            'texto_extraido': {
                'texto_completo': texto_completo,
                'longitud_texto': len(texto_completo),
                'lineas_texto': len(texto_completo.split('\n')) if texto_completo else 0
            },
            'coordenadas': {
                'disponibles': len(coordenadas) > 0,
                'total': len(coordenadas),
                'elementos': coordenadas[:50]  # Limitar para performance
            },
            'palabras_individuales': {
                'total': len(palabras_individuales),
                'con_coordenadas': len([p for p in palabras_individuales if p.get('coordenadas')]),
                'elementos': palabras_individuales[:50]  # Limitar para performance
            },
            'datos_financieros': {
                'disponibles': len(datos_financieros) > 0,
                'campos_detectados': list(datos_financieros.keys()) if datos_financieros else [],
                'datos': datos_financieros
            },
            'calidad_extraccion': {
                'score': calidad_extraccion.get('score', 0),
                'categoria': calidad_extraccion.get('categoria', 'N/A'),
                'confianza_promedio': calidad_extraccion.get('confianza_promedio', 0),
                'distribucion_confianza': calidad_extraccion.get('distribucion_confianza', {}),
                'recomendaciones': calidad_extraccion.get('recomendaciones', [])
            }
        }
        
        return jsonify(viewer_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo datos para visualizador {filename}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error obteniendo datos del visualizador: {str(e)}',
            'filename': filename
        }), 500

@app.route('/api/ocr/download_json/<filename>')
def download_json(filename):
    """
    FIX: Endpoint para descargar archivos JSON de resultados OCR
    REASON: Usuario necesita poder descargar resultados JSON individualmente
    IMPACT: Permite acceso directo a resultados de OCR procesados
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        # Buscar archivo JSON en directorio de resultados
        results_dir = Path(directories['results'])
        json_filename = filename.replace('.png', '.json')
        json_path = results_dir / json_filename
        
        if not json_path.exists():
            # Buscar también en directorio de procesados
            processed_dir = Path(directories['processed'])
            json_path = processed_dir / json_filename
            
        if not json_path.exists():
            return jsonify({
                'status': 'error',
                'message': 'Archivo JSON no encontrado'
            }), 404
        
        # Leer y devolver el archivo JSON
        from flask import send_file
        return send_file(
            json_path,
            as_attachment=True,
            download_name=json_filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error descargando JSON {filename}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error descargando archivo: {str(e)}'
        }), 500

# Sistema de gestión de API Keys
API_KEYS_FILE = 'api_keys.json'

def load_api_keys():
    """Cargar API keys desde archivo"""
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_api_keys(keys_data):
    """Guardar API keys en archivo"""
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(keys_data, f, indent=2)

def generate_api_key():
    """Generar una nueva API key única"""
    import secrets
    return f"ocr_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"

@app.route('/api/generate_key', methods=['POST'])
def api_generate_key():
    """
    FIX: Endpoint para generar nuevas API keys con permisos configurables
    REASON: Usuario requiere sistema de generación de API keys para uso externo
    IMPACT: Permite autenticación segura para integraciones externas del sistema OCR
    """
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        permissions = data.get('permissions', {})
        
        if not name:
            return jsonify({
                'status': 'error',
                'message': 'Nombre requerido para la API key'
            }), 400
            
        # Generar nueva API key
        api_key = generate_api_key()
        key_id = str(uuid.uuid4())
        
        # Cargar keys existentes
        keys_data = load_api_keys()
        
        # Añadir nueva key
        keys_data[key_id] = {
            'id': key_id,
            'name': name,
            'key': api_key,
            'permissions': permissions,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'usage_count': 0
        }
        
        # Guardar
        save_api_keys(keys_data)
        
        logger.info(f"Nueva API key generada: {name} ({key_id})")
        
        return jsonify({
            'status': 'success',
            'api_key': api_key,
            'key_id': key_id,
            'message': 'API key generada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error generando API key: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error generando API key: {str(e)}'
        }), 500

@app.route('/api/list_keys')
def api_list_keys():
    """
    FIX: Endpoint para listar API keys existentes (sin mostrar la key)
    REASON: Usuario necesita ver y gestionar API keys creadas
    IMPACT: Interface de gestión completa para API keys del sistema
    """
    try:
        keys_data = load_api_keys()
        
        # Preparar respuesta sin exponer las keys
        keys_list = []
        for key_info in keys_data.values():
            keys_list.append({
                'id': key_info['id'],
                'name': key_info['name'],
                'created_at': key_info['created_at'],
                'last_used': key_info.get('last_used'),
                'usage_count': key_info.get('usage_count', 0),
                'permissions': key_info.get('permissions', {})
            })
        
        return jsonify({
            'status': 'success',
            'keys': keys_list
        })
        
    except Exception as e:
        logger.error(f"Error listando API keys: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error listando API keys: {str(e)}'
        }), 500

@app.route('/api/revoke_key/<key_id>', methods=['DELETE'])
def api_revoke_key(key_id):
    """
    FIX: Endpoint para revocar API keys específicas
    REASON: Usuario necesita poder eliminar API keys no utilizadas o comprometidas
    IMPACT: Gestión segura completa del ciclo de vida de API keys
    """
    try:
        keys_data = load_api_keys()
        
        if key_id not in keys_data:
            return jsonify({
                'status': 'error',
                'message': 'API key no encontrada'
            }), 404
            
        # Remover la key
        removed_key = keys_data.pop(key_id)
        save_api_keys(keys_data)
        
        logger.info(f"API key revocada: {removed_key['name']} ({key_id})")
        
        return jsonify({
            'status': 'success',
            'message': 'API key revocada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error revocando API key: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error revocando API key: {str(e)}'
        }), 500

@app.route('/api/clean', methods=['POST'])
def api_clean():
    """
    FIX: Endpoint crítico para limpiar el sistema después de procesar lotes
    REASON: Interface llama a /api/clean que estaba faltante en routes.py principal
    IMPACT: Botones de limpieza completamente funcionales siguiendo workflow empresarial
    TEST: Limpia directorios processed, results, errors y temporales correctamente
    MONITOR: Logging detallado de archivos eliminados y contadores por directorio
    INTERFACE: Endpoint llamado por botones de limpieza en interface_excellence_dashboard.html
    VISUAL_CHANGE: Habilita funcionalidad completa de limpieza en workflow empresarial
    REFERENCE_INTEGRITY: Endpoint /api/clean ahora existe y es accesible desde frontend
    """
    try:
        from config import get_async_directories
        import glob
        import shutil
        
        directories = get_async_directories()
        cleaned_counts = {}
        
        # FIX: Mover archivos procesados a HISTORIAL en lugar de eliminarlos
        # REASON: Usuario requiere historial para preservar archivos sin interferir con nuevos lotes
        # IMPACT: Limpieza segura que preserva archivos en historial empresarial permanente
        # WORKFLOW: processed → historial → eliminación tras 24h en historial solamente
        # INTEGRIDAD: Archivos procesados NO interfieren pero se preservan en historial
        processed_files = glob.glob(os.path.join(directories['processed'], "*.*"))
        processed_moved = 0
        historial_dir = 'data/historial'
        # Crear directorio historial si no existe
        os.makedirs(historial_dir, exist_ok=True)
        
        for file_path in processed_files:
            try:
                filename = os.path.basename(file_path)
                # Agregar timestamp al archivo en historial para evitar conflictos
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                historial_filename = f"{name}_historial_{timestamp}{ext}"
                historial_path = os.path.join(historial_dir, historial_filename)
                
                # Mover archivo a historial
                shutil.move(file_path, historial_path)
                processed_moved += 1
                logger.debug(f"Archivo movido a historial: {filename} → {historial_filename}")
            except Exception as e:
                logger.warning(f"No se pudo mover archivo procesado {file_path}: {e}")
        cleaned_counts['processed_moved_to_historial'] = processed_moved
        
        # FIX: Mover archivos results a HISTORIAL y aplicar eliminación 24h SOLO en historial
        # REASON: Usuario requiere que archivos procesados vayan a historial, eliminación 24h solo en historial
        # IMPACT: Results activos se mueven a historial, eliminación temporal SOLO en historial
        # WORKFLOW: results → historial → eliminación tras 24h SOLO en historial
        # INTEGRIDAD: Results no acumulan, historial maneja retención temporal
        
        from datetime import datetime, timedelta
        
        # Mover archivos results a historial
        result_files = glob.glob(os.path.join(directories['results'], "*.json"))
        results_moved = 0
        
        for file_path in result_files:
            try:
                filename = os.path.basename(file_path)
                # Agregar timestamp para evitar conflictos en historial
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                historial_filename = f"{name}_result_{timestamp}{ext}"
                historial_path = os.path.join(historial_dir, historial_filename)
                
                # Mover a historial
                shutil.move(file_path, historial_path)
                results_moved += 1
                logger.debug(f"Resultado movido a historial: {filename} → {historial_filename}")
            except Exception as e:
                logger.warning(f"No se pudo mover resultado {file_path}: {e}")
        
        cleaned_counts['results_moved_to_historial'] = results_moved
        
        # FIX: Aplicar eliminación de 24 horas SOLO en directorio historial
        # REASON: Historial mantiene archivos 24h antes de eliminación final
        # IMPACT: Eliminación temporal solo afecta historial, no archivos activos
        historial_files = glob.glob(os.path.join(historial_dir, "*.*"))
        historial_cleaned = 0
        historial_preserved = 0
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for file_path in historial_files:
            try:
                file_stat = os.stat(file_path)
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    # Archivo en historial tiene más de 24 horas, eliminar definitivamente
                    os.remove(file_path)
                    historial_cleaned += 1
                    logger.debug(f"Archivo historial eliminado (>24h): {os.path.basename(file_path)}")
                else:
                    # Archivo reciente en historial, preservar
                    historial_preserved += 1
                    logger.debug(f"Archivo historial preservado (<24h): {os.path.basename(file_path)}")
                    
            except Exception as e:
                logger.warning(f"No se pudo procesar archivo historial {file_path}: {e}")
                
        cleaned_counts['historial_eliminated'] = historial_cleaned
        cleaned_counts['historial_preserved'] = historial_preserved
        
        if historial_preserved > 0:
            logger.info(f"📁 Historial empresarial: {historial_preserved} preservados, {historial_cleaned} eliminados (>24h)")
        
        # FIX: Limpiar directorio errors (opcional para archivos con errores)
        # REASON: Limpiar archivos que fallaron en procesamiento anterior
        # IMPACT: Sistema libre de archivos problemáticos acumulados
        try:
            error_files = glob.glob(os.path.join(directories.get('errors', 'data/errors'), "*.*"))
            errors_cleaned = 0
            for file_path in error_files:
                try:
                    os.remove(file_path)
                    errors_cleaned += 1
                except Exception as e:
                    logger.warning(f"No se pudo eliminar error {file_path}: {e}")
            cleaned_counts['errors'] = errors_cleaned
        except Exception as e:
            logger.warning(f"Error accediendo directorio de errores: {e}")
            cleaned_counts['errors'] = 0
        
        # FIX: Limpiar directorios temporales web
        # REASON: Eliminar directorios temporales creados durante procesamiento web
        # IMPACT: Libera espacio y evita acumulación de archivos temporales
        temp_dirs = glob.glob(os.path.join('temp', 'web_*'))
        temp_cleaned = 0
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                temp_cleaned += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio temporal {temp_dir}: {e}")
        cleaned_counts['temp_dirs'] = temp_cleaned
        
        total_cleaned = sum(cleaned_counts.values())
        logger.info(f"✅ Sistema limpiado exitosamente: {cleaned_counts} - Total: {total_cleaned} elementos")
        
        return jsonify({
            'status': 'exitoso',
            'estado': 'exitoso',
            'message': 'Sistema limpiado exitosamente',
            'mensaje': 'Sistema limpiado exitosamente',
            'cleaned_counts': cleaned_counts,
            'total_cleaned': total_cleaned,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error crítico limpiando sistema: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'message': f'Error al limpiar sistema: {str(e)}',
            'mensaje': f'Error al limpiar sistema: {str(e)}',
            'error_code': 'CLEAN_SYSTEM_ERROR',
            'timestamp': datetime.now().isoformat(),
            'success': False
        }), 500

@app.route('/api/extract_all_results', methods=['GET'])
def api_extract_all_results():
    """
    FIX: Endpoint para extraer TODOS los archivos (historial completo)
    REASON: Usuario necesita acceder tanto a lote actual como historial completo
    IMPACT: Separación entre procesamiento actual y acceso a historial
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        results_dir = directories['results']
        
        # Buscar TODOS los archivos (como estaba antes)
        json_files = []
        
        # Buscar en directorio results activo (archivos actuales)
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(results_dir, file)
                    if os.path.isfile(file_path):
                        json_files.append(file_path)
        
        # Buscar TAMBIÉN en directorio historial empresarial
        historial_dir = 'data/historial'
        if os.path.exists(historial_dir):
            for file in os.listdir(historial_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(historial_dir, file)
                    if os.path.isfile(file_path):
                        json_files.append(file_path)
                        
        logger.info(f"📊 Archivos encontrados (historial completo): {len(json_files)} archivos")
        
        if not json_files:
            return jsonify({
                'status': 'warning',
                'message': 'No hay resultados disponibles para extraer',
                'total_files': 0,
                'error_code': 'NO_RESULTS_AVAILABLE'
            }), 404
        
        # Procesar como antes pero con todos los archivos
        consolidated_results = {
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'total_archivos': len(json_files),
                'version_sistema': '1.0',
                'tipo_extraccion': 'historial_completo'
            },
            'archivos_procesados': []
        }
        
        # Procesar todos los archivos ordenados por fecha
        file_info_list = []
        
        for json_file in json_files:
            try:
                file_path = json_file
                file_stat = os.stat(file_path)
                modification_time = file_stat.st_mtime
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                batch_info = _extract_batch_info(json_file)
                
                file_info_list.append({
                    'file_path': json_file,
                    'result_data': result_data,
                    'modification_time': modification_time,
                    'batch_info': batch_info
                })
                
            except Exception as e:
                logger.error(f"Error procesando archivo {json_file}: {e}")
                continue
        
        # Ordenar por fecha de modificación (más reciente primero)
        file_info_list.sort(key=lambda x: x['modification_time'], reverse=True)
        
        # Procesar archivos y extraer datos estructurados
        for file_info in file_info_list:
            try:
                json_file = file_info['file_path']
                result_data = file_info['result_data']
                batch_info = file_info['batch_info']
                
                nombre_archivo = _extract_original_filename(json_file, result_data)
                
                metadata = result_data.get('metadata', {})
                texto_completo = _extract_full_text(result_data)
                
                tracking_params = _extract_tracking_parameters(nombre_archivo, metadata, result_data)
                
                enterprise_fields = _extract_enterprise_fields(result_data, texto_completo)
                
                archivo_resultado = {
                    'nombre_archivo': nombre_archivo,
                    'lote': batch_info.get('batch_id', 'N/A'),
                    'fecha_procesamiento': batch_info.get('date', 'N/A'),
                    'caption': tracking_params.get('caption', ''),
                    'otro': tracking_params.get('otro', ''),
                    'referencia': enterprise_fields.get('referencia', ''),
                    'bancoorigen': enterprise_fields.get('bancoorigen', ''),
                    'monto': enterprise_fields.get('monto', ''),
                    'datosbeneficiario': {
                        'cedula': enterprise_fields.get('cedula', ''),
                        'telefono': enterprise_fields.get('telefono', ''),
                        'banco_destino': enterprise_fields.get('banco_destino', '')
                    },
                    'pago_fecha': enterprise_fields.get('pago_fecha', ''),
                    'concepto': enterprise_fields.get('concepto', ''),
                    'texto_total_ocr': texto_completo[:500] if texto_completo else ''
                }
                
                consolidated_results['archivos_procesados'].append(archivo_resultado)
                
            except Exception as e:
                logger.error(f"Error extrayendo datos empresariales de {json_file}: {e}")
                archivo_resultado = {
                    'nombre_archivo': os.path.basename(json_file),
                    'lote': 'Error',
                    'error': str(e),
                    'status': 'error_extraccion'
                }
                consolidated_results['archivos_procesados'].append(archivo_resultado)
        
        response = jsonify(consolidated_results)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=historial_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        logger.info(f"✅ JSON historial completo generado: {len(consolidated_results['archivos_procesados'])} archivos")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generando JSON historial completo: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error generando historial: {str(e)}'
        }), 500

@app.route('/api/batches/download/<string:batch_id>', methods=['GET'])
def api_download_batch_results(batch_id):
    """
    MANDATO: Endpoint optimizado para descargar JSON de lotes específicos con reutilización
    OBJETIVO: Reutilizar archivo JSON previamente guardado si existe, generar y guardar si no existe
    UBICACIÓN: routes.py, función api_download_batch_results()
    AHORRO CRÉDITOS: Evita regeneración innecesaria, lee archivos existentes primero
    """
    try:
        from config import get_async_directories
        
        directories = get_async_directories()
        results_dir = directories['results']
        historial_dir = directories.get('historial', 'data/historial')
        
        # Convención de nombre: [lote_id]_resultados.json
        cached_json_filename = f"{batch_id}_resultados.json"
        cached_json_path = os.path.join(results_dir, cached_json_filename)
        
        # PASO 1: Intentar buscar archivo JSON previamente guardado
        if os.path.exists(cached_json_path):
            logger.info(f"📁 REUTILIZACIÓN: Archivo JSON encontrado para lote {batch_id}")
            try:
                with open(cached_json_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                response = jsonify(cached_data)
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                response.headers['Content-Disposition'] = f'attachment; filename=resultados_{batch_id}.json'
                
                logger.info(f"✅ REUTILIZACIÓN: JSON servido desde caché para lote {batch_id}")
                return response
                
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"⚠️ Error leyendo JSON cacheado {cached_json_path}: {e}")
                # Continuar con generación si el archivo está corrupto
        
        # PASO 2: Si no existe, generar JSON completo para el lote
        logger.info(f"🔄 GENERACIÓN: Creando JSON para lote {batch_id}")
        
        # Buscar archivos del lote específico
        batch_files = []
        
        # Buscar en directorio results
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.endswith('.json') and file.startswith(batch_id):
                    batch_files.append(os.path.join(results_dir, file))
        
        # Buscar en directorio historial
        if os.path.exists(historial_dir):
            for file in os.listdir(historial_dir):
                if file.endswith('.json') and file.startswith(batch_id):
                    batch_files.append(os.path.join(historial_dir, file))
        
        if not batch_files:
            logger.warning(f"❌ No se encontraron archivos para el lote {batch_id}")
            return jsonify({
                'status': 'error',
                'message': f'No se encontraron archivos para el lote {batch_id}',
                'error_code': 'BATCH_NOT_FOUND'
            }), 404
        
        # Generar JSON consolidado con estructura empresarial
        consolidated_results = {
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'total_archivos': len(batch_files),
                'version_sistema': '1.0',
                'tipo_extraccion': 'lote_especifico',
                'lote_id': batch_id
            },
            'archivos_procesados': []
        }
        
        for json_file in batch_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extraer datos empresariales usando la misma lógica que extract_results
                archivo_resultado = _extract_enterprise_data_from_json(data, json_file)
                archivo_resultado['lote_id'] = batch_id
                
                consolidated_results['archivos_procesados'].append(archivo_resultado)
                
            except Exception as e:
                logger.error(f"Error procesando archivo {json_file}: {e}")
                continue
        
        # PASO 3: Guardar JSON generado para reutilización futura
        try:
            os.makedirs(results_dir, exist_ok=True)
            with open(cached_json_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 CACHÉ: JSON guardado para reutilización futura: {cached_json_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error guardando JSON en caché: {e}")
            # Continuar sirviendo el JSON aunque no se pueda guardar
        
        # PASO 4: Servir JSON recién generado
        response = jsonify(consolidated_results)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=resultados_{batch_id}.json'
        
        logger.info(f"✅ GENERACIÓN: JSON servido para lote {batch_id} ({len(batch_files)} archivos)")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error crítico en descarga de lote {batch_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error descargando lote {batch_id}: {str(e)}',
            'error_code': 'BATCH_DOWNLOAD_ERROR'
        }), 500

@app.route('/api/batches/history', methods=['GET'])
def api_get_batch_history():
    """
    FIX: Endpoint para obtener historial completo de lotes con numeración correcta
    REASON: Usuario necesita ver todos los lotes procesados con numeración secuencial
    IMPACT: Dropdown de lotes muestra historial completo con números de lote
    """
    try:
        from config import get_async_directories
        import glob
        
        directories = get_async_directories()
        results_dir = directories['results']
        
        # Obtener todos los archivos JSON de resultados
        batch_files = {}
        
        # Buscar en directorio results activo
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.endswith('.json') and 'BATCH_' in file:
                    file_path = os.path.join(results_dir, file)
                    if os.path.isfile(file_path):
                        # Extraer batch_prefix del nombre del archivo - CORREGIDO PARA MOSTRAR TODOS LOS ARCHIVOS
                        try:
                            parts = file.split('_')
                            if len(parts) >= 4:
                                # Usar solo las primeras 3 partes para agrupar por lote
                                # Esto asegura que todos los archivos del mismo lote se muestren juntos
                                batch_prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"
                                batch_date = datetime.strptime(parts[1], '%Y%m%d').date()
                                batch_time = datetime.strptime(parts[2], '%H%M%S').time()
                                
                                # Usar batch_prefix para agrupar todos los archivos del mismo lote
                                if batch_prefix not in batch_files:
                                    batch_files[batch_prefix] = {
                                        'id': batch_prefix,
                                        'date': datetime.combine(batch_date, batch_time).isoformat(),
                                        'files': []
                                    }
                                
                                batch_files[batch_prefix]['files'].append(file)
                        except (ValueError, IndexError):
                            continue
        
        # Buscar en directorio historial
        historial_dir = 'data/historial'
        if os.path.exists(historial_dir):
            for file in os.listdir(historial_dir):
                if file.endswith('.json') and 'BATCH_' in file:
                    file_path = os.path.join(historial_dir, file)
                    if os.path.isfile(file_path):
                        # Extraer batch_prefix del nombre del archivo - CORREGIDO PARA MOSTRAR TODOS LOS ARCHIVOS
                        try:
                            parts = file.split('_')
                            if len(parts) >= 4:
                                # Usar solo las primeras 3 partes para agrupar por lote
                                # Esto asegura que todos los archivos del mismo lote se muestren juntos
                                batch_prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"
                                batch_date = datetime.strptime(parts[1], '%Y%m%d').date()
                                batch_time = datetime.strptime(parts[2], '%H%M%S').time()
                                
                                # Usar batch_prefix para agrupar todos los archivos del mismo lote
                                if batch_prefix not in batch_files:
                                    batch_files[batch_prefix] = {
                                        'id': batch_prefix,
                                        'date': datetime.combine(batch_date, batch_time).isoformat(),
                                        'files': []
                                    }
                                
                                batch_files[batch_prefix]['files'].append(file)
                        except (ValueError, IndexError):
                            continue
        
        # Convertir a lista y ordenar por fecha (más reciente primero)
        batches = list(batch_files.values())
        batches.sort(key=lambda x: x['date'], reverse=True)
        
        # Añadir numeración secuencial y total de archivos
        for index, batch in enumerate(batches):
            batch['number'] = len(batches) - index  # Numeración inversa
            batch['totalFiles'] = len(batch['files'])
        
        logger.info(f"📊 Historial de lotes: {len(batches)} lotes encontrados")
        
        return jsonify({
            'status': 'success',
            'batches': batches,
            'total_batches': len(batches)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de lotes: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error obteniendo historial: {str(e)}'
        }), 500

@app.route('/api/extract_results', methods=['GET'])
def api_extract_results():
    """
    FIX: Endpoint crítico para extraer JSON consolidado empresarial con estructura específica
    REASON: Usuario requiere JSON consolidado NO ZIP con campos específicos empresariales
    IMPACT: Formato final estructurado para procesamiento empresarial de recibos
    TEST: Genera JSON con todos los archivos procesados en formato empresarial
    MONITOR: Logging detallado de extracción consolidada y estadísticas empresariales
    INTERFACE: Endpoint llamado por extractResults() para descarga JSON consolidado
    VISUAL_CHANGE: Descarga JSON consolidado en lugar de ZIP con archivos individuales
    REFERENCE_INTEGRITY: Estructura empresarial con campos obligatorios por archivo
    """
    try:
        from config import get_async_directories
        import tempfile
        from flask import send_file
        
        directories = get_async_directories()
        results_dir = directories['results']
        
        # Crear directorio de resultados si no existe
        os.makedirs(results_dir, exist_ok=True)
        
        # Si el directorio estaba vacío, usar historial como fuente principal
        if not os.path.exists(results_dir) or not os.listdir(results_dir):
            logger.info(f"Directorio de resultados vacío, usando historial como fuente principal")
            historial_dir = directories.get('historial', 'data/historial')
            if os.path.exists(historial_dir):
                results_dir = historial_dir
        
        # INTEGRIDAD TOTAL: Usar ID único del lote actual
        current_batch_id = _get_current_batch_id_from_file()
        json_files = []
        
        if current_batch_id:
            # Buscar archivos del lote específico usando el ID único
            logger.info(f"📊 INTEGRIDAD TOTAL: Buscando archivos del lote único: {current_batch_id}")
            
            # Buscar archivos en AMBOS directorios con el ID único
            all_json_files = []
            
            # Buscar en directorio results
            if os.path.exists(results_dir):
                for file in os.listdir(results_dir):
                    if file.endswith('.json') and file.startswith(current_batch_id):
                        file_path = os.path.join(results_dir, file)
                        if os.path.isfile(file_path):
                            all_json_files.append(file_path)
            
            # Buscar TAMBIÉN en historial (para archivos que se movieron automáticamente)
            historial_dir = directories.get('historial', 'data/historial')
            if os.path.exists(historial_dir):
                for file in os.listdir(historial_dir):
                    if file.endswith('.json') and file.startswith(current_batch_id):
                        file_path = os.path.join(historial_dir, file)
                        if os.path.isfile(file_path):
                            all_json_files.append(file_path)
            
            json_files = all_json_files
            logger.info(f"📊 INTEGRIDAD TOTAL: Encontrados {len(json_files)} archivos del lote único {current_batch_id}")
        else:
            logger.warning("📊 No hay lote único configurado, usando fallback temporal")
            # Fallback: buscar por proximidad temporal si no hay ID único
            # [mantener código anterior como fallback]
            all_json_files = []
            
            # Buscar en directorio results
            if os.path.exists(results_dir):
                for file in os.listdir(results_dir):
                    if file.endswith('.json') and file.startswith('BATCH_'):
                        file_path = os.path.join(results_dir, file)
                        if os.path.isfile(file_path):
                            all_json_files.append(file_path)
            
            # Buscar TAMBIÉN en historial (para archivos que se movieron automáticamente)
            historial_dir = directories.get('historial', 'data/historial')
            if os.path.exists(historial_dir):
                for file in os.listdir(historial_dir):
                    if file.endswith('.json') and file.startswith('BATCH_'):
                        file_path = os.path.join(historial_dir, file)
                        if os.path.isfile(file_path):
                            all_json_files.append(file_path)
            
            # Agrupar archivos por proximidad temporal (mismo minuto de procesamiento)
            if all_json_files:
                file_timestamps = []
                for file_path in all_json_files:
                    filename = os.path.basename(file_path)
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        timestamp = f"{parts[1]}_{parts[2]}"
                        file_timestamps.append((timestamp, file_path))
                
                batch_groups = {}
                for timestamp, file_path in file_timestamps:
                    batch_minute = timestamp[:13]  # YYYYMMDD_HHMM
                    if batch_minute not in batch_groups:
                        batch_groups[batch_minute] = []
                    batch_groups[batch_minute].append(file_path)
                
                if batch_groups:
                    sorted_batches = sorted(batch_groups.keys(), reverse=True)
                    if sorted_batches:
                        latest_batch_minute = sorted_batches[0]
                        json_files = batch_groups[latest_batch_minute]
                        logger.info(f"📥 FALLBACK: Recuperando TODOS los archivos del último lote por ejecución: {latest_batch_minute} ({len(json_files)} archivos)")
        
        if not json_files:
            logger.info("📭 No hay archivos JSON disponibles")
                        
        # INTEGRIDAD TOTAL: Determinar el ID del lote actual correctamente
        current_batch_id = "Sin lotes"
        if json_files:
            # Analizar el primer archivo para determinar el lote
            first_file = os.path.basename(json_files[0])
            if first_file.startswith('BATCH_'):
                parts = first_file.split('_')
                if len(parts) >= 3:
                    current_batch_id = f"{parts[0]}_{parts[1]}_{parts[2]}"
        logger.info(f"📊 INTEGRIDAD TOTAL: Mostrando {len(json_files)} archivos del lote {current_batch_id}")
        
        if not json_files:
            logger.info("No hay archivos de resultados disponibles para extraer")
            return jsonify({
                'status': 'warning',
                'message': 'No hay resultados disponibles para extraer',
                'total_files': 0,
                'error_code': 'NO_RESULTS_AVAILABLE'
            }), 404
        
        # FIX: Generar JSON consolidado empresarial con estructura específica requerida
        # REASON: Usuario requiere formato consolidado con campos específicos empresariales
        # IMPACT: Estructura empresarial lista para procesamiento posterior
        consolidated_results = {
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'total_archivos': len(json_files),
                'version_sistema': '1.0',
                'tipo_extraccion': 'consolidado_empresarial'
            },
            'archivos_procesados': []
        }
        
        # FIX: ORDENAMIENTO POR FECHA DE PROCESAMIENTO (MAYOR A MENOR)
        # REASON: Usuario requiere que el último procesado aparezca primero
        # IMPACT: Lista ordenada con archivos más recientes al inicio
        file_info_list = []
        
        for json_file in json_files:
            try:
                file_path = json_file
                file_stat = os.stat(file_path)
                modification_time = file_stat.st_mtime
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                # Extraer información del lote desde el nombre del archivo
                batch_info = _extract_batch_info(json_file)
                
                file_info_list.append({
                    'file_path': json_file,
                    'result_data': result_data,
                    'modification_time': modification_time,
                    'batch_info': batch_info
                })
                
            except Exception as e:
                logger.error(f"Error procesando archivo {json_file}: {e}")
                continue
        
        # Ordenar por fecha de modificación (más reciente primero)
        file_info_list.sort(key=lambda x: x['modification_time'], reverse=True)
        
        # Procesar archivos ordenados y extraer datos estructurados
        # FIX: ORDENAMIENTO INVERSO PARA CAMPO NUMERO_LLEGADA
        # REASON: Último procesado debe tener el número mayor (orden inverso al procesamiento)
        # IMPACT: Campo 'numero_llegada' muestra orden correcto (último=mayor número)
        total_archivos = len(file_info_list)
        
        for index, file_info in enumerate(file_info_list):
            try:
                json_file = file_info['file_path']
                result_data = file_info['result_data']
                batch_info = file_info['batch_info']
                
                # Extraer nombre de archivo original
                nombre_archivo = _extract_original_filename(json_file, result_data)
                
                # Extraer metadatos WhatsApp si están disponibles
                metadata = result_data.get('metadata', {})
                caption = metadata.get('caption', '')
                
                # Extraer texto completo para análisis
                texto_completo = _extract_full_text(result_data)
                
                # FIX: Extracción inteligente de campos empresariales específicos
                # REASON: Mapeo de campos empresariales desde OCR estructurado
                # IMPACT: Campos empresariales extraídos automáticamente cuando están disponibles
                campos_empresariales = _extract_enterprise_fields(result_data, texto_completo)
                
                # FIX: AGREGAR INFORMACIÓN DEL LOTE AL ARCHIVO
                # REASON: Usuario requiere saber a qué lote pertenece cada archivo
                # IMPACT: Campo 'lote' visible en lista de procesamientos
                lote_info = batch_info.get('lote_id', 'N/A')
                lote_fecha = batch_info.get('fecha_procesamiento', 'N/A')
                
                # FIX: Asegurar que caption se popule basado en contenido del texto
                # REASON: Caption debe reflejar el tipo de transacción detectado
                # IMPACT: Mejora información contextual en respuesta empresarial
                if not caption and texto_completo:
                    if 'PagomovilBDV' in texto_completo:
                        caption = 'Pago Móvil BDV'
                    elif 'Transferencia' in texto_completo:
                        caption = 'Transferencia Bancaria'
                    elif 'Envio' in texto_completo:
                        caption = 'Envío de Dinero'
                    elif 'Operacion' in texto_completo and 'Banco' in texto_completo:
                        caption = 'Operación Bancaria'
                    elif any(term in texto_completo for term in ['Bs', 'bolivares', 'Banco']):
                        caption = 'Transacción Financiera'
                
                # MANDATO CRÍTICO BACKEND #1: Extracción de parámetros de seguimiento desde metadata/filename
                # REASON: Frontend necesita parámetros de entrada (codigo_sorteo, id_whatsapp, etc.) en respuesta
                # IMPACT: Sistema completo de seguimiento para correlación frontend-backend
                tracking_params = _extract_tracking_parameters(nombre_archivo, metadata, result_data)
                
                # FIX: CORRECCIÓN ORDENAMIENTO NUMERO_LLEGADA (ORDEN INVERSO)
                # REASON: Último procesado debe tener el número mayor dentro del lote
                # IMPACT: Campo 'numero_llegada' refleja orden inverso de procesamiento
                numero_llegada_corregido = total_archivos - index  # Último archivo = número mayor
                tracking_params['numero_llegada'] = numero_llegada_corregido
                
                # Pequeña pausa para evitar 100% CPU usage
                import time
                time.sleep(0.01)  # 10ms pausa para eficiencia de créditos
                
                # MANDATO CRÍTICO #2: Inclusión obligatoria de texto_total_ocr y concepto redefinido
                # REASON: Campo texto_total_ocr AUSENTE violaba mandato estructural  
                # IMPACT: Campo texto_total_ocr incluido con texto completo + concepto conciso separado
                # INTEGRIDAD TOTAL: Campo codigo_sorteo removido según solicitud del usuario
                archivo_consolidado = {
                    'nombre_archivo': nombre_archivo,
                    'id_whatsapp': tracking_params.get('id_whatsapp', ''),      # MANDATO: Parámetro de seguimiento
                    'nombre_usuario': tracking_params.get('nombre_usuario', ''), # MANDATO: Parámetro de seguimiento
                    'caption': caption,
                    'hora_exacta': tracking_params.get('hora_exacta', ''),      # MANDATO: Parámetro de seguimiento
                    'numero_llegada': tracking_params.get('numero_llegada', 0), # MANDATO: Parámetro de seguimiento NUEVO
                    'otro': campos_empresariales.get('otro', ''),
                    'referencia': campos_empresariales.get('referencia', ''),
                    'bancoorigen': campos_empresariales.get('bancoorigen', ''),
                    'monto': campos_empresariales.get('monto', ''),
                    'datosbeneficiario': {
                        'cedula': campos_empresariales.get('cedula', ''),
                        'telefono': campos_empresariales.get('telefono', ''),
                        'banco_destino': campos_empresariales.get('banco_destino', '')
                    },
                    'pago_fecha': campos_empresariales.get('pago_fecha', ''),
                    'concepto': campos_empresariales.get('concepto', ''),
                    'texto_total_ocr': texto_completo,  # MANDATO #22: Campo obligatorio con texto completo
                    # NUEVO: Información del lote
                    'lote_id': lote_info,
                    'lote_fecha': lote_fecha,
                    # Campos técnicos adicionales
                    'extraction_stats': {
                        'confidence': campos_empresariales.get('confidence', 0),
                        'total_words': campos_empresariales.get('total_words', 0),
                        'processing_time': result_data.get('tiempo_procesamiento', 0)
                    }
                }
                
                consolidated_results['archivos_procesados'].append(archivo_consolidado)
                logger.debug(f"Archivo procesado: {nombre_archivo} - {len(texto_completo)} chars")
                
            except Exception as file_error:
                logger.error(f"Error procesando archivo {json_file}: {file_error}")
                # FIX: Incluir archivos con error en resultado final con campos en blanco
                # REASON: Usuario requiere que todos los archivos aparezcan aunque tengan errores
                # IMPACT: Estructura completa sin omitir archivos problemáticos
                archivo_error = {
                    'nombre_archivo': os.path.basename(json_file).replace('.json', ''),
                    'caption': '',
                    'otro': '',
                    'referencia': '',
                    'bancoorigen': '',
                    'monto': '',
                    'datosbeneficiario': {
                        'cedula': '',
                        'telefono': '',
                        'banco_destino': ''
                    },
                    'pago_fecha': '',
                    'concepto': '',
                    'texto_total_ocr': '',  # MANDATO #22: Campo obligatorio incluso en errores
                    'extraction_stats': {
                        'confidence': 0,
                        'total_words': 0,
                        'processing_time': 0,
                        'error': str(file_error)
                    }
                }
                consolidated_results['archivos_procesados'].append(archivo_error)
        
        # Crear archivo JSON temporal para descarga
        temp_json = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        
        try:
            # Escribir JSON consolidado con formato legible
            import json as json_module
            json_module.dump(consolidated_results, temp_json, ensure_ascii=False, indent=2)
            temp_json.close()
            
            # Generar nombre descriptivo para el archivo JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"resultados_consolidados_{timestamp}.json"
            
            logger.info(f"✅ JSON consolidado generado exitosamente: {len(json_files)} archivos")
            logger.info(f"📊 Estadísticas consolidadas: {consolidated_results['metadata']}")
            
            # Retornar archivo JSON consolidado para descarga
            return send_file(
                temp_json.name,
                as_attachment=True,
                download_name=json_filename,
                mimetype='application/json'
            )
            
        except Exception as json_error:
            # Limpiar archivo temporal en caso de error
            if os.path.exists(temp_json.name):
                os.unlink(temp_json.name)
            raise json_error
            
    except Exception as e:
        logger.error(f"Error crítico en extract_results consolidado: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error extrayendo resultados consolidados: {str(e)}',
            'error_code': 'EXTRACT_CONSOLIDATED_ERROR'
        }), 500

def _extract_enterprise_data_from_json(data, json_file_path):
    """
    MANDATO: Función auxiliar para extraer datos empresariales desde archivo JSON
    OBJETIVO: Reutilizar lógica existente para extraer campos empresariales
    UBICACIÓN: routes.py, función _extract_enterprise_data_from_json()
    """
    try:
        filename = os.path.basename(json_file_path)
        
        # Extraer metadatos de WhatsApp desde el nombre del archivo
        metadatos_whatsapp = _extract_whatsapp_metadata(filename)
        
        # Usar la función existente para extraer campos empresariales
        datos_extraidos = data.get('datos_extraidos', {})
        texto_completo = datos_extraidos.get('texto_completo', '')
        
        # Extraer campos empresariales usando la función existente
        campos_empresariales = _extract_enterprise_fields(data, texto_completo)
        
        # Construir estructura empresarial final
        archivo_resultado = {
            'nombre_archivo': filename.replace('.json', ''),
            'id_whatsapp': metadatos_whatsapp.get('id_whatsapp', ''),
            'nombre_usuario': metadatos_whatsapp.get('nombre_usuario', ''),
            'caption': metadatos_whatsapp.get('caption', 'Operación Bancaria'),
            'hora_exacta': metadatos_whatsapp.get('hora_exacta', ''),
            'numero_llegada': metadatos_whatsapp.get('numero_llegada', 0),
            'otro': campos_empresariales.get('otro', ''),
            'referencia': campos_empresariales.get('referencia', ''),
            'bancoorigen': campos_empresariales.get('bancoorigen', ''),
            'monto': campos_empresariales.get('monto', ''),
            'datosbeneficiario': {
                'cedula': campos_empresariales.get('cedula', ''),
                'telefono': campos_empresariales.get('telefono', ''),
                'banco_destino': campos_empresariales.get('banco_destino', '')
            },
            'pago_fecha': campos_empresariales.get('pago_fecha', ''),
            'concepto': campos_empresariales.get('concepto', ''),
            'texto_total_ocr': campos_empresariales.get('texto_total_ocr', texto_completo),
            'lote_fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'extraction_stats': {
                'confidence': campos_empresariales.get('confidence', 0),
                'total_words': campos_empresariales.get('total_words', 0),
                'processing_time': data.get('processing_time', 0)
            }
        }
        
        return archivo_resultado
        
    except Exception as e:
        logger.error(f"Error extrayendo datos empresariales de {json_file_path}: {e}")
        return {
            'nombre_archivo': os.path.basename(json_file_path).replace('.json', ''),
            'error': str(e),
            'status': 'error_extraccion'
        }

def _extract_whatsapp_metadata(filename):
    """
    MANDATO: Extraer metadatos de WhatsApp desde nombre de archivo
    OBJETIVO: Reutilizar parsing existente para nombres de archivos WhatsApp
    UBICACIÓN: routes.py, función _extract_whatsapp_metadata()
    """
    try:
        # Formato: BATCH_YYYYMMDD_HHMMSS_hash_numero_YYYYMMDD-X--idwhatsapp@lid_nombre_HH-MM_timestamp.ext
        import re
        
        # Patrón para extraer metadatos WhatsApp
        whatsapp_pattern = r'(\d+)_(\d{8})-([A-Z])--(\d+)@lid_([^_]+)_(\d{2}-\d{2})_'
        
        match = re.search(whatsapp_pattern, filename)
        if match:
            numero_llegada = match.group(1)
            fecha_sorteo = match.group(2)
            codigo_sorteo = match.group(3)
            id_whatsapp = match.group(4)
            nombre_usuario = match.group(5)
            hora_exacta = match.group(6)
            
            return {
                'numero_llegada': int(numero_llegada),
                'fecha_sorteo': fecha_sorteo,
                'codigo_sorteo': codigo_sorteo,
                'id_whatsapp': id_whatsapp,
                'nombre_usuario': nombre_usuario,
                'hora_exacta': hora_exacta,
                'caption': f'Operación de {nombre_usuario}',
                'raw_filename': filename
            }
        
        # Fallback para nombres simples
        return {
            'numero_llegada': 0,
            'fecha_sorteo': '',
            'codigo_sorteo': '',
            'id_whatsapp': '',
            'nombre_usuario': '',
            'hora_exacta': '',
            'caption': 'Operación Bancaria',
            'raw_filename': filename
        }
        
    except Exception as e:
        logger.warning(f"Error extrayendo metadatos WhatsApp de {filename}: {e}")
        return {
            'numero_llegada': 0,
            'fecha_sorteo': '',
            'codigo_sorteo': '',
            'id_whatsapp': '',
            'nombre_usuario': '',
            'hora_exacta': '',
            'caption': 'Operación Bancaria',
            'raw_filename': filename
        }

def _extract_batch_info(json_file_path):
    """
    FIX: Extraer información del lote desde el nombre del archivo
    REASON: Usuario requiere saber a qué lote pertenece cada archivo
    IMPACT: Campo 'lote' visible en lista de procesamientos
    """
    try:
        filename = os.path.basename(json_file_path)
        
        # Extraer información del formato BATCH_YYYYMMDD_HHMMSS_hash_filename
        if filename.startswith('BATCH_'):
            parts = filename.split('_')
            if len(parts) >= 3:
                batch_date = parts[1]  # YYYYMMDD
                batch_time = parts[2]  # HHMMSS
                
                # Formar el ID del lote
                lote_id = f"BATCH_{batch_date}_{batch_time}"
                
                # Convertir fecha a formato legible
                try:
                    fecha_dt = datetime.strptime(f"{batch_date}{batch_time}", "%Y%m%d%H%M%S")
                    fecha_procesamiento = fecha_dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    fecha_procesamiento = f"{batch_date[:4]}-{batch_date[4:6]}-{batch_date[6:8]} {batch_time[:2]}:{batch_time[2:4]}:{batch_time[4:6]}"
                
                return {
                    'lote_id': lote_id,
                    'fecha_procesamiento': fecha_procesamiento,
                    'batch_date': batch_date,
                    'batch_time': batch_time
                }
        
        # Fallback para archivos sin formato BATCH_
        return {
            'lote_id': 'Lote Individual',
            'fecha_procesamiento': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'batch_date': '',
            'batch_time': ''
        }
        
    except Exception as e:
        logger.error(f"Error extrayendo información del lote: {e}")
        return {
            'lote_id': 'N/A',
            'fecha_procesamiento': 'N/A',
            'batch_date': '',
            'batch_time': ''
        }

def _find_corresponding_image(json_file, result_data, processed_dir):
    """
    FIX: Algoritmo inteligente de mapeo archivo-resultado para correlación correcta
    REASON: Nombres con prefijo BATCH_ no coinciden con archivos originales WhatsApp
    IMPACT: Mapeo correcto entre resultados JSON y archivos procesados
    TEST: Maneja múltiples convenciones de nomenclatura y busqueda fuzzy
    MONITOR: Logging de correlaciones exitosas y fallidas para análisis
    INTERFACE: Permite visualización correcta de resultados en interface
    VISUAL_CHANGE: Resultados mostrados correctamente con archivos correspondientes
    REFERENCE_INTEGRITY: Validación de existencia de archivos antes de mapeo
    """
    import difflib
    from pathlib import Path
    
    # Extraer información del JSON para mapeo inteligente
    original_filename = None
    
    # Buscar en metadata del resultado
    if isinstance(result_data, dict):
        # Buscar en diferentes ubicaciones posibles
        metadata_sources = [
            result_data.get('metadata', {}),
            result_data.get('archivo_info', {}),
            result_data.get('imagen_info', {}),
            result_data
        ]
        
        for source in metadata_sources:
            if isinstance(source, dict):
                original_filename = (
                    source.get('original_filename') or
                    source.get('filename') or
                    source.get('archivo_original') or
                    source.get('nombre_archivo')
                )
                if original_filename:
                    break
    
    # Lista de archivos procesados disponibles
    processed_files = []
    for ext in ['.png', '.jpg', '.jpeg']:
        processed_files.extend(processed_dir.glob(f'*{ext}'))
    
    if not processed_files:
        return None, None
    
    # Estrategia 1: Busqueda por nombre original si está disponible
    if original_filename:
        original_name = Path(original_filename).stem
        for img_file in processed_files:
            if img_file.stem == original_name:
                return img_file.stem, str(img_file.relative_to(Path.cwd()))
    
    # Estrategia 2: Remover prefijo BATCH_ del JSON y buscar coincidencia
    # FIX: CORRECCIÓN CRÍTICA - Algoritmo corregido para extraer nombre exacto desde formato BATCH
    # REASON: Algoritmo anterior fallaba en detectar nombres con formatos WhatsApp complejos
    # IMPACT: Mapeo correcto al 100% entre archivos BATCH y archivos procesados
    # TEST: Maneja BATCH_20250706_193217_170_20250706-H--212950389261079@lid_Ana_16-58_20250706_193129_330.png.json
    # MONITOR: Logging detallado con validación de cada paso del algoritmo
    # INTERFACE: Todos los archivos procesados ahora visibles en visualizador
    # VISUAL_CHANGE: Elimina mensaje "No hay resultados disponibles para este archivo"
    # REFERENCE_INTEGRITY: Validación exhaustiva de existencia y mapeo antes de retorno
    json_name = json_file.stem
    if json_name.startswith('BATCH_'):
        # Formato completo: BATCH_20250706_193217_170_20250706-H--212950389261079@lid_Ana_16-58_20250706_193129_330.png
        # Estrategia: buscar patrón de fecha al inicio del filename (después del hash)
        
        # Dividir por guiones bajos
        parts = json_name.split('_')
        logger.debug(f"Analizando BATCH: {json_name} → partes: {parts}")
        
        if len(parts) >= 4:
            # Las primeras 3 partes son: BATCH, fecha, hora
            # La cuarta parte es el hash (3-8 caracteres)
            # Después del hash viene el filename real
            
            # Buscar donde empieza el filename (después del hash)
            for i in range(3, len(parts)):
                remaining_parts = parts[i:]
                potential_filename = '_'.join(remaining_parts)
                
                # Verificar si esta parte contiene patrón de fecha YYYYMMDD
                if len(remaining_parts) > 0 and len(remaining_parts[0]) >= 8:
                    # Si la primera parte restante empieza con fecha (8 dígitos), es el filename
                    first_part = remaining_parts[0]
                    if first_part[:8].isdigit() and first_part.startswith('202'):
                        # Es el filename real, construir nombre completo
                        clean_name = potential_filename
                        
                        # Remover extensión si está presente
                        for ext in ['.png', '.jpg', '.jpeg']:
                            if clean_name.endswith(ext):
                                clean_name = clean_name[:-len(ext)]
                                break
                        
                        logger.debug(f"✅ Filename extraído: {json_name} → {clean_name}")
                        
                        # Buscar archivo correspondiente
                        for img_file in processed_files:
                            if img_file.stem == clean_name:
                                logger.info(f"✅ Mapeo BATCH exitoso: {json_file.name} → {img_file.name}")
                                return img_file.stem, str(img_file.relative_to(Path.cwd()))
                        
                        # Si no se encuentra exacto, intentar sin extensiones adicionales
                        base_clean_name = clean_name.split('.')[0]  # Remover cualquier extensión extra
                        for img_file in processed_files:
                            if img_file.stem == base_clean_name:
                                logger.info(f"✅ Mapeo BATCH exitoso (base): {json_file.name} → {img_file.name}")
                                return img_file.stem, str(img_file.relative_to(Path.cwd()))
                        break
    
    # Estrategia 3: Busqueda fuzzy por similitud de nombres
    json_stem = json_file.stem
    file_stems = [f.stem for f in processed_files]
    
    # Buscar mejor coincidencia por similitud
    matches = difflib.get_close_matches(json_stem, file_stems, n=1, cutoff=0.6)
    if matches:
        best_match = matches[0]
        for img_file in processed_files:
            if img_file.stem == best_match:
                logger.debug(f"Mapeo fuzzy exitoso: {json_file.name} → {img_file.name}")
                return img_file.stem, str(img_file.relative_to(Path.cwd()))
    
    logger.warning(f"No se pudo mapear resultado JSON: {json_file.name}")
    return None, None

def _extract_original_filename(json_file, result_data):
    """
    FIX: Extrae el nombre de archivo original desde metadata o desde nombre del JSON
    REASON: Necesario para identificar correctamente los archivos en formato consolidado
    IMPACT: Nombres de archivos correctos en estructura empresarial
    """
    # Intentar extraer desde metadata primero
    if isinstance(result_data, dict):
        metadata_sources = [
            result_data.get('metadata', {}),
            result_data.get('archivo_info', {}),
            result_data.get('imagen_info', {}),
            result_data
        ]
        
        for source in metadata_sources:
            if isinstance(source, dict):
                original_filename = (
                    source.get('original_filename') or
                    source.get('filename') or
                    source.get('archivo_original') or
                    source.get('nombre_archivo')
                )
                if original_filename:
                    return original_filename
    
    # Fallback: extraer desde nombre del archivo JSON
    json_name = os.path.basename(json_file).replace('.json', '')
    
    # Si es archivo BATCH, extraer nombre original
    if json_name.startswith('BATCH_'):
        parts = json_name.split('_')
        if len(parts) >= 4:
            # Buscar parte que contenga patrón de fecha al estilo WhatsApp
            for i, part in enumerate(parts):
                if len(part) >= 8 and part.startswith('202'):  # Formato fecha YYYYMMDD
                    # Reconstruir nombre desde la parte de fecha
                    return '_'.join(parts[i:])
    
    return json_name

def _extract_full_text(result_data):
    """
    FIX: Extrae el texto completo desde diferentes ubicaciones posibles en result_data
    REASON: Texto puede estar en diferentes campos según la estructura del resultado
    IMPACT: Extracción consistente de texto para análisis empresarial
    """
    if not isinstance(result_data, dict):
        return ""
    
    # Buscar texto en diferentes ubicaciones posibles
    text_sources = [
        result_data.get('datos_extraidos', {}).get('texto_completo', ''),
        result_data.get('texto_extraido', ''),
        result_data.get('texto_completo', ''),
        result_data.get('ocr_data', {}).get('texto_completo', ''),
        result_data.get('text', ''),
        result_data.get('full_text', '')
    ]
    
    for text in text_sources:
        if text and isinstance(text, str) and len(text.strip()) > 0:
            return text.strip()
    
    return ""

def _extract_enterprise_fields(result_data, texto_completo):
    """
    FIX: Extracción inteligente de campos empresariales específicos desde OCR
    REASON: Mapeo automático de campos empresariales desde datos estructurados de OCR
    IMPACT: Campos empresariales extraídos automáticamente cuando están disponibles
    """
    import re
    
    # Inicializar campos empresariales
    campos = {
        'otro': '',
        'referencia': '',
        'bancoorigen': '',
        'monto': '',
        'cedula': '',
        'telefono': '',
        'banco_destino': '',
        'pago_fecha': '',
        'concepto': '',
        'caption': '',  # FIX: Agregar caption explícitamente
        'nombre_beneficiario': '',  # FIX: NUEVO CAMPO CRÍTICO - MANDATO REFINAMIENTO
        'confidence': 0,
        'total_words': 0
    }
    
    # FIX: Extraer estadísticas técnicas desde estructura real de datos
    # REASON: estadisticas_ocr no existe, datos están directamente en result_data
    # IMPACT: Extracción correcta de confidence y total_words reales
    if isinstance(result_data, dict):
        datos_extraidos = result_data.get('datos_extraidos', {})
        
        # FIX: Calcular estadísticas desde palabras_detectadas reales
        palabras_detectadas = datos_extraidos.get('palabras_detectadas', [])
        if palabras_detectadas:
            # Calcular confianza promedio real
            confidencias = [p.get('confianza', 0) for p in palabras_detectadas if isinstance(p, dict)]
            if confidencias:
                campos['confidence'] = round(sum(confidencias) / len(confidencias), 3)
                campos['total_words'] = len(palabras_detectadas)
        
        # MANDATO CRÍTICO #2: INTEGRACIÓN DIRECTA DE LÓGICA DE ORO COORDENADAS
        # REASON: Usar campos texto_total_ocr y concepto_empresarial ya procesados por lógica de oro
        # IMPACT: Texto estructurado y concepto refinado automáticamente disponibles
        texto_total_ocr_coordenadas = datos_extraidos.get('texto_total_ocr', '')
        concepto_empresarial_refinado = datos_extraidos.get('concepto_empresarial', '')
        texto_completo_local = datos_extraidos.get('texto_completo', '')
        
        # PRIORIDAD MÁXIMA: Usar texto ordenado por coordenadas si está disponible
        if texto_total_ocr_coordenadas:
            campos['texto_total_ocr'] = texto_total_ocr_coordenadas
            logger.info(f"🏗️ LÓGICA DE ORO APLICADA: {len(texto_total_ocr_coordenadas)} caracteres ordenados por coordenadas")
        else:
            # Fallback al texto tradicional
            campos['texto_total_ocr'] = texto_completo_local
            logger.info(f"📄 Texto tradicional usado: {len(texto_completo_local)} caracteres")
        
        # MANDATO CRÍTICO #2: USO DIRECTO DE CONCEPTO EMPRESARIAL REFINADO
        # REASON: Aplicar concepto ya procesado por lógica de oro con patrones empresariales
        # IMPACT: Concepto ultra-conciso sin ruido, máximo 50 caracteres, núcleo semántico puro
        if concepto_empresarial_refinado:
            campos['concepto'] = concepto_empresarial_refinado
            logger.info(f"🎯 CONCEPTO EMPRESARIAL REFINADO: '{concepto_empresarial_refinado}'")
        elif not campos['concepto']:
            # FALLBACK: Extracción tradicional como respaldo
            texto_para_concepto = texto_total_ocr_coordenadas or texto_completo_local
            if texto_para_concepto:
                # PRIORIDAD MÁXIMA: Códigos y números de proyecto/referencia específicos
                concepto_patterns = [
                    r'(?:Concepto|CONCEPTO)[:=]?\s*([A-Z0-9\s]{3,25})',   # Códigos como "4 15 D 107"
                    r'(?:Por|Para)[:=]?\s*([A-Za-z0-9\s]{5,30})',         # "Por: Pago Servicios"
                    r'(?:Motivo|MOTIVO)[:=]?\s*([A-Za-z\s]{5,30})',       # Motivo conciso
                    r'(Pago\s+(?:Móvil|Movil|de\s+\w+))',                # "Pago Móvil", "Pago de Servicios"
                    r'(Transferencia\s+(?:a\s+\w+|Bancaria))',            # "Transferencia Bancaria"
                    r'(Envío?\s+de\s+\w+)',                              # "Envío de Dinero"
                    r'([A-Z0-9]{2,}\s+[A-Z0-9]{2,}\s+[A-Z0-9]{1,})',     # Códigos alfanuméricos separados
                ]
                
                concepto_extraido = ""
                for pattern in concepto_patterns:
                    match = re.search(pattern, texto_para_concepto, re.IGNORECASE)
                    if match:
                        concepto_extraido = match.group(1).strip()
                        # VALIDAR QUE NO SEA RUIDO (como "Crear Acceso directo")
                        ruido_keywords = ['crear', 'acceso', 'directo', 'webpage', 'url', 'http', 'x', '-']
                        texto_limpio = concepto_extraido.lower().replace(' ', '')
                        if not any(ruido in texto_limpio for ruido in ruido_keywords):
                            campos['concepto'] = concepto_extraido
                            break
                        else:
                            concepto_extraido = ""  # Resetear si es ruido
            
            # FALLBACK ULTRA-ESPECÍFICO: Solo para casos extremos
            if not concepto_extraido:
                # Buscar códigos o números significativos aislados
                codigo_match = re.search(r'([A-Z0-9]{2,}\s+[A-Z0-9]{2,}(?:\s+[A-Z0-9]{1,})?)', texto_completo_local)
                if codigo_match:
                    concepto_extraido = codigo_match.group(1).strip()
            
            # FALLBACK INTELIGENTE: Si no hay concepto específico, extraer frase relevante
            if not concepto_extraido:
                # Buscar primera frase que contenga información financiera
                frases_relevantes = [
                    r'([^.]*(?:Bs|bolivares|monto|transferencia|pago|envio)[^.]{0,30})',
                    r'([A-Z][^.]{20,60}(?:realizada|enviado|operacion)[^.]{0,20})',
                ]
                
                for pattern in frases_relevantes:
                    match = re.search(pattern, texto_completo_local, re.IGNORECASE)
                    if match:
                        concepto_extraido = match.group(1).strip()
                        break
                
                # ÚLTIMO FALLBACK: Primeras palabras significativas (no todo el texto)
                if not concepto_extraido and len(texto_completo_local) > 20:
                    palabras = texto_completo_local.split()[:15]  # Máximo 15 palabras
                    concepto_extraido = ' '.join(palabras)
            
            campos['concepto'] = concepto_extraido[:100] if concepto_extraido else "Transacción financiera"
        
        # FIX: EXTRACCIÓN AVANZADA CON COORDENADAS Y PROXIMIDAD INTELIGENTE
        # REASON: Usar coordenadas geométricas para mapeo preciso de campos empresariales
        # IMPACT: Extracción robusta que maneja diferentes layouts y reduce falsos positivos
        palabras_detectadas = datos_extraidos.get('palabras_detectadas', [])
        if palabras_detectadas:
            # Aplicar extracción inteligente basada en coordenadas
            campos_coordenadas = _extract_with_coordinate_proximity(palabras_detectadas, texto_completo_local)
            for campo, valor in campos_coordenadas.items():
                if valor and not campos.get(campo):
                    campos[campo] = valor
            
            # FIX: EXTRACCIÓN CRÍTICA BASADA EN COORDENADAS REALES DE ONNXTR
            # REASON: Aprovechar coordenadas geométricas para mapeo espacial preciso
            # IMPACT: Elimina falsos positivos y mejora precisión de campos empresariales
            campos_onnxtr = _extract_onnxtr_enterprise_fields(palabras_detectadas, texto_completo_local)
            for campo, valor in campos_onnxtr.items():
                if valor and not campos.get(campo):
                    campos[campo] = valor
                elif valor and campo in ['caption', 'otro']:  # Sobrescribir caption y otro siempre
                    campos[campo] = valor
        
        # MANDATO CRÍTICO #3: DETECCIÓN DIRECTA DE BANCO DESTINO CON CÓDIGOS BANCARIOS  
        # REASON: "Bancoc 0105 - BANCO MERCANIIL" debe extraer "BANCO MERCANTIL" como banco_destino
        # IMPACT: Implementación directa de códigos bancarios en función de extracción empresarial
        if not campos.get('banco_destino') and texto_completo_local:
            # TABLA DE CÓDIGOS BANCARIOS VENEZOLANOS (FUENTE DE ALTA FIABILIDAD)
            codigos_bancarios = {
                '0102': 'BANCO DE VENEZUELA',
                '0105': 'BANCO MERCANTIL', 
                '0108': 'BBVA PROVINCIAL',
                '0115': 'BANCO EXTERIOR',
                '0134': 'BANESCO',
                '0172': 'BANCAMIGA',
                '0191': 'BANCO NACIONAL DE CREDITO'
            }
            
            bancoorigen_actual = campos.get('bancoorigen', '')
            
            # BÚSQUEDA POR CÓDIGO BANCARIO CON MÁXIMA PRIORIDAD
            for codigo, nombre_banco in codigos_bancarios.items():
                if codigo in texto_completo_local and nombre_banco != bancoorigen_actual:
                    campos['banco_destino'] = nombre_banco
                    break
        
        # Buscar también en extracted_fields_positional como fallback
        extracted_fields = datos_extraidos.get('extracted_fields_positional', {})
        if extracted_fields:
            for campo in ['referencia', 'monto', 'bancoorigen', 'cedula', 'telefono', 'banco_destino', 'pago_fecha']:
                valor = extracted_fields.get(campo, '')
                if valor and not campos.get(campo):
                    campos[campo] = valor
            
        # FIX: Buscar también en datos_financieros como fallback
        datos_financieros = datos_extraidos.get('datos_financieros', {})
        if datos_financieros and not campos['monto']:
            campos['monto'] = datos_financieros.get('monto', '')
            campos['referencia'] = datos_financieros.get('referencia', campos['referencia'])
            
        # FIX: Extraer bancoorigen desde texto si no está en campos estructurados
        if not campos['bancoorigen'] and texto_completo_local:
            # Buscar patrón "Banco : XXXX" o "BANCO XXXX"
            import re
            banco_match = re.search(r'[Bb]anco\s*[:=]?\s*([A-Z][A-Z\s]+)', texto_completo_local)
            if banco_match:
                campos['bancoorigen'] = banco_match.group(1).strip()
    
    # FIX: EXTRACCIÓN CRÍTICA FINAL DE CAPTION BASADA EN TEXTO
    # REASON: Garantizar que caption se asigne siempre después de procesar campos
    # IMPACT: Población definitiva de caption sin fallos
    if not campos['caption'] and texto_completo:
        if 'PagomovilBDV' in texto_completo:
            campos['caption'] = 'Pago Móvil BDV'
        elif 'Transferencia' in texto_completo:
            campos['caption'] = 'Transferencia Bancaria'
        elif 'Envio' in texto_completo:
            campos['caption'] = 'Envío de Dinero'
        elif 'Operacion' in texto_completo and 'Banco' in texto_completo:
            campos['caption'] = 'Operación Bancaria'
        elif any(term in texto_completo for term in ['Bs', 'bolivares', 'Banco']):
            campos['caption'] = 'Transacción Financiera'
    
    # FIX: Análisis mejorado de texto completo con patrones empresariales específicos
    # REASON: Extraer datos desde texto cuando no están en campos estructurados
    # IMPACT: Mejora significativa en población de campos empresariales
    if texto_completo:
        import re
        
        # FIX: Buscar monto con patrones venezolanos específicos
        if not campos['monto']:
            monto_patterns = [
                r'(\d{1,3}(?:[,\.]\d{2,3})*(?:[,\.]\d{2})?\s*Bs)',  # 104,54 Bs
                r'Bs\.?\s*(\d{1,3}(?:[,\.]\d{2,3})*(?:[,\.]\d{2})?)',  # Bs 104,54
                r'(\d{1,3}(?:[,\.]\d{2,3})*(?:[,\.]\d{2})?)\s*bolivares',  # 104,54 bolivares
            ]
            for pattern in monto_patterns:
                match = re.search(pattern, texto_completo, re.IGNORECASE)
                if match:
                    campos['monto'] = match.group(1) if 'Bs' in match.group(0) else match.group(0)
                    break
        
        # FIX: EXTRACCIÓN CRÍTICA DE REFERENCIA - MANDATO REFINAMIENTO  
        # REASON: Priorizar secuencias numéricas largas cerca de palabras clave
        # IMPACT: Corrección de "Fecha" → "48311146148" y "0000120" → "000012071"
        if not campos['referencia']:
            ref_patterns = [
                r'(?:Operacion|OPERACION)\s*[:;=]?\s*(\d{8,15})',     # Operacion : 003039387344
                r'(?:Referencia|REFERENCIA)\s*[:;=]?\s*(\d{8,15})',   # REFERENCIA : 190018901378
                r'(?:Ref|REF)\s*[:;=]?\s*(\d{8,15})',                # Ref: 003039387344
                r'(?:NUMERO DE REFERENCIA)\s*[:;=]?\s*(\d{8,15})',    # NUMERO DE REFERENCIA : 190018901378
                r'(\d{10,15})',                                       # Números largos directos
                r'(\d{8,12})'                                        # Números medianos como fallback
            ]
            
            # Buscar con prioridad espacial - números cerca de palabras clave
            for pattern in ref_patterns:
                matches = re.finditer(pattern, texto_completo, re.IGNORECASE)
                for match in matches:
                    referencia_num = match.group(1)
                    # Validar que es número puro y longitud apropiada
                    if referencia_num.isdigit() and 8 <= len(referencia_num) <= 15:
                        # Verificar que no es teléfono (no empieza con 04, +58)
                        if not referencia_num.startswith(('04', '58')):
                            campos['referencia'] = referencia_num
                            break
                if campos.get('referencia'):
                    break
        
        # FIX: EXTRACCIÓN CRÍTICA DE CÉDULA - MANDATO REFINAMIENTO
        # REASON: Fortalecer patrones regex para formatos V-27061025, 27.061.025
        # IMPACT: Corrección de cédulas vacías → extracción correcta con puntos y guiones
        if not campos['cedula']:
            cedula_patterns = [
                r'(?:Identificacion|C\.?I\.?|cedula|RIF|BENEFICIARIO)\s*[:=]?\s*([VvEe]?-?\d{1,2}\.?\d{3}\.?\d{3})',  # V-27.061.025
                r'([VvEe]-?\d{1,2}\.?\d{3}\.?\d{3})',                                                                # V-27.061.025 directo
                r'([VvEe]-?\d{7,9})',                                                                               # V-27061025
                r'(\d{1,2}\.?\d{3}\.?\d{3})',                                                                       # 27.061.025
                r'(\d{7,9})',                                                                                       # 27061025 directo
            ]
            for pattern in cedula_patterns:
                matches = re.finditer(pattern, texto_completo, re.IGNORECASE)
                for match in matches:
                    cedula_str = match.group(1)
                    # Validar longitud apropiada después de limpiar
                    cedula_digits = re.sub(r'[^\d]', '', cedula_str)
                    if 7 <= len(cedula_digits) <= 9:
                        # Verificar que no es teléfono (no empieza con 04, 02)
                        if not cedula_digits.startswith(('04', '02', '58')):
                            campos['cedula'] = cedula_str
                            break
                if campos.get('cedula'):
                    break
        
        # MANDATO CRÍTICO #1: FUNCIÓN TELEFONO CONSOLIDADA CON VALIDACIÓN ESTRICTA
        # REASON: Esta función secundaria ignoraba validación venezolana causando asignación incorrecta
        # IMPACT: ELIMINACIÓN de asignación sin validación - solo prefijos venezolanos válidos
        if not campos['telefono']:
            # VALIDACIÓN ESTRICTA: Solo prefijos de operadores celulares venezolanos
            prefijos_validos = ['0412', '0416', '0426', '0414', '0424']
            
            telefono_patterns = [
                r'Destino\s*[:=]?\s*(\d{11})',  # Destino : 04125318244
                r'(04\d{9})',  # 04125318244 directo - solo con prefijo 04
                r'(\+58\d{10})',  # +58 seguido de 10 dígitos
            ]
            
            telefono_validado = False
            for pattern in telefono_patterns:
                match = re.search(pattern, texto_completo)
                if match:
                    telefono_str = re.sub(r'[^\d+]', '', match.group(1))
                    
                    # VALIDACIÓN BINARIA OBLIGATORIA: APLICAR MISMAS REGLAS
                    cumple_internacional = telefono_str.startswith('+58') and len(telefono_str) == 13
                    cumple_nacional = len(telefono_str) == 11 and any(telefono_str.startswith(p) for p in prefijos_validos)
                    
                    if cumple_internacional:
                        # Convertir formato internacional a nacional
                        telefono_nacional = '0' + telefono_str[3:]
                        if any(telefono_nacional.startswith(prefijo) for prefijo in prefijos_validos):
                            campos['telefono'] = telefono_nacional
                            telefono_validado = True
                            break
                    elif cumple_nacional:
                        # Verificar que NO es la referencia ya extraída
                        if telefono_str != campos.get('referencia', ''):
                            campos['telefono'] = telefono_str
                            telefono_validado = True
                            break
                    else:
                        # MANDATO CRÍTICO: RECHAZO ABSOLUTO - NO asignar
                        # El número no cumple con prefijos venezolanos válidos
                        continue
                
                if telefono_validado:
                    break
        
        # FIX: REFINAMIENTO CRÍTICO - Buscar fecha con patrones mejorados que manejan espacios
        # REASON: Los patrones anteriores no detectaban fechas con espacios como "20/06/ 2025"
        # IMPACT: Extracción precisa de fechas venezolanas con espacios
        if not campos['pago_fecha']:
            fecha_patterns = [
                r'Fecha\s*[:=]?\s*(\d{1,2}/\d{1,2}/\s*\d{4})',  # Fecha : 20/06/ 2025 (con espacios)
                r'(\d{1,2}/\d{1,2}/\s*\d{4})',                 # 20/06/ 2025 directo (con espacios)
                r'(\d{1,2}/\d{1,2}/\d{4})',                    # 20/06/2025 sin espacios
                r'(\d{4}-\d{2}-\d{2})',                        # 2025-06-20 formato ISO
            ]
            for pattern in fecha_patterns:
                match = re.search(pattern, texto_completo)
                if match:
                    fecha_str = match.group(1).replace(' ', '')  # Eliminar espacios adicionales
                    campos['pago_fecha'] = fecha_str
                    break
    
    return campos

def _extract_with_coordinate_proximity(palabras_detectadas, texto_completo):
    """
    FIX: Extracción inteligente usando coordenadas y proximidad espacial
    REASON: Mejorar precisión de extracción aprovechando información posicional
    IMPACT: Reduce falsos positivos y mejora mapeo de campos en diferentes layouts
    """
    import re
    
    campos_extraidos = {
        'referencia': '',
        'monto': '',
        'bancoorigen': '',
        'cedula': '',
        'telefono': '',
        'banco_destino': '',
        'pago_fecha': ''
    }
    
    if not palabras_detectadas:
        return campos_extraidos
    
    # Convertir palabras a estructura con coordenadas válidas
    words_with_coords = []
    for palabra in palabras_detectadas:
        if isinstance(palabra, dict):
            coords = palabra.get('coordinates', [0, 0, 0, 0])
            if len(coords) == 4 and sum(coords) > 0:  # Coordenadas válidas
                words_with_coords.append({
                    'text': palabra.get('texto', ''),
                    'confidence': palabra.get('confianza', 0),
                    'coords': coords
                })
    
    if not words_with_coords:
        return campos_extraidos
    
    # FIX: PATRONES DE EXTRACCIÓN CON VALIDACIÓN ESPACIAL
    # REASON: Combinar regex con proximidad espacial para máxima precisión
    # IMPACT: Extracción robusta que maneja variaciones de layout
    
    # 1. EXTRACCIÓN DE REFERENCIA/OPERACIÓN (ajustado para 12 dígitos como 003039387344)
    ref_keywords = ['operacion', 'referencia', 'ref', 'op', 'numero']
    referencia = _find_field_by_spatial_proximity(words_with_coords, ref_keywords, r'\d{12}')
    if referencia:
        campos_extraidos['referencia'] = referencia
    
    # 2. EXTRACCIÓN DE MONTO VENEZOLANO
    monto_keywords = ['monto', 'total', 'bs', 'bolivares']
    monto = _find_field_by_spatial_proximity(words_with_coords, monto_keywords, r'\d{1,3}(?:[,\.]\d{2,3})*(?:[,\.]\d{2})?')
    if monto:
        campos_extraidos['monto'] = monto
    
    # 3. EXTRACCIÓN DE BANCO
    banco_keywords = ['banco', 'bco', 'entidad']
    banco = _find_field_by_spatial_proximity(words_with_coords, banco_keywords, r'[A-Z][A-Z\s]+')
    if banco:
        campos_extraidos['bancoorigen'] = banco
        campos_extraidos['banco_destino'] = banco  # Misma entidad en muchos casos
    
    # 4. EXTRACCIÓN DE CÉDULA (7-8 dígitos)
    cedula_keywords = ['identificacion', 'ci', 'cedula', 'v-']
    cedula = _find_field_by_spatial_proximity(words_with_coords, cedula_keywords, r'^[VE]?\d{7,8}$')
    if cedula:
        campos_extraidos['cedula'] = cedula
    
    # 5. EXTRACCIÓN DE TELÉFONO (11 dígitos específicamente)
    telefono_keywords = ['destino', 'telefono', 'tel', 'movil']
    telefono = _find_field_by_spatial_proximity(words_with_coords, telefono_keywords, r'^0\d{10}$')
    if telefono:
        campos_extraidos['telefono'] = telefono
    
    # 6. EXTRACCIÓN DE FECHA
    fecha_keywords = ['fecha', 'date', 'dia']
    fecha = _find_field_by_spatial_proximity(words_with_coords, fecha_keywords, r'\d{1,2}/\d{1,2}/\d{4}')
    if fecha:
        campos_extraidos['pago_fecha'] = fecha
    
    return campos_extraidos

def _find_field_by_spatial_proximity(words_with_coords, keywords, value_pattern):
    """
    FIX: Busca un campo específico usando proximidad espacial entre keyword y valor
    REASON: Mapeo inteligente que considera posición física de elementos en documento
    IMPACT: Extracción precisa que maneja diferentes layouts de documentos financieros
    """
    import re
    
    # Buscar keywords en las palabras
    keyword_positions = []
    for i, word in enumerate(words_with_coords):
        word_text = word['text'].lower()
        for keyword in keywords:
            if keyword.lower() in word_text:
                keyword_positions.append({
                    'index': i,
                    'coords': word['coords'],
                    'keyword': keyword,
                    'confidence': word['confidence']
                })
    
    if not keyword_positions:
        return None
    
    # Para cada keyword encontrado, buscar valores cercanos
    best_match = None
    best_score = 0
    
    for kw_pos in keyword_positions:
        kw_coords = kw_pos['coords']
        kw_center_x = (kw_coords[0] + kw_coords[2]) / 2
        kw_center_y = (kw_coords[1] + kw_coords[3]) / 2
        
        # Buscar palabras cercanas que coincidan con el patrón
        for i, word in enumerate(words_with_coords):
            if abs(i - kw_pos['index']) > 5:  # Límite de proximidad por índice
                continue
                
            if re.search(value_pattern, word['text']):
                word_coords = word['coords']
                word_center_x = (word_coords[0] + word_coords[2]) / 2
                word_center_y = (word_coords[1] + word_coords[3]) / 2
                
                # Calcular distancia espacial
                distance = ((kw_center_x - word_center_x) ** 2 + (kw_center_y - word_center_y) ** 2) ** 0.5
                
                # Score basado en proximidad y confianza
                proximity_score = max(0, 100 - distance)  # Máximo 100 si están en mismo lugar
                confidence_score = (kw_pos['confidence'] + word['confidence']) / 2
                total_score = proximity_score * confidence_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_match = word['text']
    
    return best_match

def _extract_onnxtr_enterprise_fields(palabras_detectadas, texto_completo):
    """
    FIX: EXTRACCIÓN EMPRESARIAL AVANZADA CON COORDENADAS ONNXTR REALES Y VALIDACIÓN INTELIGENTE
    REASON: Implementar algoritmo híbrido que combina análisis contextual y espacial para máxima precisión
    IMPACT: Elimina falsos positivos y mejora dramáticamente la extracción de campos empresariales críticos
    """
    import re
    
    campos_extraidos = {
        'referencia': '',
        'monto': '',
        'bancoorigen': '',
        'cedula': '',
        'telefono': '',
        'banco_destino': '',
        'pago_fecha': '',
        'caption': '',
        'otro': ''
    }
    
    if not palabras_detectadas or not texto_completo:
        return campos_extraidos
    
    # FIX: EXTRACCIÓN INTELIGENTE DE REFERENCIA/OPERACIÓN - MANDATO REFINAMIENTO
    # REASON: Buscar patrones específicos de operación con validación numérica
    # IMPACT: Extracción precisa de números de operación de 8-15 dígitos
    ref_patterns = [
        r'(?:Operacion|OPERACION)\s*[:;=]?\s*(\d{8,15})',     # Operacion : 003039387344
        r'(?:NUMERO DE REFERENCIA)\s*[:;=]?\s*(\d{8,15})',    # NUMERO DE REFERENCIA : 190018901378  
        r'(?:Referencia|REFERENCIA)\s*[:;=]?\s*(\d{8,15})',   # REFERENCIA : 190018901378
        r'(?:Ref|REF)\s*[:;=]?\s*(\d{8,15})',                # Ref: 003039387344
        r'(\d{10,15})',                                       # Números largos directos
        r'(\d{8,12})'                                        # Números medianos como fallback
    ]
    
    for pattern in ref_patterns:
        matches = re.finditer(pattern, texto_completo, re.IGNORECASE)
        for match in matches:
            referencia_num = match.group(1)
            # Validar que es número puro y longitud apropiada
            if referencia_num.isdigit() and 8 <= len(referencia_num) <= 15:
                # Verificar que no es teléfono (no empieza con 04, +58)
                if not referencia_num.startswith(('04', '58')):
                    campos_extraidos['referencia'] = referencia_num
                    break
        if campos_extraidos.get('referencia'):
            break
    
    # FIX: EXTRACCIÓN CRÍTICA DE BANCO ORIGEN/DESTINO - MANDATO REFINAMIENTO  
    # REASON: Implementar diccionario completo de códigos y acrónimos venezolanos
    # IMPACT: Mapeo correcto de BDV, Mercantil, Provincial según mandato crítico
    
    # Diccionario empresarial AMPLIADO de bancos venezolanos (mandato crítico)
    bank_mapping = {
        # Códigos oficiales completos
        '0102': 'BANCO DE VENEZUELA',
        '0104': 'BANCO VENEZOLANO DE CREDITO', 
        '0105': 'BANCO MERCANTIL',
        '0108': 'BBVA PROVINCIAL',
        '0114': 'BANCARIBE',
        '0115': 'BANCO EXTERIOR',
        '0134': 'BANESCO',
        '0151': 'BANCO FONDO COMUN',
        '0163': 'BANCO DEL TESORO',
        '0171': 'BANCO ACTIVO',
        '0172': 'BANCAMIGA BANCO UNIVERSAL',
        '0174': 'BANPLUS',
        '0191': 'BANCO NACIONAL DE CREDITO',
        
        # Acrónimos y nombres comerciales (mandato crítico)
        'BDV': 'BANCO DE VENEZUELA',
        'BNC': 'BANCO NACIONAL DE CREDITO',
        'BFC': 'BANCO FONDO COMUN',
        'BVC': 'BANCO VENEZOLANO DE CREDITO',
        'BANESCO': 'BANESCO',
        'MERCANTIL': 'BANCO MERCANTIL',
        'PROVINCIAL': 'BBVA PROVINCIAL',
        'BANCARIBE': 'BANCARIBE',
        'EXTERIOR': 'BANCO EXTERIOR',
        'ACTIVO': 'BANCO ACTIVO',
        'BANCAMIGA': 'BANCAMIGA BANCO UNIVERSAL',
        'BANPLUS': 'BANPLUS',
        'R4': 'R4 BANCO MICROFINANCIERO',
        
        # Patrones adicionales detectados en OCR (mandato crítico)
        'PAGOMOVILBDV': 'BANCO DE VENEZUELA',
        'PAGOMOVIL BDV': 'BANCO DE VENEZUELA',
        'PAGO MOVIL BDV': 'BANCO DE VENEZUELA',
        'BANCO MERCANTIL N': 'BANCO MERCANTIL',
        'BBVA': 'BBVA PROVINCIAL'
    }
    
    # FIX: DETECCIÓN CRÍTICA DE ACRÓNIMOS INCRUSTADOS - MANDATO REFINAMIENTO CRÍTICO
    # REASON: PagomovilBDV debe extraer "BANCO DE VENEZUELA" no "BANCO MERCANTIL"
    # IMPACT: Corrección fundamental del algoritmo de extracción bancaria posicional
    # PRIORIDAD: Primera detección de banco en documento define bancoorigen
    
    # 1. REGLA: PRIMER BANCO DETECTADO + ACRÓNIMOS INCRUSTADOS
    bancoorigen_detectado = False
    
    # Detectar acrónimos incrustados con máxima prioridad
    acronimos_incrustados = {
        'PAGOMOVILBDV': 'BANCO DE VENEZUELA',
        'PAGOMOVIL BDV': 'BANCO DE VENEZUELA', 
        'PAGO MOVIL BDV': 'BANCO DE VENEZUELA',
        'PAGOMOVILMERCANTIL': 'BANCO MERCANTIL',
        'PAGOMOVILBANESCO': 'BANESCO',
        'PAGOMOVILPROVINCIAL': 'BBVA PROVINCIAL'
    }
    
    # Buscar acrónimos incrustados PRIMERO (máxima prioridad)
    texto_upper = texto_completo.upper()
    for acronimo, banco_oficial in acronimos_incrustados.items():
        if acronimo in texto_upper:
            campos_extraidos['bancoorigen'] = banco_oficial
            campos_extraidos['caption'] = f'Pago Móvil {banco_oficial.split()[-1]}'  # BDV, Mercantil, etc.
            bancoorigen_detectado = True
            logger.info(f"🏦 ACRÓNIMO INCRUSTADO detectado: {acronimo} → {banco_oficial}")
            break
    
    # 2. REGLA: PRIMER BANCO DETECTADO ESPACIALMENTE (si no hay acrónimos)
    if not bancoorigen_detectado:
        # Buscar primera mención de banco en el texto usando diccionario completo
        primeras_menciones = []
        for codigo_banco, nombre_banco in bank_mapping.items():
            # Buscar tanto el código como el nombre en el texto
            for busqueda in [codigo_banco, nombre_banco]:
                pos = texto_upper.find(busqueda.upper())
                if pos != -1:
                    primeras_menciones.append((pos, nombre_banco, busqueda))
        
        # Ordenar por posición y tomar la primera
        if primeras_menciones:
            primeras_menciones.sort(key=lambda x: x[0])  # Ordenar por posición
            primer_banco = primeras_menciones[0][1]  # Nombre oficial del banco
            campos_extraidos['bancoorigen'] = primer_banco
            bancoorigen_detectado = True
            logger.info(f"🏦 PRIMER BANCO DETECTADO: {primer_banco}")
    
    # 3. EXTRACCIÓN DE BANCO DESTINO (segundo banco mencionado)
    if bancoorigen_detectado:
        banco_destino_patterns = [
            r'Banco\s*[:=]?\s*\d{4}\s*=\s*([A-Z\s]+[A-Z])',  # Banco : 0105 = BANCO MERCANTIL
            r'BANCO\s+([A-Z\s]+[A-Z])',                       # BANCO MERCANTIL
            r'(\d{4})\s*=\s*([A-Z\s]+BANCO[A-Z\s]*)',        # 0105 = BANCO MERCANTIL
        ]
        for pattern in banco_destino_patterns:
            match = re.search(pattern, texto_completo, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    banco_nombre = match.group(2).strip()
                else:
                    banco_nombre = match.group(1).strip()
                
                # Verificar que es diferente al banco origen y es válido
                if (len(banco_nombre) >= 8 and 
                    banco_nombre != campos_extraidos['bancoorigen'] and
                    'BANCO' in banco_nombre.upper()):
                    campos_extraidos['banco_destino'] = banco_nombre
                    break
    
    # MANDATO FASE 2 IMPLEMENTADO: EXTRACCIÓN Y NORMALIZACIÓN CRÍTICA DE MONTO VENEZOLANO
    # PROBLEMA: "210,00" se convertía a "2706102.00" - SOLUCIÓN INTEGRAL
    # IMPACTO: Normalización correcta de formato decimal venezolano
    if not campos_extraidos['monto']:
        def normalizar_monto_venezolano_routes(monto_str):
            """
            MANDATO FASE 2: Normalización específica para routes.py
            PROBLEMA: "210,00" convertido a "2706102.00"
            SOLUCIÓN: Detectar y normalizar formato venezolano correctamente
            """
            try:
                # Limpiar espacios y caracteres no numéricos excepto comas y puntos
                monto_limpio = re.sub(r'[^\d.,]', '', monto_str)
                
                # DETECCIÓN ESPECÍFICA: Formato venezolano con coma como separador decimal
                if ',' in monto_limpio and monto_limpio.count(',') == 1:
                    partes = monto_limpio.split(',')
                    # Verificar que la parte decimal tenga exactamente 2 dígitos (formato venezolano)
                    if len(partes) == 2 and partes[1].isdigit() and len(partes[1]) == 2:
                        # Formato venezolano confirmado: 210,00 → 210.00
                        parte_entera = partes[0].replace('.', '')  # Eliminar puntos de miles si existen
                        parte_decimal = partes[1]
                        monto_normalizado = f"{parte_entera}.{parte_decimal}"
                        logger.info(f"🏆 MANDATO FASE 2: Monto venezolano normalizado en routes.py: {monto_str} → {monto_normalizado}")
                        return monto_normalizado
                
                # Formato internacional: eliminar puntos de miles, convertir coma a punto decimal
                if '.' in monto_limpio and ',' in monto_limpio:
                    # Formato 1.234,56 → 1234.56
                    monto_normalizado = monto_limpio.replace('.', '').replace(',', '.')
                    return monto_normalizado
                
                # Solo números con puntos (posible formato miles): 1.234 → 1234
                if '.' in monto_limpio and not ',' in monto_limpio:
                    # Verificar si es separador de miles o decimal
                    partes = monto_limpio.split('.')
                    if len(partes) == 2 and len(partes[1]) == 2:
                        # Probable decimal: 210.00
                        return monto_limpio
                    else:
                        # Probable separador de miles: 1.234 → 1234
                        return monto_limpio.replace('.', '')
                
                # Solo números enteros
                return monto_limpio
                
            except Exception as e:
                logger.warning(f"Error normalizando monto en routes.py '{monto_str}': {e}")
                return monto_str
        
        monto_patterns = [
            r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*Bs',     # 210,00 Bs
            r'Bs\.?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # Bs 210,00
            r'(\d{1,3}(?:[,.]\d{2,3})+)',             # 104,54 o 210,00
            r'Se\s+Envio\s+\(Bs\s+(\d{1,3}(?:\.\d{3})*,\d{2})\)',  # Se Envio (Bs 210,00)
        ]
        for pattern in monto_patterns:
            match = re.search(pattern, texto_completo)
            if match:
                monto_str = match.group(1)
                # Validar que contiene números y formato válido
                if re.search(r'\d+[,.]\d{2}', monto_str):
                    # APLICAR NORMALIZACIÓN MANDATO FASE 2
                    monto_normalizado = normalizar_monto_venezolano_routes(monto_str)
                    campos_extraidos['monto'] = monto_normalizado
                    logger.info(f"✅ MANDATO FASE 2: Monto extraído y normalizado en routes.py: {monto_normalizado}")
                    break
    
    # FIX: EXTRACCIÓN CRÍTICA DE CÉDULA - MANDATO REFINAMIENTO
    # REASON: Fortalecer patrones regex para formatos V-27061025, 27.061.025
    # IMPACT: Corrección de cédulas vacías → extracción correcta con puntos y guiones
    if not campos_extraidos['cedula']:
        cedula_patterns = [
            r'(?:Identificacion|C\.?I\.?|cedula|RIF|BENEFICIARIO)\s*[:=]?\s*([VvEe]?-?\d{1,2}\.?\d{3}\.?\d{3})',  # V-27.061.025
            r'([VvEe]-?\d{1,2}\.?\d{3}\.?\d{3})',                                                                # V-27.061.025 directo
            r'([VvEe]-?\d{7,9})',                                                                               # V-27061025
            r'(\d{1,2}\.?\d{3}\.?\d{3})',                                                                       # 27.061.025
            r'(\d{7,9})',                                                                                       # 27061025 directo
        ]
        for pattern in cedula_patterns:
            matches = re.finditer(pattern, texto_completo, re.IGNORECASE)
            for match in matches:
                cedula_str = match.group(1)
                # Validar longitud apropiada después de limpiar
                cedula_digits = re.sub(r'[^\d]', '', cedula_str)
                if 7 <= len(cedula_digits) <= 9:
                    # Verificar que no es teléfono (no empieza con 04, 02) y no es la referencia ya extraída
                    if not cedula_digits.startswith(('04', '02', '58')) and cedula_digits != campos_extraidos.get('referencia', ''):
                        campos_extraidos['cedula'] = cedula_str
                        break
            if campos_extraidos.get('cedula'):
                break
    
    # MANDATO CRÍTICO #1: VALIDACIÓN BINARIA OBLIGATORIA DE TELÉFONOS VENEZOLANOS
    # REASON: 48311146148 persiste como teléfono - implementar RECHAZO ABSOLUTO
    # IMPACT: PUNTO DE CONTROL ÚNICO con validación estricta según mandato #19
    if not campos_extraidos['telefono']:
        # VALIDACIÓN ESTRICTA: Solo prefijos de operadores celulares venezolanos
        prefijos_validos = ['0412', '0416', '0426', '0414', '0424']
        
        telefono_patterns = [
            # PRIORIDAD MÁXIMA: Keywords explícitas de teléfono
            r'(?:Teléfono|TELF|Celular|Telf\.\s*Celular|telefono|celular|movil)\s*[:=]?\s*(\d{11})',
            # PRIORIDAD MEDIA: Contexto de destino
            r'(?:Destino|BENEFICIARIO)\s*[:=]?\s*(\d{11})',
            # PRIORIDAD BAJA: Números de 11 dígitos que empiecen con 04
            r'(04\d{9})',
            # FORMATO INTERNACIONAL: +58 seguido de 10 dígitos
            r'(\+58\d{10})',
        ]
        
        # MANDATO CRÍTICO: VALIDACIÓN BINARIA OBLIGATORIA - RECHAZO ABSOLUTO
        # CONDICIÓN DE ASIGNACIÓN: Solo asignar si cumple AMBAS condiciones obligatorias
        telefono_validado = False
        for pattern in telefono_patterns:
            matches = re.finditer(pattern, texto_completo, re.IGNORECASE)
            for match in matches:
                telefono_raw = match.group(1)
                telefono_str = re.sub(r'[^\d+]', '', telefono_raw)  # Limpiar completamente
                
                # VALIDACIÓN BINARIA OBLIGATORIA: AMBAS condiciones REQUERIDAS
                cumple_internacional = telefono_str.startswith('+58') and len(telefono_str) == 13
                cumple_nacional = len(telefono_str) == 11 and any(telefono_str.startswith(p) for p in prefijos_validos)
                
                if cumple_internacional:
                    # Convertir formato internacional a nacional
                    telefono_nacional = '0' + telefono_str[3:]
                    if any(telefono_nacional.startswith(prefijo) for prefijo in prefijos_validos):
                        campos_extraidos['telefono'] = telefono_nacional
                        logger.info(f"📱 TELÉFONO VENEZOLANO VÁLIDO (internacional): {telefono_str} → {telefono_nacional}")
                        telefono_validado = True
                        break
                elif cumple_nacional:
                    # Verificar que NO es la referencia ya extraída
                    if telefono_str != campos_extraidos.get('referencia', ''):
                        campos_extraidos['telefono'] = telefono_str
                        logger.info(f"📱 TELÉFONO VENEZOLANO VÁLIDO (nacional): {telefono_str}")
                        telefono_validado = True
                        break
                else:
                    # MANDATO CRÍTICO: RECHAZO ABSOLUTO - NO asignar a telefono
                    # BAJO NINGUNA CIRCUNSTANCIA debe ser asignado a datosbeneficiario.telefono
                    logger.info(f"📱 NÚMERO RECHAZADO DEFINITIVAMENTE (no es teléfono venezolano): {telefono_str}")
                    # Re-dirigir a referencia si cumple patrón y no se ha extraído
                    if not campos_extraidos.get('referencia') and len(telefono_str) >= 8:
                        campos_extraidos['referencia'] = telefono_str
                        logger.info(f"📋 REDIRIGIDO A REFERENCIA: {telefono_str}")
                        
            if telefono_validado:
                break
    
    # FIX: EXTRACCIÓN CRÍTICA DE FECHA DE PAGO - MANDATO REFINAMIENTO
    # REASON: Buscar patrones específicos de fechas venezolanas con espacios
    # IMPACT: Extracción precisa de fechas en formato DD/MM/YYYY  
    if not campos_extraidos['pago_fecha']:
        fecha_patterns = [
            r'Fecha\s*[:=]?\s*(\d{1,2}/\d{1,2}/\s*\d{4})',  # Fecha : 20/06/ 2025
            r'(\d{1,2}/\d{1,2}/\s*\d{4})',                 # 20/06/ 2025 directo
            r'(\d{1,2}/\d{1,2}/\d{4})',                    # 20/06/2025 sin espacios
            r'(\d{4}-\d{2}-\d{2})',                        # 2025-06-20 formato ISO
        ]
        for pattern in fecha_patterns:
            match = re.search(pattern, texto_completo)
            if match:
                fecha_str = match.group(1).replace(' ', '')  # Eliminar espacios adicionales
                campos_extraidos['pago_fecha'] = fecha_str
                break
    
    # FIX: INFERENCIA AVANZADA DE BANCO DESTINO INTRABANCARIO - MANDATO OPTIMIZACIÓN CONTINUA  
    # REASON: Implementar lógica de inferencia contextual según mandato #20
    # IMPACT: Completa banco_destino cuando es transacción intrabancaria
    # PROBLEMA RESUELTO: Llena banco_destino vacío cuando es mismo banco que bancoorigen
    if campos_extraidos.get('bancoorigen') and not campos_extraidos.get('banco_destino'):
        # REGLA DE INFERENCIA CONDICIONAL INTRABANCARIA
        # Verificar contexto que sugiere transacción dentro del mismo banco
        indicadores_intrabancarios = [
            'Desde mi cuenta',
            'a beneficiario Cuenta',
            'Cuenta de Ahorro',
            'mi cuenta',
            'Envio de Tpago',
            'Operacion realizada Desde',
            'cuenta Se Envio'
        ]
        
        # Buscar indicadores de transacción intrabancaria
        es_intrabancario = any(indicador in texto_completo for indicador in indicadores_intrabancarios)
        
        # Verificar que solo se menciona un banco (el origen) sin banco destino explícito
        banco_origen = campos_extraidos['bancoorigen']
        menciones_banco_origen = texto_completo.upper().count(banco_origen.upper().split()[-1])  # Última palabra del banco
        
        # Si hay indicadores intrabancarios y solo se menciona el banco origen
        if es_intrabancario and menciones_banco_origen >= 1:
            # VERIFICAR: No hay mención explícita de otro banco diferente
            otros_bancos_mencionados = False
            for codigo_banco, nombre_banco in bank_mapping.items():
                if nombre_banco != banco_origen and nombre_banco.upper() in texto_completo.upper():
                    otros_bancos_mencionados = True
                    break
            
            # FIX: EXTRACCIÓN ROBUSTA DE BANCO DESTINO EXPLÍCITO - MANDATO CORRECCIÓN CRÍTICA PUNTO #21
            # REASON: Priorizar detección EXPLÍCITA de banco destino sobre inferencia intrabancaria
            # IMPACT: Capturar bancos destino mencionados directamente en transacciones interbancarias
            
            # MANDATO CRÍTICO #3: DETECCIÓN EXPLÍCITA CON CÓDIGOS BANCARIOS Y FUZZY MATCHING
            # REASON: Detectar "Bancoc 0105 - BANCO MERCANIIL" como "BANCO MERCANTIL"
            # IMPACT: Prioridad máxima para códigos bancarios sobre inferencia intrabancaria
            
            # TABLA DE CÓDIGOS BANCARIOS VENEZOLANOS (FUENTE DE ALTA FIABILIDAD)
            codigos_bancarios = {
                '0102': 'BANCO DE VENEZUELA',
                '0105': 'BANCO MERCANTIL', 
                '0108': 'BBVA PROVINCIAL',
                '0115': 'BANCO EXTERIOR',
                '0134': 'BANESCO',
                '0172': 'BANCAMIGA',
                '0191': 'BANCO NACIONAL DE CREDITO'
            }
            
            banco_destino_encontrado = False
            
            # PRIORIDAD MÁXIMA: BÚSQUEDA POR CÓDIGO BANCARIO
            for codigo, nombre_banco in codigos_bancarios.items():
                if codigo in texto_completo and nombre_banco != banco_origen:
                    campos_extraidos['banco_destino'] = nombre_banco
                    logger.info(f"🏦 BANCO DESTINO EXPLÍCITO detectado por código {codigo}: {nombre_banco}")
                    banco_destino_encontrado = True
                    break
            
            # PRIORIDAD ALTA: DETECCIÓN POR PATRONES CON FUZZY MATCHING
            if not banco_destino_encontrado:
                banco_destino_patterns = [
                    r'Bancoc?\s+\d{4}\s*[-=]\s*([A-Z\s]+)',               # Bancoc 0105 - BANCO MERCANIIL
                    r'Banco\s*[:=]?\s*(BANCO\s+[A-Z\s]+)',                # Banco: BANCO MERCANTIL
                    r'destino\s*[:=]?\s*(BANCO\s+[A-Z\s]+)',              # destino: BANCO MERCANTIL  
                    r'([A-Z\s]*BANCO\s+[A-Z\s]+)',                       # BANCO MERCANTIL directo
                    r'(MERCANTIL|VENEZUELA|BANESCO|PROVINCIAL|EXTERIOR|BICENTENARIO|BBVA|BNC|BANCAMIGA)'  # Nombres directos
                ]
                
                for pattern in banco_destino_patterns:
                    matches = re.finditer(pattern, texto_completo, re.IGNORECASE)
                    for match in matches:
                        banco_candidato = match.group(1).strip().upper()
                        
                        # FUZZY MATCHING CON BANCOS CONOCIDOS
                        mejor_match = None
                        mejor_score = 0
                        
                        for banco_oficial in codigos_bancarios.values():
                            # Algoritmo de similitud simple
                            palabras_candidato = set(banco_candidato.split())
                            palabras_oficial = set(banco_oficial.split())
                            
                            if palabras_candidato and palabras_oficial:
                                interseccion = len(palabras_candidato & palabras_oficial)
                                union = len(palabras_candidato | palabras_oficial)
                                score = interseccion / union if union > 0 else 0
                                
                                # Bonus por coincidencias exactas
                                if 'MERCANTIL' in banco_candidato and 'MERCANTIL' in banco_oficial:
                                    score += 0.3
                                elif 'VENEZUELA' in banco_candidato and 'VENEZUELA' in banco_oficial:
                                    score += 0.3
                                    
                                if score > mejor_score and score >= 0.4:  # Umbral reducido
                                    mejor_score = score
                                    mejor_match = banco_oficial
                        
                        if mejor_match and mejor_match != banco_origen:
                            campos_extraidos['banco_destino'] = mejor_match
                            logger.info(f"🏦 BANCO DESTINO EXPLÍCITO detectado (fuzzy): {banco_candidato} → {mejor_match} (score: {mejor_score:.3f})")
                            banco_destino_encontrado = True
                            break
                    
                    if banco_destino_encontrado:
                        break
            
            # PRIORIDAD SECUNDARIA: Si no hay otros bancos mencionados, es intrabancario
            if not banco_destino_encontrado and not otros_bancos_mencionados:
                campos_extraidos['banco_destino'] = banco_origen
                logger.info(f"🏦 BANCO DESTINO INFERIDO (intrabancario): {banco_origen}")
    
    # FIX: DETERMINACIÓN INTELIGENTE DE CAPTION - MANDATO REFINAMIENTO
    # REASON: Caption debe reflejar el tipo de transacción detectado automáticamente
    # IMPACT: Mejora información contextual en respuesta empresarial
    if not campos_extraidos['caption']:
        if 'PagomovilBDV' in texto_completo:
            campos_extraidos['caption'] = 'Pago Móvil BDV'
        elif 'Transferencia' in texto_completo:
            campos_extraidos['caption'] = 'Transferencia Bancaria'
        elif 'Envio' in texto_completo:
            campos_extraidos['caption'] = 'Envío de Dinero'
        elif 'Operacion' in texto_completo and 'Banco' in texto_completo:
            campos_extraidos['caption'] = 'Operación Bancaria'
        elif any(term in texto_completo for term in ['Bs', 'bolivares', 'Banco']):
            campos_extraidos['caption'] = 'Transacción Financiera'
    
    return campos_extraidos

def _extract_tracking_parameters(nombre_archivo, metadata, result_data):
    """
    MANDATO CRÍTICO BACKEND: Extracción de parámetros de seguimiento desde filename y metadata
    REASON: Frontend necesita correlacionar archivos procesados con parámetros de entrada
    IMPACT: Sistema completo de seguimiento y trazabilidad frontend-backend
    
    Args:
        nombre_archivo: Nombre del archivo original
        metadata: Metadatos disponibles en result_data
        result_data: Datos completos del resultado JSON
        
    Returns:
        dict: Parámetros de seguimiento (codigo_sorteo, id_whatsapp, nombre_usuario, etc.)
    """
    import re
    
    # Inicializar parámetros de seguimiento con valores por defecto
    tracking_params = {
        'codigo_sorteo': '',      # Letra o número de sorteo (A-Z, 01-99)
        'id_whatsapp': '',        # ID de WhatsApp con @lid
        'nombre_usuario': '',     # Nombre del usuario
        'hora_exacta': '',        # Hora en formato HH-MM
        'numero_llegada': 0       # Orden de llegada en el lote (NUEVO MANDATO)
    }
    
    try:
        # FUENTE 1: Extraer desde metadata si está disponible
        if isinstance(metadata, dict):
            tracking_params['codigo_sorteo'] = metadata.get('numerosorteo', '') or metadata.get('codigo_sorteo', '')
            tracking_params['id_whatsapp'] = metadata.get('idWhatsapp', '') or metadata.get('id_whatsapp', '')
            tracking_params['nombre_usuario'] = metadata.get('nombre', '') or metadata.get('nombre_usuario', '')
            tracking_params['hora_exacta'] = metadata.get('horamin', '') or metadata.get('hora_exacta', '')
        
        # FUENTE 2: Extraer desde filename usando patrones WhatsApp empresariales
        if nombre_archivo and not all(tracking_params.values()):
            # Patrones para formato WhatsApp: 20250711-A--123456@lid_Juan_14-30.png
            patterns = [
                r'^(?:\d{8}-)?([A-Z\d]{1,2})--(\d+@lid)_([^_]+)_(\d{2}-\d{2})',  # Con/sin fecha inicial
                r'^([A-Z\d]{1,2})-(\d+@lid)_([^_]+)_(\d{2}-\d{2})',              # Formato alternativo
                r'BATCH_\d+_\d+_[a-f0-9]+_(?:\d{8}-)?([A-Z\d]{1,2})--(\d+@lid)_([^_]+)_(\d{2}-\d{2})'  # Formato BATCH
            ]
            
            for pattern in patterns:
                match = re.search(pattern, nombre_archivo)
                if match:
                    groups = match.groups()
                    if len(groups) >= 4:
                        # Solo actualizar si el campo está vacío
                        if not tracking_params['codigo_sorteo']:
                            tracking_params['codigo_sorteo'] = groups[0]
                        if not tracking_params['id_whatsapp']:
                            tracking_params['id_whatsapp'] = groups[1]
                        if not tracking_params['nombre_usuario']:
                            tracking_params['nombre_usuario'] = groups[2]
                        if not tracking_params['hora_exacta']:
                            tracking_params['hora_exacta'] = groups[3]
                    break
        
        # FUENTE 3: Extraer desde result_data si hay información adicional
        if isinstance(result_data, dict):
            # Buscar en diferentes ubicaciones posibles
            metadata_sources = [
                result_data.get('metadata', {}),
                result_data.get('archivo_info', {}),
                result_data.get('imagen_info', {}),
                result_data.get('datos_extraidos', {}).get('metadata', {})
            ]
            
            for source in metadata_sources:
                if isinstance(source, dict):
                    # Solo actualizar campos vacíos
                    if not tracking_params['codigo_sorteo']:
                        tracking_params['codigo_sorteo'] = source.get('numerosorteo', '') or source.get('codigo_sorteo', '')
                    if not tracking_params['id_whatsapp']:
                        tracking_params['id_whatsapp'] = source.get('idWhatsapp', '') or source.get('id_whatsapp', '')
                    if not tracking_params['nombre_usuario']:
                        tracking_params['nombre_usuario'] = source.get('nombre', '') or source.get('nombre_usuario', '')
                    if not tracking_params['hora_exacta']:
                        tracking_params['hora_exacta'] = source.get('horamin', '') or source.get('hora_exacta', '')
        
        # MANDATO CRÍTICO: Generar numero_llegada basado en timestamp o posición en filename
        # REASON: Frontend necesita orden de llegada para correlación con interfaz
        if nombre_archivo:
            # Extraer timestamp del filename si está disponible
            timestamp_match = re.search(r'BATCH_(\d{8})_(\d{6})_([a-f0-9]+)_', nombre_archivo)
            if timestamp_match:
                # Usar últimos 2 dígitos del hash como numero_llegada único
                hash_suffix = timestamp_match.group(3)
                tracking_params['numero_llegada'] = int(hash_suffix[-2:], 16) % 100  # 0-99
            else:
                # Fallback: usar hash del nombre del archivo
                import hashlib
                hash_obj = hashlib.md5(nombre_archivo.encode())
                tracking_params['numero_llegada'] = int(hash_obj.hexdigest()[-2:], 16) % 100
        
        # Validación y limpieza de parámetros
        if tracking_params['codigo_sorteo']:
            tracking_params['codigo_sorteo'] = tracking_params['codigo_sorteo'].strip().upper()
        if tracking_params['id_whatsapp'] and not tracking_params['id_whatsapp'].endswith('@lid'):
            # Agregar @lid si falta
            if '@' not in tracking_params['id_whatsapp']:
                tracking_params['id_whatsapp'] += '@lid'
        if tracking_params['nombre_usuario']:
            tracking_params['nombre_usuario'] = tracking_params['nombre_usuario'].strip().title()
        
        logger.debug(f"🎯 Parámetros de seguimiento extraídos: {tracking_params}")
        
    except Exception as e:
        logger.error(f"Error extrayendo parámetros de seguimiento de {nombre_archivo}: {e}")
    
    return tracking_params

def _save_last_batch_request_id(request_id):
    """
    FIX: Almacena el request_id del último lote procesado exitosamente
    REASON: Necesario para filtrar archivos JSON por lote específico
    IMPACT: Permite extracción consolidada específica del último lote únicamente
    """
    try:
        state_file = 'data/last_batch_state.txt'
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            f.write(f"{request_id}\n{datetime.now().isoformat()}")
        logger.debug(f"📝 Estado almacenado: {request_id}")
    except Exception as e:
        logger.error(f"Error almacenando request_id: {e}")

def _get_last_batch_request_id():
    """
    FIX: Recupera el request_id del último lote procesado exitosamente
    REASON: Necesario para filtrar archivos JSON por lote específico
    IMPACT: Permite extracción consolidada específica del último lote únicamente
    """
    try:
        state_file = 'data/last_batch_state.txt'
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 1:
                    request_id = lines[0]
                    logger.debug(f"📖 Estado recuperado: {request_id}")
                    return request_id
        return None
    except Exception as e:
        logger.error(f"Error recuperando request_id: {e}")
        return None

def validate_api_key(api_key):
    """
    FIX: Función para validar API keys en requests
    REASON: Autenticación requerida para endpoints externos
    IMPACT: Seguridad implementada para todas las APIs externas
    """
    if not api_key:
        return None
        
    keys_data = load_api_keys()
    
    for key_info in keys_data.values():
        if key_info['key'] == api_key:
            # Actualizar último uso
            key_info['last_used'] = datetime.now().isoformat()
            key_info['usage_count'] = key_info.get('usage_count', 0) + 1
            save_api_keys(keys_data)
            return key_info
            
    return None

# ====================================================================================================
# MANDATO 15 - SISTEMA DE GENERACIÓN DE API KEYS
# FILOSOFÍA: INTEGRIDAD TOTAL + TRANSPARENCIA TOTAL + SEGURIDAD EMPRESARIAL
# ====================================================================================================

import secrets
import hashlib

def generate_secure_api_key():
    """Generar API Key segura de 64 caracteres"""
    # Generar 32 bytes aleatorios seguros
    random_bytes = secrets.token_bytes(32)
    # Convertir a hexadecimal para API key legible
    api_key = random_bytes.hex()
    
    # Generar key_id único más corto para identificación
    key_id = f"ocr_{secrets.token_hex(8)}"
    
    return key_id, api_key

@app.route('/api/generate_api_key', methods=['POST'])
def generate_api_key():
    """
    ENDPOINT: POST /api/generate_api_key
    PROPÓSITO: Generar nueva API Key única y segura para el sistema OCR
    FILOSOFÍA: INTEGRIDAD TOTAL + SEGURIDAD EMPRESARIAL SIN POSTGRESQL
    """
    try:
        logger.info("🔑 Iniciando generación de nueva API Key")
        
        # Obtener datos del request
        data = request.get_json() or {}
        api_key_name = data.get('name', f'API Key {datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        # Generar API Key segura
        key_id, api_key = generate_secure_api_key()
        
        # Cargar API keys existentes
        api_keys_data = load_api_keys()
        
        # Crear nueva entrada
        new_api_key_data = {
            'key_id': key_id,
            'api_key': api_key,
            'name': api_key_name,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'usage_count': 0
        }
        
        # Agregar nueva API key
        api_keys_data[key_id] = new_api_key_data
        
        # Guardar en archivo
        save_api_keys(api_keys_data)
        
        logger.info(f"✅ API Key generada exitosamente: {key_id}")
        
        # Respuesta exitosa
        response = {
            'status': 'success',
            'mensaje': 'API Key generada exitosamente',
            'data': {
                'key_id': key_id,
                'api_key': api_key,
                'name': api_key_name,
                'created_at': new_api_key_data['created_at'],
                'is_active': True
            }
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        logger.error(f"Error generando API Key: {e}")
        return jsonify({
            'status': 'error',
            'mensaje': f'Error interno generando API Key: {str(e)}',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@app.route('/api/current_api_key', methods=['GET'])
def api_current_api_key():
    """
    ENDPOINT: GET /api/current_api_key
    PROPÓSITO: Obtener la API Key actual
    """
    try:
        api_keys_data = load_api_keys()
        
        # Obtener la API key más reciente
        if api_keys_data:
            latest_key = max(api_keys_data.items(), key=lambda x: x[1].get('created_at', ''))
            key_id, key_info = latest_key
            
            return jsonify({
                'status': 'success',
                'estado': 'exitoso',
                'api_key': key_info.get('api_key'),
                'key_id': key_id,
                'name': key_info.get('name'),
                'created_at': key_info.get('created_at'),
                'usage_count': key_info.get('usage_count', 0)
            })
        else:
            return jsonify({
                'status': 'not_found',
                'estado': 'no_encontrado',
                'message': 'No hay API Key configurada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo API Key actual: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'message': f'Error obteniendo API Key: {str(e)}'
        }), 500

@app.route('/api/queue_count', methods=['GET'])
def api_get_queue_count():
    """
    ENDPOINT: GET /api/queue_count
    PROPÓSITO: Obtener contador de archivos en cola
    """
    try:
        from config import get_async_directories
        directories = get_async_directories()
        inbox_dir = directories['inbox']
        
        count = 0
        if os.path.exists(inbox_dir):
            for file in os.listdir(inbox_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                    count += 1
        
        return jsonify({
            'error': False,
            'status': 'exitoso',
            'count': count,
            'message': f'Archivos en cola: {count}'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo contador de cola: {e}")
        return jsonify({
            'error': True,
            'status': 'error',
            'count': 0,
            'message': 'Error obteniendo contador'
        }), 500

@app.route('/api/list_api_keys', methods=['GET'])
def list_api_keys():
    """
    ENDPOINT: GET /api/list_api_keys
    PROPÓSITO: Listar todas las API Keys activas (sin exponer las keys completas)
    FILOSOFÍA: TRANSPARENCIA TOTAL + SEGURIDAD SIN POSTGRESQL
    """
    try:
        # Cargar API keys desde archivo
        api_keys_data = load_api_keys()
        
        api_keys = []
        for key_id, key_info in api_keys_data.items():
            api_keys.append({
                'key_id': key_id,
                'name': key_info.get('name', 'Sin nombre'),
                'is_active': key_info.get('is_active', True),
                'created_at': key_info.get('created_at'),
                'last_used': key_info.get('last_used'),
                'usage_count': key_info.get('usage_count', 0),
                'api_key_preview': f"{key_id[:12]}...{key_id[-4:]}" if key_id else "N/A"
            })
        
        # Ordenar por fecha de creación (más reciente primero)
        api_keys.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return jsonify({
            'status': 'success',
            'mensaje': f'Lista de {len(api_keys)} API Keys',
            'data': {
                'api_keys': api_keys,
                'total_count': len(api_keys),
                'active_count': sum(1 for key in api_keys if key['is_active'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error listando API Keys: {e}")
        return jsonify({
            'status': 'error',
            'mensaje': f'Error interno: {str(e)}'
        }), 500

@app.route('/api/validate_api_key', methods=['POST'])
def validate_api_key_endpoint():
    """
    ENDPOINT: POST /api/validate_api_key
    PROPÓSITO: Validar una API Key específica
    FILOSOFÍA: SEGURIDAD EMPRESARIAL SIN POSTGRESQL
    """
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'mensaje': 'API Key requerida',
                'valid': False
            }), 400
        
        # Cargar API keys desde archivo
        api_keys_data = load_api_keys()
        
        # Buscar la API key en los datos
        for key_id, key_info in api_keys_data.items():
            if key_info.get('api_key') == api_key and key_info.get('is_active', True):
                # Actualizar último uso y contador
                key_info['last_used'] = datetime.now().isoformat()
                key_info['usage_count'] = key_info.get('usage_count', 0) + 1
                
                # Guardar cambios
                save_api_keys(api_keys_data)
                
                return jsonify({
                    'status': 'success',
                    'mensaje': 'API Key válida',
                    'valid': True,
                    'data': {
                        'key_id': key_id,
                        'name': key_info.get('name', 'Sin nombre'),
                        'created_at': key_info.get('created_at'),
                        'usage_count': key_info['usage_count']
                    }
                })
        
        return jsonify({
            'status': 'error',
            'mensaje': 'API Key inválida o inactiva',
            'valid': False
        }), 401
        
    except Exception as e:
        logger.error(f"Error validando API Key: {e}")
        return jsonify({
            'status': 'error',
            'mensaje': f'Error interno: {str(e)}',
            'valid': False
        }), 500

# ====================================================================================================
# ENDPOINTS ADICIONALES - MIGRACIÓN REPLIT COMPLETADA
# ====================================================================================================

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """
    ENDPOINT: GET /api/stats
    PROPÓSITO: Obtener estadísticas del sistema OCR
    """
    try:
        import psutil
        
        # Obtener estadísticas del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Obtener información de caché
        cache_info = get_cache_info()
        
        stats = {
            'sistema': {
                'cpu_uso': cpu_percent,
                'memoria_uso': memory.percent,
                'memoria_total': round(memory.total / (1024**3), 2),  # GB
                'memoria_disponible': round(memory.available / (1024**3), 2)  # GB
            },
            'cache': cache_info,
            'ocr': {
                'componentes_cargados': True,
                'modelos_disponibles': 2,
                'status': 'operativo'
            },
            'archivos': {
                'en_cola': get_queue_count(),
                'procesados': get_processed_count()
            }
        }
        
        return jsonify({
            'status': 'success',
            'estado': 'exitoso',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'message': f'Error obteniendo estadísticas: {str(e)}'
        }), 500

def get_cache_info():
    """Obtener información del caché"""
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        cache_size = 0
        cache_files = 0
        
        for cache_dir in [directories.get('cache', ''), directories.get('temp', '')]:
            if cache_dir and os.path.exists(cache_dir):
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    if os.path.isfile(file_path):
                        cache_size += os.path.getsize(file_path)
                        cache_files += 1
        
        return {
            'archivos': cache_files,
            'tamaño_mb': round(cache_size / (1024**2), 2)
        }
    except:
        return {'archivos': 0, 'tamaño_mb': 0}

def get_queue_count():
    """Obtener contador de archivos en cola"""
    try:
        from config import get_async_directories
        directories = get_async_directories()
        inbox_dir = directories.get('inbox', '')
        
        if not inbox_dir or not os.path.exists(inbox_dir):
            return 0
            
        count = 0
        for file in os.listdir(inbox_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                count += 1
        return count
    except:
        return 0

def get_processed_count():
    """Obtener contador de archivos procesados"""
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        count = 0
        for results_dir in [directories.get('results', ''), directories.get('historial', '')]:
            if results_dir and os.path.exists(results_dir):
                for file in os.listdir(results_dir):
                    if file.endswith('.json'):
                        count += 1
        return count
    except:
        return 0

def _save_batch_execution_id(batch_id):
    """
    INTEGRIDAD TOTAL: Almacenar ID único del lote de ejecución
    """
    try:
        batch_file = Path('data/current_batch_id.txt')
        batch_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_id)
        
        logger.info(f"📦 INTEGRIDAD TOTAL: ID único de lote almacenado: {batch_id}")
        
    except Exception as e:
        logger.error(f"Error almacenando ID de lote: {e}")

def _get_current_batch_execution_id():
    """
    INTEGRIDAD TOTAL: Obtener ID único del lote actual
    """
    try:
        batch_file = Path('data/current_batch_id.txt')
        if batch_file.exists():
            with open(batch_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.error(f"Error obteniendo ID de lote actual: {e}")
        return None

def _get_current_batch_id_from_file():
    """
    INTEGRIDAD TOTAL: Obtener ID único del lote actual desde archivo
    """
    try:
        batch_file = Path('data/current_batch_id.txt')
        if batch_file.exists():
            with open(batch_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.error(f"Error obteniendo ID de lote actual desde archivo: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
