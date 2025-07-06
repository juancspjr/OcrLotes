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
    """
    FIX: Página principal con Interface Excellence Dashboard
    REASON: Following Interface Excellence philosophy for enhanced filename visibility and professional appearance
    IMPACT: Better user experience with enhanced file tracking and external environment styling
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
    FIX: Endpoint corregido para subida múltiple de archivos con metadatos WhatsApp
    REASON: Usuario reporta error en subida y necesita formato WhatsApp correcto
    IMPACT: Sistema funcional con metadata de WhatsApp visible en interfaz
    INTERFACE: Manejo correcto de archivos múltiples con validación robusta
    VISUAL_CHANGE: Metadatos WhatsApp visibles en interfaz con formato correcto
    """
    try:
        # Manejo de archivos múltiples o individuales
        files_list = []
        
        if 'images' in request.files:
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
                
                # Determinar extensión de archivo
                if '.' in file.filename:
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    if file_ext not in ['png', 'jpg', 'jpeg']:
                        continue  # Saltar archivos no válidos
                else:
                    file_ext = 'png'
                
                # Generar nombre usando formato WhatsApp si es posible
                original_name = file.filename
                
                # Intentar detectar si es formato WhatsApp en el nombre original
                if ('--' in original_name and '@' in original_name and '_' in original_name):
                    # Es formato WhatsApp, usar nombre original con timestamp para evitar duplicados
                    base_name = original_name.rsplit('.', 1)[0]
                    final_filename = f"{base_name}_{timestamp_id}.{file_ext}"
                else:
                    # No es formato WhatsApp, generar nombre genérico
                    clean_name = secure_filename(original_name.rsplit('.', 1)[0] if '.' in original_name else original_name)
                    final_filename = f"{clean_name}_{timestamp_id}.{file_ext}"
                
                # Guardar archivo
                file_path = os.path.join(directories['inbox'], final_filename)
                file.save(file_path)
                
                # Extraer metadatos de WhatsApp del nombre de archivo
                from app import extract_metadata_from_filename
                whatsapp_metadata = extract_metadata_from_filename(final_filename)
                
                # Metadatos completos con datos de WhatsApp empresariales
                metadata = {
                    'filename_original': file.filename,
                    'filename_final': final_filename,
                    'request_id': final_filename.replace(f'_{timestamp_id}', ''),
                    'upload_timestamp': current_time.isoformat(),
                    'file_size': os.path.getsize(file_path),
                    # Campos críticos de WhatsApp para simulación óptima
                    'numerosorteo': whatsapp_metadata.get('numerosorteo', 'A'),
                    'idWhatsapp': whatsapp_metadata.get('idWhatsapp', 'unknown@lid'),
                    'nombre': whatsapp_metadata.get('nombre', 'Unknown'),
                    'horamin': whatsapp_metadata.get('horamin', '00-00'),
                    'texto_mensaje_whatsapp': whatsapp_metadata.get('texto_mensaje_whatsapp', ''),
                    'caption': request.form.get('caption', ''),
                    'otro_valor': request.form.get('otro_valor', 'subir'),
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
        
        # Buscar archivos JSON de resultados
        for json_file in results_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                # Buscar imagen correspondiente
                image_name = json_file.stem
                image_path = None
                for ext in ['.png', '.jpg', '.jpeg']:
                    potential_path = processed_dir / f"{image_name}{ext}"
                    if potential_path.exists():
                        image_path = str(potential_path.relative_to(Path.cwd()))
                        break
                
                processed_files.append({
                    'filename': json_file.name,
                    'image_name': image_name,
                    'image_path': image_path,
                    'json_path': str(json_file.relative_to(Path.cwd())),
                    'result_data': result_data,
                    'processed_date': datetime.fromtimestamp(json_file.stat().st_mtime).isoformat(),
                    'file_size': json_file.stat().st_size,
                    'has_coordinates': 'coordenadas' in result_data.get('datos_extraidos', {}),
                    'extraction_quality': result_data.get('calidad_extraccion', {}).get('categoria', 'N/A')
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)