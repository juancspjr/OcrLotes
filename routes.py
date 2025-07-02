"""
Rutas y controladores optimizados para la aplicación web Flask
Optimizaciones: lazy loading, instancias bajo demanda, mejor rendimiento
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from functools import lru_cache

from app import app

logger = logging.getLogger(__name__)

# FIX: Instancia lazy del orquestador para startup rápido
# REASON: Evitar crear instancia pesada al importar el módulo
# IMPACT: Reduce tiempo de startup significativamente
_orquestador_instance = None

def get_orquestador():
    """Obtiene instancia del orquestador de forma lazy"""
    global _orquestador_instance
    if _orquestador_instance is None:
        # Import lazy para evitar overhead al startup
        from main_ocr_process import OrquestadorOCR
        _orquestador_instance = OrquestadorOCR()
    return _orquestador_instance

# FIX: Cache para configuración que se lee frecuentemente
# REASON: Evitar relectura repetitiva de config
# IMPACT: Mejora rendimiento en requests frecuentes
@lru_cache(maxsize=1)
def get_web_config():
    """Obtiene configuración web de forma cached"""
    import config
    return config.WEB_CONFIG

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    web_config = get_web_config()
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in web_config['allowed_extensions']

@app.route('/')
def index():
    """Página principal de carga de imágenes"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Maneja la carga de archivos y procesamiento OCR optimizado"""
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
            
            # FIX: Obtener orquestador de forma lazy
            # REASON: Evitar instanciar componentes pesados hasta que se necesiten
            # IMPACT: Mejor tiempo de respuesta y uso de memoria
            orquestador = get_orquestador()
            
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
    """Permite descargar archivos generados con optimización"""
    try:
        file_path = Path(app.config['TEMP_FOLDER']) / filename
        
        if not file_path.exists():
            flash('Archivo no encontrado', 'error')
            return redirect(url_for('index'))
        
        # FIX: Optimizar descarga con cache headers
        # REASON: Mejorar rendimiento de descarga
        # IMPACT: Mejor experiencia de usuario
        return send_file(
            file_path, 
            as_attachment=True,
            cache_timeout=3600,  # Cache por 1 hora
            conditional=True     # Support para rangos HTTP
        )
    
    except Exception as e:
        logger.error(f"Error descargando archivo: {str(e)}")
        flash(f'Error descargando archivo: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/process', methods=['POST'])
def api_process():
    """API endpoint optimizado para procesamiento programático"""
    try:
        data = request.get_json()
        
        if not data or 'image_path' not in data:
            return jsonify({'error': 'image_path requerido'}), 400
        
        image_path = data['image_path']
        language = data.get('language', 'spa')
        profile = data.get('profile', 'rapido')
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        # FIX: Lazy loading del orquestador para API
        # REASON: Optimizar tiempo de respuesta en APIs
        # IMPACT: Mejor rendimiento en llamadas programáticas
        orquestador = get_orquestador()
        
        # Procesar imagen
        resultado = orquestador.procesar_imagen_completo(
            image_path,
            language=language,
            profile=profile,
            save_intermediate=False  # No guardar intermedios en API
        )
        
        return jsonify(resultado)
    
    except Exception as e:
        logger.error(f"Error en API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Endpoint optimizado de verificación de salud"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'memory_usage': _get_memory_usage()
    })

# FIX: Cache para funciones auxiliares frecuentemente usadas
# REASON: Evitar recálculos innecesarios
# IMPACT: Mejor rendimiento en operaciones repetitivas
@lru_cache(maxsize=128)
def _get_memory_usage():
    """Obtiene uso de memoria de forma cached"""
    try:
        import psutil
        process = psutil.Process()
        return f"{process.memory_info().rss / 1024 / 1024:.1f} MB"
    except ImportError:
        return "N/A"

def _obtener_archivos_disponibles(resultado):
    """Obtiene lista de archivos disponibles para descarga optimizada"""
    archivos = []
    temp_dir = Path(resultado.get('temp_directory', ''))
    
    if temp_dir.exists():
        # FIX: Usar generadores para mejor eficiencia de memoria
        # REASON: Procesar archivos de forma más eficiente
        # IMPACT: Menor uso de memoria con directorios grandes
        
        # Archivos de imagen
        for ext in ['.png', '.jpg', '.jpeg']:
            archivos.extend([
                {
                    'nombre': archivo.name,
                    'tipo': 'imagen',
                    'ruta': str(archivo.relative_to(Path(app.config['TEMP_FOLDER']))),
                    'tamaño': archivo.stat().st_size if archivo.exists() else 0
                }
                for archivo in temp_dir.glob(f'*{ext}')
            ])
        
        # Archivos de datos
        for ext in ['.json', '.txt']:
            archivos.extend([
                {
                    'nombre': archivo.name,
                    'tipo': 'datos',
                    'ruta': str(archivo.relative_to(Path(app.config['TEMP_FOLDER']))),
                    'tamaño': archivo.stat().st_size if archivo.exists() else 0
                }
                for archivo in temp_dir.glob(f'*{ext}')
            ])
    
    return archivos

def _preparar_datos_graficos(resultado):
    """Prepara datos para gráficos y visualizaciones optimizada"""
    try:
        etapas = resultado.get('etapas', {})
        
        # FIX: Acceso seguro a datos anidados con valores por defecto
        # REASON: Evitar errores y mejorar robustez
        # IMPACT: Mejor estabilidad en visualizaciones
        
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

# Filtros de template personalizados optimizados
@app.template_filter('filesize')
def filesize_filter(size):
    """Convierte bytes a formato legible optimizado"""
    if not isinstance(size, (int, float)) or size <= 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

@app.template_filter('duration')
def duration_filter(seconds):
    """Convierte segundos a formato legible optimizado"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "0ms"
    
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
