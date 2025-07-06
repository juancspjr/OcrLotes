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
    """Página principal del dashboard simplificado"""
    return render_template('dashboard_simple.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal del sistema OCR"""
    return render_template('dashboard_simple.html')

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
        }), 500

@app.route('/api/ocr/process_image', methods=['POST'])
def api_process_image():
    """
    FIX: Endpoint corregido con formato exacto de renombrado solicitado por el usuario
    REASON: Usuario necesita formato específico "Posición Sorteo"-"Fecha Sorteo"--"Sender ID"_"Hora (HH:MM)".png
    IMPACT: Archivos organizados con nombres exactos según especificación
    """
    try:
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'mensaje': 'No se proporcionó ninguna imagen',
                'message': 'No image provided'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'mensaje': 'Archivo vacío',
                'message': 'Empty file'
            }), 400
        
        # Obtener datos del formulario para renombrado
        custom_filename = request.form.get('custom_filename')
        posicion_sorteo = request.form.get('posicion_sorteo', '')
        fecha_sorteo = request.form.get('fecha_sorteo', '')
        sender_id = request.form.get('sender_id', '')
        hora_formato = request.form.get('hora_formato', '')
        
        # Generar timestamp único
        current_time = datetime.now()
        timestamp_id = current_time.strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        # Usar nombre personalizado si se proporciona
        if custom_filename and all([posicion_sorteo, fecha_sorteo, sender_id, hora_formato]):
            # Validar formato
            if not custom_filename.endswith(('.png', '.jpg', '.jpeg')):
                return jsonify({
                    'status': 'error',
                    'mensaje': 'Formato de archivo no válido',
                    'message': 'Invalid file format'
                }), 400
            
            # Usar nombre exacto del usuario + timestamp para evitar duplicados
            file_ext = custom_filename.rsplit('.', 1)[1]
            final_filename = f"{custom_filename.rsplit('.', 1)[0]}_{timestamp_id}.{file_ext}"
        else:
            # Nombre por defecto si no hay datos personalizados
            file_ext = file.filename.rsplit('.', 1)[1] if '.' in file.filename else 'png'
            final_filename = f"image_{timestamp_id}.{file_ext}"
        
        # Request ID basado en el nombre final
        request_id = final_filename.replace(f'_{timestamp_id}', '').replace(f'.{file_ext}', f'_{timestamp_id}')
        
        # Obtener directorios
        from config import get_async_directories
        directories = get_async_directories()
        
        # Guardar archivo
        file_path = os.path.join(directories['inbox'], final_filename)
        file.save(file_path)
        
        # Metadatos completos
        metadata = {
            'filename_original': file.filename,
            'filename_custom': custom_filename or final_filename,
            'filename_final': final_filename,
            'request_id': request_id,
            'upload_timestamp': current_time.isoformat(),
            'file_size': os.path.getsize(file_path),
            'renaming_info': {
                'posicion_sorteo': posicion_sorteo,
                'fecha_sorteo': fecha_sorteo,
                'sender_id': sender_id,
                'hora_formato': hora_formato,
                'formato_aplicado': bool(custom_filename)
            }
        }
        
        # Guardar metadatos
        metadata_path = file_path.replace(f'.{file_ext}', '.metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Imagen encolada con nombre personalizado: {final_filename}")
        
        return jsonify({
            'status': 'accepted',
            'estado': 'aceptado',
            'message': 'Image queued for processing',
            'mensaje': 'Imagen encolada para procesamiento',
            'request_id': request_id,
            'filename_original': file.filename,
            'filename_custom': final_filename,
            'check_result_endpoint': f'/api/ocr/result/{request_id}',
            'batch_process_endpoint': '/api/ocr/process_batch',
            'queue_position': 'pending',
            'metadata': metadata
        }), 202
        
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
    """Procesar lote de imágenes bajo demanda"""
    try:
        # Obtener configuración
        data = request.get_json() or {}
        profile = data.get('profile', 'ultra_rapido')
        batch_size = data.get('batch_size', 5)
        
        # Inicializar orquestador
        orquestador = OrquestadorOCR()
        
        # Procesar lote
        resultado = orquestador.process_queue_batch(
            max_files=batch_size,
            profile=profile
        )
        
        logger.info(f"✅ Lote procesado: {resultado.get('batch_info', {}).get('processed_count', 0)} éxitos")
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Error procesando lote: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error al procesar el lote: {str(e)}',
            'message': f'Batch processing error: {str(e)}'
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
    """Estado de la cola de procesamiento"""
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        # Contar archivos en cada directorio
        inbox_count = len([f for f in os.listdir(directories['inbox']) if f.endswith(('.png', '.jpg', '.jpeg'))])
        processing_count = len([f for f in os.listdir(directories['processing']) if f.endswith(('.png', '.jpg', '.jpeg'))])
        processed_count = len([f for f in os.listdir(directories['processed']) if f.endswith(('.png', '.jpg', '.jpeg'))])
        results_count = len([f for f in os.listdir(directories['results']) if f.endswith('.json')])
        
        return jsonify({
            'status': 'ok',
            'estado': 'exitoso',
            'queue_status': {
                'pending': inbox_count,
                'processing': processing_count,
                'completed': processed_count,
                'results_available': results_count
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

@app.route('/api/ocr/clean_queue', methods=['POST'])
def api_clean_queue():
    """Limpiar cola de procesamiento"""
    try:
        from config import get_async_directories
        directories = get_async_directories()
        
        # Limpiar directorios
        removed_files = 0
        for dir_name in ['inbox', 'processing']:
            dir_path = directories[dir_name]
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    removed_files += 1
        
        logger.info(f"✅ Cola limpiada: {removed_files} archivos removidos")
        
        return jsonify({
            'status': 'exitoso',
            'estado': 'exitoso',
            'mensaje': f'Cola limpiada: {removed_files} archivos removidos',
            'message': f'Queue cleaned: {removed_files} files removed',
            'files_removed': removed_files
        })
        
    except Exception as e:
        logger.error(f"Error limpiando cola: {e}")
        return jsonify({
            'status': 'error',
            'estado': 'error',
            'mensaje': f'Error al limpiar cola: {str(e)}',
            'message': f'Error cleaning queue: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)