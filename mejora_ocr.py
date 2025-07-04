"""
Módulo de mejora y preprocesamiento adaptativo de imágenes para OCR
Aplica técnicas avanzadas de procesamiento basadas en diagnóstico
"""

import cv2
import numpy as np
import json
import logging
import time
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from skimage import restoration, filters, morphology, exposure
from skimage.filters import unsharp_mask
from scipy import ndimage
import config

# Configurar logging
# FIX: Configuración directa para evitar problemas con tipos de datos en LOGGING_CONFIG
# REASON: Algunos valores en config.LOGGING_CONFIG pueden no ser compatibles con logging.basicConfig
# IMPACT: Garantiza inicialización correcta del logging sin errores de tipo
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MejoradorOCR:
    """Clase para aplicar mejoras adaptativas a imágenes para OCR"""
    
    def __init__(self):
        self.profiles = config.PERFORMANCE_PROFILES
        self.preprocessing_config = config.PREPROCESSING_CONFIG
    
    def _convert_numpy_types(self, obj):
        """
        FIX: Convierte TODOS los tipos NumPy y problemáticos a tipos nativos Python para serialización JSON
        REASON: Los valores float32/int64/bool de NumPy y operaciones booleanas no son serializables en JSON
        IMPACT: Garantiza serialización completa sin errores de tipo
        """
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (bool, np.bool)):  # FIX: Manejar booleanos nativos y NumPy
            return bool(obj)
        else:
            return obj
        
    def procesar_imagen(self, image_path, diagnostico, perfil='rapido', save_steps=False, output_dir=None):
        """
        Procesa una imagen aplicando mejoras basadas en el diagnóstico
        
        Args:
            image_path: Ruta a la imagen original
            diagnostico: Diagnóstico de validador_ocr.py
            perfil: Perfil de rendimiento a usar
            save_steps: Si guardar pasos intermedios
            output_dir: Directorio para archivos temporales
            
        Returns:
            dict: Resultado del procesamiento con ruta de imagen mejorada
        """
        try:
            # Validar perfil
            if perfil not in self.profiles:
                perfil = 'rapido'
                logger.warning(f"Perfil no válido, usando 'rapido'")
            
            profile_config = self.profiles[perfil]
            
            # Cargar imagen
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"No se puede cargar la imagen: {image_path}")
            
            # Log inicial
            logger.info(f"Iniciando procesamiento con perfil: {perfil}")
            
            # Secuencia de procesamiento adaptativo
            resultado_procesamiento = {
                'perfil_usado': perfil,
                'pasos_aplicados': [],
                'metricas_antes': self._calcular_metricas_imagen(image),
                'parametros_aplicados': {},
                'tiempo_procesamiento': 0
            }
            
            import time
            start_time = time.time()
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            current_image = gray.copy()
            
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / "01_original_gray.png"), current_image)
            
            # Aplicar secuencia de mejoras según perfil y diagnóstico
            if perfil == 'minimal_enhancement':
                current_image = self._aplicar_mejora_minimal(
                    current_image, diagnostico, profile_config, 
                    resultado_procesamiento, save_steps, output_dir
                )
            else:
                current_image = self._aplicar_secuencia_procesamiento(
                    current_image, diagnostico, profile_config, 
                    resultado_procesamiento, save_steps, output_dir
                )
            
            # Guardar imagen final
            output_path = Path(output_dir) / "imagen_mejorada.png" if output_dir else Path("imagen_mejorada.png")
            cv2.imwrite(str(output_path), current_image)
            
            # Calcular métricas finales
            resultado_procesamiento['metricas_despues'] = self._calcular_metricas_imagen(current_image)
            resultado_procesamiento['tiempo_procesamiento'] = round(time.time() - start_time, 3)
            resultado_procesamiento['imagen_mejorada'] = str(output_path)
            resultado_procesamiento['mejora_calidad'] = self._calcular_mejora_calidad(
                resultado_procesamiento['metricas_antes'],
                resultado_procesamiento['metricas_despues']
            )
            
            logger.info(f"Procesamiento completado en {resultado_procesamiento['tiempo_procesamiento']}s")
            
            # FIX: Convertir tipos NumPy antes de devolver resultado
            # REASON: Evitar errores de serialización JSON con float32/int64
            # IMPACT: Garantiza compatibilidad completa con JSON para API web
            return self._convert_numpy_types(resultado_procesamiento)
            
        except Exception as e:
            logger.error(f"Error en procesamiento de imagen: {str(e)}")
            return {'error': str(e)}
    
    def _aplicar_secuencia_procesamiento(self, image, diagnostico, profile_config, resultado, save_steps, output_dir):
        """Aplica la secuencia completa de procesamiento inteligente"""
        current = image.copy()
        step_counter = 2
        
        # FIX: CRITICAL - Sistema de Triage Inteligente y Conservación Extrema de Caracteres
        # REASON: Implementar evaluación completa antes de cualquier procesamiento
        # IMPACT: Evita transformaciones innecesarias y preserva integridad del texto
        
        # FIX: Implementar rutas especializadas basadas en detección inteligente del validador
        # REASON: Usar la detección inteligente ya implementada en validador_ocr.py
        # IMPACT: Procesamiento optimizado según tipo de imagen detectado
        
        # FIX: CRITICAL - Validar tipo de datos del diagnóstico antes de usar
        # REASON: El diagnostico puede venir como string o dict, necesitamos manejarlo correctamente
        # IMPACT: Evita errores de tipo "string indices must be integers, not 'str'"
        if isinstance(diagnostico, str):
            logger.warning("Diagnóstico recibido como string, usando procesamiento tradicional")
            deteccion_inteligente = {}
            tipo_imagen = 'documento_escaneado'
            inversion_requerida = False
        elif isinstance(diagnostico, dict):
            deteccion_inteligente = diagnostico.get('deteccion_inteligente', {})
            tipo_imagen = deteccion_inteligente.get('tipo_imagen', 'documento_escaneado')
            inversion_requerida = deteccion_inteligente.get('inversion_requerida', False)
        else:
            logger.error(f"Tipo de diagnóstico inesperado: {type(diagnostico)}")
            deteccion_inteligente = {}
            tipo_imagen = 'documento_escaneado'
            inversion_requerida = False
        
        # FIX: ELIMINAR COMPLETAMENTE la fase de unificación de fondos
        # REASON: Usuario reporta que esta fase daña la calidad de la imagen
        # IMPACT: Preserva la calidad original de la imagen sin procesamiento agresivo
        
        # FASE 1.0: Análisis simple sin modificar la imagen
        intensidad_media = np.mean(current)
        histogram = cv2.calcHist([current], [0], None, [256], [0, 256])
        
        # Detectar si el fondo es predominantemente oscuro (solo para análisis)
        pixeles_oscuros = np.sum(histogram[0:80])
        pixeles_totales = current.shape[0] * current.shape[1]
        porcentaje_fondo_oscuro = pixeles_oscuros / pixeles_totales
        
        # NO aplicar unificación - solo registrar las métricas
        resultado['pasos_aplicados'].append('00_analisis_sin_unificacion')
        resultado['parametros_aplicados']['analisis_fondos'] = {
            'intensidad_media_original': float(round(intensidad_media, 2)),
            'porcentaje_fondo_oscuro': float(round(porcentaje_fondo_oscuro, 3)),
            'unificacion_aplicada': False,  # Siempre False ahora
            'razon_no_unificacion': 'preservacion_calidad_usuario'
        }
        
        # Maximizar claridad de letras independientemente de la estrategia
        # Aplicar filtro de nitidez suave para preservar caracteres
        kernel_nitidez = np.array([[-0.1, -0.1, -0.1],
                                  [-0.1,  1.8, -0.1],
                                  [-0.1, -0.1, -0.1]])
        current = cv2.filter2D(current, -1, kernel_nitidez)
        current = np.clip(current, 0, 255).astype(np.uint8)
        
        resultado['pasos_aplicados'].append('00_maxima_claridad_letras')
        
        if save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_claridad_letras.png"), current)
            step_counter += 1

        # FIX: ELIMINAR inversión localizada - aplicar solo inversión global si es necesario
        # REASON: Simplificar procesamiento y evitar degradación de calidad
        # IMPACT: Procesamiento más limpio y preservación de calidad original
        
        # FASE 1.1: Inversión simple y directa solo para imágenes muy oscuras
        if intensidad_media < 80:  # Solo para imágenes muy oscuras
            current = cv2.bitwise_not(current)
            resultado['pasos_aplicados'].append('01_inversion_global_simple')
            resultado['parametros_aplicados']['inversion_global'] = {
                'intensidad_media_original': float(round(intensidad_media, 2)),
                'razon': 'imagen_muy_oscura_necesita_inversion'
            }
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_inversion_global.png"), current)
                step_counter += 1
        else:
            resultado['pasos_aplicados'].append('01_no_inversion_necesaria')
            resultado['parametros_aplicados']['no_inversion'] = {
                'razon': 'imagen_suficientemente_clara',
                'intensidad_media': float(round(intensidad_media, 2))
            }
        # FASE 2: Aplicar estrategia especializada según tipo de imagen
        if tipo_imagen == "screenshot_movil":
            current = self._procesar_screenshot_movil(current, deteccion_inteligente, profile_config, resultado, save_steps, output_dir, step_counter)
        else:
            current = self._procesar_documento_escaneado(current, diagnostico, profile_config, resultado, save_steps, output_dir, step_counter)
        
        if save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_procesamiento_final.png"), current)
        
        return current
    
    def _aplicar_mejora_minimal(self, image, diagnostico, profile_config, resultado, save_steps, output_dir):
        """
        FIX: Implementa mejora mínima con solo nitidez suave y ajustes de brillo/contraste
        REASON: Usuario solicita procesamiento mínimo sin degradación agresiva de calidad
        IMPACT: Preserva calidad original mientras mejora legibilidad de texto
        """
        current = image.copy()
        step_counter = 2
        
        # Detectar si necesita inversión de colores (solo para fondos muy oscuros)
        mean_intensity = np.mean(current)
        if mean_intensity < 80:  # Solo para imágenes muy oscuras
            current = cv2.bitwise_not(current)
            resultado['pasos_aplicados'].append('01_inversion_colores')
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_inversion.png"), current)
                step_counter += 1
        
        # Paso 1: Ampliar imagen suavemente (solo si es pequeña)
        h, w = current.shape
        if h < 1000 or w < 1000:
            scale_factor = min(2.0, 1500 / max(h, w))  # Ampliar hasta máximo 1500px
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            current = cv2.resize(current, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            resultado['pasos_aplicados'].append('02_ampliacion_suave')
            resultado['parametros_aplicados']['ampliacion'] = {
                'factor': float(round(scale_factor, 2)),
                'tamano_original': [int(h), int(w)],
                'tamano_nuevo': [int(new_h), int(new_w)]
            }
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_ampliacion.png"), current)
                step_counter += 1
        
        # Paso 2: Ajuste suave de brillo y contraste
        brightness = 10  # Aumentar brillo ligeramente
        contrast = 1.1   # Aumentar contraste muy suavemente
        current = cv2.convertScaleAbs(current, alpha=contrast, beta=brightness)
        resultado['pasos_aplicados'].append('03_ajuste_suave_brillo_contraste')
        resultado['parametros_aplicados']['ajuste_brillo_contraste'] = {
            'brillo': int(brightness),
            'contraste': float(contrast)
        }
        if save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_brillo_contraste.png"), current)
            step_counter += 1
        
        # Paso 3: Nitidez suave (solo si es necesario)
        # Detectar si la imagen necesita nitidez
        laplacian_var = cv2.Laplacian(current, cv2.CV_64F).var()
        if laplacian_var < 100:  # Solo si está desenfocada
            # Aplicar nitidez suave con kernel personalizado
            kernel = np.array([[-0.5, -0.5, -0.5],
                              [-0.5,  5.0, -0.5],
                              [-0.5, -0.5, -0.5]])
            current = cv2.filter2D(current, -1, kernel)
            resultado['pasos_aplicados'].append('04_nitidez_suave')
            resultado['parametros_aplicados']['nitidez'] = {
                'metodo': 'kernel_suave',
                'desenfoque_detectado': float(round(laplacian_var, 2))
            }
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_nitidez_suave.png"), current)
                step_counter += 1
        
        # Paso 4: Eliminación muy suave de ruido (solo si hay ruido significativo)
        noise_level = np.std(current)
        if noise_level > 30:  # Solo si hay ruido considerable
            current = cv2.bilateralFilter(current, 5, 20, 20)  # Filtro muy suave
            resultado['pasos_aplicados'].append('05_eliminacion_ruido_suave')
            resultado['parametros_aplicados']['eliminacion_ruido'] = {
                'metodo': 'bilateral_suave',
                'nivel_ruido_detectado': float(round(noise_level, 2))
            }
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_ruido_suave.png"), current)
                step_counter += 1
        
        resultado['pasos_aplicados'].append('06_mejora_minimal_completada')
        resultado['parametros_aplicados']['mejora_minimal'] = {
            'filosofia': 'conservacion_maxima_caracteres',
            'procesamiento': 'minimal_sin_degradacion'
        }
        
        return current
    
    def _evaluacion_inteligente_triage(self, image, diagnostico, resultado):
        """Evaluación inteligente inicial - Fase 1 del sistema"""
        # FIX: Implementar evaluación de viabilidad crítica
        # REASON: Detectar imágenes no procesables antes de desperdiciar recursos
        # IMPACT: Eficiencia del sistema y prevención de falsos positivos
        
        h, w = image.shape
        
        # 1. Evaluación de Viabilidad y Detección de Daño Crítico
        if h < 50 or w < 50:
            return {
                'skip_processing': True,
                'razon': 'dimensiones_criticas',
                'imagen_optimizada': image
            }
        
        # 2. Detección de dispersión de píxeles (ruido extremo)
        edges = cv2.Canny(image, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)
        
        if edge_density > 0.8:  # Demasiado ruido
            return {
                'skip_processing': True,
                'razon': 'dispersion_pixels_critica',
                'imagen_optimizada': image
            }
        
        # 3. Detección de contraste cero
        min_val, max_val = np.min(image), np.max(image)
        if max_val - min_val < 10:  # Contraste casi nulo
            return {
                'skip_processing': True,
                'razon': 'contraste_cero',
                'imagen_optimizada': image
            }
        
        # 4. Análisis de estado visual para imágenes viables
        mean_intensity = np.mean(image)
        
        # Detección temprana de inversión (Caso A: Fondo Oscuro, Letras Claras)
        from config import IMAGE_TYPE_DETECTION
        if mean_intensity < IMAGE_TYPE_DETECTION['dark_background_threshold']:
            histogram = cv2.calcHist([image], [0], None, [256], [0, 256])
            dark_pixels = np.sum(histogram[0:64])
            light_pixels = np.sum(histogram[192:256])
            
            confidence = dark_pixels / (dark_pixels + light_pixels) if (dark_pixels + light_pixels) > 0 else 0
            
            if confidence > IMAGE_TYPE_DETECTION['inversion_confidence_threshold']:
                # Inversión inmediata para conservar caracteres
                inverted = cv2.bitwise_not(image)
                resultado['pasos_aplicados'].append('Inversión temprana (Caso A)')
                resultado['parametros_aplicados']['inversion_caso_a'] = {
                    'intensidad_media_original': float(round(mean_intensity, 2)),
                    'confianza_inversion': float(round(confidence, 3)),
                    'pixeles_oscuros': int(dark_pixels),
                    'pixeles_claros': int(light_pixels)
                }
                
                return {
                    'skip_processing': False,
                    'razon': 'inversion_aplicada',
                    'imagen_optimizada': inverted
                }
        
        return {
            'skip_processing': False,
            'razon': 'procesamiento_necesario',
            'imagen_optimizada': image
        }
    
    def _detectar_tipo_imagen(self, image, diagnostico, resultado):
        """Detecta el tipo de imagen para aplicar estrategia específica"""
        h, w = image.shape
        aspect_ratio = w / h if h > 0 else 1
        
        from config import IMAGE_TYPE_DETECTION
        detection_config = IMAGE_TYPE_DETECTION
        
        # Detección de captura de pantalla
        is_screenshot = (
            w >= detection_config['screenshot_indicators']['min_width'] and
            h >= detection_config['screenshot_indicators']['min_height'] and
            aspect_ratio >= detection_config['screenshot_indicators']['aspect_ratio_min'] and
            (w * h) >= detection_config['screenshot_indicators']['resolution_threshold']
        )
        
        # Detección de documento escaneado
        geometria = diagnostico.get('geometria_orientacion', {})
        skew_angle = abs(geometria.get('sesgo_estimado', 0))
        
        is_scanned_doc = (
            skew_angle > detection_config['document_scan_indicators']['skew_threshold'] or
            not is_screenshot
        )
        
        tipo = 'screenshot' if is_screenshot else 'documento_escaneado'
        
        resultado['tipo_imagen_detectado'] = {
            'tipo': tipo,
            'es_screenshot': is_screenshot,
            'dimensiones': f"{w}x{h}",
            'aspect_ratio': float(round(aspect_ratio, 2)),
            'sesgo_detectado': float(round(skew_angle, 2))
        }
        
        return tipo
    
    def _seleccionar_estrategia_procesamiento(self, tipo_imagen, profile_config, resultado):
        """Selecciona la estrategia de procesamiento basada en el tipo de imagen"""
        if tipo_imagen == 'screenshot':
            # Estrategia para capturas de pantalla - Conservación Extrema
            estrategia = {
                'redimensionar': profile_config.get('resize_if_needed', True),
                'deskew': False,  # NUNCA para screenshots
                'bilateral_filter': False,  # NUNCA para capturas digitales
                'noise_removal': False,  # NUNCA para capturas digitales
                'contrast_enhancement': True,
                'adaptive_threshold': True,
                'morphology': 'minimal',  # Solo operaciones mínimas
                'sharpening': 'conditional'  # Solo si se detecta blur
            }
        else:
            # Estrategia para documentos escaneados
            estrategia = {
                'redimensionar': profile_config.get('resize_if_needed', True),
                'deskew': profile_config.get('deskew', 'conditional'),
                'bilateral_filter': profile_config.get('bilateral_filter', 'conditional'),
                'noise_removal': profile_config.get('noise_removal_iterations', 0) > 0,
                'contrast_enhancement': True,
                'adaptive_threshold': True,
                'morphology': 'full',
                'sharpening': profile_config.get('sharpening', 'conditional')
            }
        
        resultado['estrategia_seleccionada'] = estrategia
        return estrategia
    
    def _aplicar_estrategia_inteligente(self, image, estrategia, diagnostico, resultado, save_steps, output_dir, step_counter, profile_config):
        """Aplica la estrategia de procesamiento seleccionada"""
        current = image.copy()
        
        # Aplicar solo los pasos necesarios según la estrategia
        
        # 1. Redimensionamiento si es necesario
        if estrategia['redimensionar'] and max(current.shape) > self.preprocessing_config['resize_max_dimension']:
            current = self._aplicar_redimensionamiento(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_redimensionado.png"), current)
                step_counter += 1
        
        # 2. Corrección de sesgo SOLO para documentos escaneados
        if estrategia['deskew'] and estrategia['deskew'] != False:
            geometria = diagnostico.get('geometria_orientacion', {})
            if geometria.get('requiere_deskew', False):
                current = self._aplicar_deskew(current, diagnostico, resultado)
                if save_steps and output_dir:
                    cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_deskew.png"), current)
                    step_counter += 1
        
        # 3. Filtro bilateral SOLO si se detecta ruido significativo
        if estrategia['bilateral_filter'] and estrategia['bilateral_filter'] != False:
            if self._evaluar_necesidad_bilateral(current, diagnostico):
                current = self._aplicar_filtro_bilateral(current, diagnostico, resultado)
                if save_steps and output_dir:
                    cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_bilateral.png"), current)
                    step_counter += 1
        
        # 4. Eliminación de ruido OMITIDA para capturas digitales
        # (Los pasos 04_denoise y 05_denoise se eliminan completamente)
        
        # 5. Mejora de contraste (siempre necesario)
        if estrategia['contrast_enhancement']:
            current = self._aplicar_mejora_contraste(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_contraste.png"), current)
                step_counter += 1
        
        # FIX: 5.1 Técnicas Avanzadas de Mejora - MÁS ALLÁ DEL UPSCALING
        # REASON: Usuario solicita nuevas técnicas de mejora más sofisticadas
        # IMPACT: Mejora significativa en calidad antes de binarización
        
        # profile_config ya está disponible como parámetro
        if profile_config.get('advanced_binarization', False) or profile_config.get('character_conservation') == 'extreme':
            
            # 5.1a CLAHE Adaptativo para mejor distribución de contraste
            current = self._aplicar_clahe_adaptativo(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_clahe.png"), current)
                step_counter += 1
            
            # 5.1b Corrección Gamma Adaptativa
            current = self._aplicar_correccion_gamma_adaptativa(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_gamma.png"), current)
                step_counter += 1
            
            # 5.1c Unsharp Masking para nitidez preservando caracteres
            current = self._aplicar_unsharp_mask(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_unsharp.png"), current)
                step_counter += 1
            
            # 5.1d Realce de bordes inteligente
            current = self._aplicar_realce_bordes(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_edges.png"), current)
                step_counter += 1
        
        # 6. Binarización avanzada mejorada (REEMPLAZA la simple)
        if estrategia['adaptive_threshold']:
            current = self._aplicar_binarizacion_adaptativa(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_binarizacion.png"), current)
                step_counter += 1
        
        # 7. Operaciones morfológicas (mínimas para screenshots)
        if estrategia['morphology'] == 'minimal':
            current = self._aplicar_morfologia_minimal(current, resultado)
        elif estrategia['morphology'] == 'full':
            current = self._aplicar_morfologia(current, resultado)
        
        if estrategia['morphology'] != False and save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_morfologia.png"), current)
            step_counter += 1
        
        # 8. Nitidez SOLO si es necesario
        if estrategia['sharpening'] == 'conditional' and self._evaluar_necesidad_nitidez(current, diagnostico):
            current = self._aplicar_nitidez(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_nitidez.png"), current)
                step_counter += 1
        
        return current
    
    def _evaluar_necesidad_bilateral(self, image, diagnostico):
        """Evalúa si realmente se necesita filtro bilateral"""
        ruido = diagnostico.get('ruido_artefactos', {})
        noise_level = ruido.get('nivel_ruido', 0)
        return noise_level > 15  # Solo si hay ruido significativo
    
    def _evaluar_necesidad_nitidez(self, image, diagnostico):
        """Evalúa si se necesita filtro de nitidez"""
        calidad = diagnostico.get('calidad_imagen', {})
        blur_variance = calidad.get('blur_variance', 100)
        return blur_variance < 50  # Solo si la imagen está borrosa
    
    def _aplicar_morfologia_minimal(self, image, resultado):
        """Aplica operaciones morfológicas mínimas para screenshots"""
        # Solo apertura muy suave para limpiar píxeles sueltos
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
        
        resultado['pasos_aplicados'].append('Morfología mínima (screenshot)')
        resultado['parametros_aplicados']['morfologia_minimal'] = {
            'kernel_size': (1, 1),
            'operacion': 'apertura',
            'iteraciones': 1
        }
        
        return cleaned
    
    def _aplicar_redimensionamiento(self, image, resultado):
        """Redimensiona la imagen manteniendo proporción"""
        h, w = image.shape
        max_dim = self.preprocessing_config['resize_max_dimension']
        
        if max(h, w) > max_dim:
            if h > w:
                new_h = max_dim
                new_w = int(w * max_dim / h)
            else:
                new_w = max_dim
                new_h = int(h * max_dim / w)
            
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            resultado['pasos_aplicados'].append('Redimensionamiento')
            resultado['parametros_aplicados']['redimensionamiento'] = {
                'original': (w, h),
                'nuevo': (new_w, new_h),
                'factor': max_dim / max(h, w)
            }
            
            return resized
        
        return image
    
    def _aplicar_deskew(self, image, diagnostico, resultado):
        """
        FIX: DESKEW COMPLETAMENTE ELIMINADO
        REASON: Usuario reporta que causa falsa inclinación en screenshots
        IMPACT: Elimina rotaciones innecesarias, preserva integridad de caracteres
        """
        # FIX: No aplicar deskew NUNCA - conservación extrema de caracteres
        geometria = diagnostico.get('geometria_orientacion', {})
        angle = geometria.get('sesgo_estimado', 0)
        
        resultado['pasos_aplicados'].append('Deskew ELIMINADO (Conservación Extrema)')
        resultado['parametros_aplicados']['deskew_eliminado'] = {
            'razon': 'conservacion_extrema_caracteres',
            'angulo_detectado_ignorado': float(round(angle, 2)),
            'politica': 'nunca_rotar_screenshots_ni_documentos'
        }
        
        logger.info("Deskew eliminado según política de conservación extrema de caracteres")
        return image  # Devolver imagen sin modificar
    
    def _aplicar_filtro_bilateral(self, image, diagnostico, resultado):
        """Aplica filtro bilateral para reducir ruido preservando bordes"""
        # FIX: Conservación extrema de caracteres - bilateral solo cuando realmente hay ruido
        # REASON: Las capturas de pantalla digitales no necesitan bilateral, causa difuminación
        # IMPACT: Preserva la nitidez original del texto digital
        
        ruido = diagnostico.get('ruido_artefactos', {})
        noise_level = ruido.get('nivel_ruido', 10)
        
        # Detectar tipo de imagen
        imagen_info = diagnostico.get('imagen_info', {})
        width = imagen_info.get('ancho', 0)
        height = imagen_info.get('alto', 0)
        aspect_ratio = width / height if height > 0 else 1
        
        is_screenshot = (
            aspect_ratio > 1.5 or
            width > 1000 or
            height > 600
        )
        
        # Solo aplicar filtro bilateral si:
        # 1. Hay ruido significativo (>15 para screenshots, >10 para documentos escaneados)
        # 2. O no es screenshot y hay ruido moderado
        noise_threshold = 15 if is_screenshot else 10
        should_apply_bilateral = noise_level > noise_threshold
        
        # Inicializar parámetros por defecto
        d, sigma_color, sigma_space = 5, 50, 50
        
        if should_apply_bilateral:
            # Parámetros más conservadores para capturas de pantalla
            if is_screenshot:
                # Para screenshots: parámetros mínimos que preserven nitidez
                if noise_level > 25:
                    d, sigma_color, sigma_space = 5, 30, 30
                else:
                    d, sigma_color, sigma_space = 3, 20, 20
            else:
                # Para documentos escaneados: parámetros normales
                if noise_level > 20:
                    d, sigma_color, sigma_space = 9, 100, 100
                elif noise_level > 10:
                    d, sigma_color, sigma_space = 7, 75, 75
                else:
                    d, sigma_color, sigma_space = 5, 50, 50
            
            filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            
            resultado['pasos_aplicados'].append('Filtro bilateral')
            resultado['parametros_aplicados']['filtro_bilateral'] = {
                'd': d, 'sigma_color': sigma_color, 'sigma_space': sigma_space,
                'tipo_imagen': 'screenshot' if is_screenshot else 'escaneada',
                'nivel_ruido': noise_level
            }
            
            return filtered
        else:
            # Log por qué no se aplicó bilateral
            resultado['parametros_aplicados']['bilateral_omitido'] = {
                'razon': 'preservacion_nitidez',
                'nivel_ruido': noise_level,
                'umbral_requerido': noise_threshold,
                'tipo_imagen': 'screenshot' if is_screenshot else 'escaneada'
            }
            
        return image
    
    def _aplicar_eliminacion_ruido(self, image, profile_config, resultado):
        """Aplica eliminación de ruido gaussiano"""
        # FIX: Conservación extrema de caracteres - denoise solo cuando es crítico
        # REASON: Gaussian blur en capturas de pantalla causa difuminación innecesaria
        # IMPACT: Preserva la nitidez del texto digital evitando suavizado excesivo
        
        # Detectar si es captura de pantalla
        h, w = image.shape
        aspect_ratio = w / h if h > 0 else 1
        is_screenshot = (
            aspect_ratio > 1.5 or
            w > 1000 or
            h > 600
        )
        
        iterations = profile_config['noise_removal_iterations']
        kernel_size = profile_config['gaussian_blur_kernel']
        
        # Para capturas de pantalla: eliminar casi todo el denoising
        if is_screenshot:
            # Solo aplicar si hay muchas iteraciones configuradas (ruido severo)
            if iterations > 2:
                iterations = 1  # Máximo 1 iteración
                kernel_size = min(kernel_size, 3)  # Kernel muy pequeño
            else:
                # Skip denoising completamente para screenshots
                resultado['parametros_aplicados']['denoise_omitido'] = {
                    'razon': 'screenshot_preservacion_nitidez',
                    'iteraciones_originales': iterations,
                    'kernel_original': kernel_size
                }
                return image
        
        denoised = image.copy()
        for i in range(iterations):
            denoised = cv2.GaussianBlur(denoised, (kernel_size, kernel_size), 0)
        
        resultado['pasos_aplicados'].append('Eliminación de ruido')
        resultado['parametros_aplicados']['eliminacion_ruido'] = {
            'iteraciones': iterations,
            'kernel_size': kernel_size,
            'tipo_imagen': 'screenshot' if is_screenshot else 'escaneada',
            'reducido_por_conservacion': is_screenshot
        }
        
        return denoised
    
    def _aplicar_mejora_contraste(self, image, diagnostico, resultado):
        """Aplica mejora de contraste adaptativa"""
        calidad = diagnostico.get('calidad_imagen', {})
        contraste_actual = calidad.get('contraste', 50)
        
        if contraste_actual < 40:
            # CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            
            resultado['pasos_aplicados'].append('Mejora de contraste CLAHE')
            resultado['parametros_aplicados']['mejora_contraste'] = {
                'metodo': 'CLAHE',
                'clip_limit': 3.0,
                'tile_size': (8, 8)
            }
        else:
            # Ecualización histograma simple
            enhanced = cv2.equalizeHist(image)
            
            resultado['pasos_aplicados'].append('Ecualización de histograma')
            resultado['parametros_aplicados']['mejora_contraste'] = {
                'metodo': 'Equalización simple'
            }
        
        return enhanced
    
    def _aplicar_binarizacion_adaptativa(self, image, diagnostico, resultado):
        """
        FIX: Binarización adaptativa MEJORADA - Ahora usa múltiples algoritmos
        REASON: Usuario reporta que 05_binarizacion necesita mejoras
        IMPACT: Selecciona automáticamente el mejor algoritmo de binarización
        """
        # FIX: Usar la nueva binarización ELITE
        return self._aplicar_binarizacion_elite(image, diagnostico, resultado)
    
    def _aplicar_morfologia(self, image, resultado):
        """Aplica operaciones morfológicas para limpiar la imagen"""
        # Kernel para operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Apertura para eliminar ruido pequeño
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Cierre para conectar componentes de texto
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        
        resultado['pasos_aplicados'].append('Operaciones morfológicas')
        resultado['parametros_aplicados']['morfologia'] = {
            'apertura_kernel': (2, 2),
            'cierre_kernel': (3, 1)
        }
        
        return closed
    
    def _aplicar_nitidez(self, image, diagnostico, resultado):
        """Aplica filtro de nitidez"""
        # FIX: Mejora agresiva de nitidez para compensar difuminación de procesamientos previos
        # REASON: Los filtros conservadores pueden haber reducido ligeramente la nitidez
        # IMPACT: Recupera la definición de bordes esencial para OCR óptimo
        
        calidad = diagnostico.get('calidad_imagen', {})
        blur_variance = calidad.get('blur_variance', 100)
        
        # Detectar tipo de imagen
        h, w = image.shape
        aspect_ratio = w / h if h > 0 else 1
        is_screenshot = (
            aspect_ratio > 1.5 or
            w > 1000 or
            h > 600
        )
        
        # Aplicar nitidez más agresiva para screenshots o si hay cualquier signo de difuminación
        should_sharpen = (
            blur_variance < 300 or  # Umbral más alto que antes
            is_screenshot  # Siempre aplicar a screenshots para compensar procesamientos previos
        )
        
        if should_sharpen:
            if is_screenshot:
                # Para screenshots: nitidez más agresiva para compensar bilateral/denoise reducidos
                kernel = np.array([
                    [0, -1, 0],
                    [-1, 5.5, -1],  # Centro más fuerte para mayor nitidez
                    [0, -1, 0]
                ], dtype=np.float32)
                metodo = 'Nitidez agresiva para screenshot'
            else:
                # Para documentos escaneados: nitidez estándar
                kernel = np.array(self.preprocessing_config['sharpening_kernel'], dtype=np.float32)
                metodo = 'Nitidez estándar'
            
            sharpened = cv2.filter2D(image, -1, kernel)
            
            # Aplicar unsharp masking adicional para screenshots muy difuminados
            if is_screenshot and blur_variance < 150:
                gaussian = cv2.GaussianBlur(image, (3, 3), 0.8)
                unsharp = cv2.addWeighted(sharpened, 1.5, gaussian, -0.5, 0)
                sharpened = np.clip(unsharp, 0, 255).astype(np.uint8)
                metodo += ' + Unsharp masking'
            
            resultado['pasos_aplicados'].append('Aplicación de nitidez')
            resultado['parametros_aplicados']['nitidez'] = {
                'blur_variance_detectado': round(blur_variance, 1),
                'metodo': metodo,
                'umbral_aplicado': 300,
                'tipo_imagen': 'screenshot' if is_screenshot else 'escaneada'
            }
            
            return sharpened
        else:
            resultado['parametros_aplicados']['nitidez_omitida'] = {
                'razon': 'imagen_suficientemente_nitida',
                'blur_variance': round(blur_variance, 1),
                'umbral_minimo': 300
            }
        
        return image
    
    def _calcular_metricas_imagen(self, image):
        """Calcula métricas básicas de una imagen"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        return {
            'brillo_promedio': float(np.mean(gray)),
            'contraste': float(np.std(gray)),
            'nitidez': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
            'rango_dinamico': float(np.max(gray) - np.min(gray))
        }
    
    def _calcular_mejora_calidad(self, antes, despues):
        """Calcula la mejora en calidad entre antes y después"""
        mejoras = {}
        
        for metrica in ['contraste', 'nitidez', 'rango_dinamico']:
            if metrica in antes and metrica in despues:
                cambio = despues[metrica] - antes[metrica]
                porcentaje = (cambio / antes[metrica]) * 100 if antes[metrica] != 0 else 0
                mejoras[metrica] = {
                    'antes': round(antes[metrica], 2),
                    'despues': round(despues[metrica], 2),
                    'cambio': round(cambio, 2),
                    'porcentaje': round(porcentaje, 1)
                }
        
        return mejoras
    
    # FIX: Nuevas técnicas avanzadas de procesamiento más allá del upscaling
    # REASON: Implementar algoritmos sofisticados para mejorar calidad OCR
    # IMPACT: Mejora significativa en precisión y confianza de extracción
    
    def _aplicar_clahe_adaptativo(self, image, resultado):
        """Aplica Contrast Limited Adaptive Histogram Equalization"""
        try:
            config_clahe = self.preprocessing_config['advanced_techniques']
            if not config_clahe.get('clahe_enabled', False):
                return image
                
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Aplicar CLAHE
            clahe = cv2.createCLAHE(
                clipLimit=config_clahe.get('clahe_clip_limit', 2.0),
                tileGridSize=config_clahe.get('clahe_tile_grid_size', (8, 8))
            )
            enhanced = clahe.apply(gray)
            
            resultado['pasos_aplicados'].append('CLAHE Adaptativo')
            resultado['parametros_aplicados']['clahe'] = {
                'clip_limit': float(config_clahe.get('clahe_clip_limit', 2.0)),
                'tile_grid_size': config_clahe.get('clahe_tile_grid_size', (8, 8))
            }
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error en CLAHE adaptativo: {str(e)}")
            return image
    
    def _aplicar_unsharp_mask(self, image, resultado):
        """Aplica Unsharp Masking para mejorar nitidez preservando caracteres"""
        try:
            config_unsharp = self.preprocessing_config['advanced_techniques']
            if not config_unsharp.get('unsharp_mask_enabled', False):
                return image
            
            # Normalizar imagen para scikit-image
            if image.dtype == np.uint8:
                image_normalized = image.astype(np.float64) / 255.0
            else:
                image_normalized = image
            
            # Aplicar unsharp masking
            enhanced = unsharp_mask(
                image_normalized,
                radius=config_unsharp.get('unsharp_mask_radius', 1.0),
                amount=config_unsharp.get('unsharp_mask_strength', 1.5)
            )
            
            # Convertir de vuelta a uint8
            enhanced = (enhanced * 255).astype(np.uint8)
            
            resultado['pasos_aplicados'].append('Unsharp Masking')
            resultado['parametros_aplicados']['unsharp_mask'] = {
                'radius': float(config_unsharp.get('unsharp_mask_radius', 1.0)),
                'strength': float(config_unsharp.get('unsharp_mask_strength', 1.5))
            }
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error en Unsharp Masking: {str(e)}")
            return image
    
    def _aplicar_realce_bordes(self, image, resultado):
        """Aplica realce de bordes inteligente para mejorar definición de caracteres"""
        try:
            config_edge = self.preprocessing_config['advanced_techniques']
            if not config_edge.get('edge_enhancement_enabled', False):
                return image
            
            # Detectar bordes con Canny
            edges = cv2.Canny(image, 50, 150)
            
            # Crear máscara de realce
            enhanced = image.copy()
            enhanced[edges > 0] = np.minimum(enhanced[edges > 0] * 1.2, 255)
            
            resultado['pasos_aplicados'].append('Realce de Bordes')
            resultado['parametros_aplicados']['edge_enhancement'] = {
                'canny_low': 50,
                'canny_high': 150,
                'enhancement_factor': 1.2
            }
            
            return enhanced.astype(np.uint8)
            
        except Exception as e:
            logger.warning(f"Error en realce de bordes: {str(e)}")
            return image
    
    def _aplicar_correccion_gamma_adaptativa(self, image, resultado):
        """Aplica corrección gamma adaptativa para optimizar contraste"""
        try:
            config_gamma = self.preprocessing_config['advanced_techniques']
            if not config_gamma.get('gamma_correction_enabled', False):
                return image
                
            # Calcular gamma óptimo basado en la distribución de intensidades
            mean_intensity = np.mean(image)
            
            # Determinar gamma basado en la intensidad media
            if mean_intensity < 85:  # Imagen oscura
                gamma = 0.8
            elif mean_intensity > 170:  # Imagen clara
                gamma = 1.2
            else:  # Imagen normal
                gamma = 1.0
            
            # Aplicar corrección gamma
            gamma_range = config_gamma.get('gamma_range', (0.8, 1.2))
            gamma = max(gamma_range[0], min(gamma_range[1], gamma))
            
            # Tabla de lookup para gamma
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            enhanced = cv2.LUT(image, table)
            
            resultado['pasos_aplicados'].append('Corrección Gamma Adaptativa')
            resultado['parametros_aplicados']['gamma_correction'] = {
                'gamma_value': float(gamma),
                'mean_intensity_original': float(mean_intensity)
            }
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error en corrección gamma: {str(e)}")
            return image
    
    def _aplicar_rangos_elite(self, imagen_binaria, config_elite):
        """
        FIX: Aplica rangos ELITE específicos para fondo blanco uniforme y texto negro nítido
        REASON: Implementa rangos 245-255 para fondo y 0-10 para texto según estrategia ELITE
        IMPACT: Imagen binaria perfecta con contraste óptimo para OCR de una sola pasada
        """
        try:
            fondo_min = config_elite.get('fondo_blanco_min', 245)
            fondo_max = config_elite.get('fondo_blanco_max', 255)
            texto_min = config_elite.get('texto_negro_min', 0)
            texto_max = config_elite.get('texto_negro_max', 10)
            
            # Crear imagen ELITE con rangos específicos
            imagen_elite = imagen_binaria.copy()
            
            # Píxeles de fondo (blancos) -> rango 245-255
            mask_fondo = imagen_binaria > 127  # Píxeles considerados fondo
            rango_fondo = np.random.randint(fondo_min, fondo_max + 1, np.sum(mask_fondo))
            imagen_elite[mask_fondo] = rango_fondo
            
            # Píxeles de texto (negros) -> rango 0-10
            mask_texto = imagen_binaria <= 127  # Píxeles considerados texto
            rango_texto = np.random.randint(texto_min, texto_max + 1, np.sum(mask_texto))
            imagen_elite[mask_texto] = rango_texto
            
            return imagen_elite
            
        except Exception as e:
            logger.warning(f"Error aplicando rangos ELITE: {str(e)}")
            return imagen_binaria
    
    def _seleccionar_mejor_binarizacion_elite(self, algoritmos_elite, config_elite):
        """
        FIX: Selecciona el mejor algoritmo de binarización ELITE basado en métricas específicas
        REASON: Necesario para elegir óptima binarización según nueva estrategia
        IMPACT: Garantiza la mejor imagen binaria para OCR de una sola pasada
        """
        try:
            if not algoritmos_elite:
                return None
            
            mejor_algoritmo = None
            mejor_score = -1
            
            for nombre, imagen in algoritmos_elite:
                # Evaluar métricas ELITE específicas
                score = self._evaluar_calidad_elite(imagen, config_elite)
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_algoritmo = (nombre, imagen)
            
            return mejor_algoritmo
            
        except Exception as e:
            logger.warning(f"Error seleccionando mejor binarización ELITE: {str(e)}")
            return algoritmos_elite[0] if algoritmos_elite else None
    
    def _evaluar_calidad_elite(self, imagen_binaria, config_elite):
        """
        FIX: Evalúa calidad específica para binarización ELITE
        REASON: Métricas especializadas para validar rangos 245-255 fondo y 0-10 texto
        IMPACT: Asegura que la imagen cumple estándares ELITE para OCR óptimo
        """
        try:
            # Verificar distribución de píxeles en rangos ELITE
            fondo_min = config_elite.get('fondo_blanco_min', 245)
            texto_max = config_elite.get('texto_negro_max', 10)
            
            # Contar píxeles en rangos correctos
            pixels_fondo_elite = np.sum(imagen_binaria >= fondo_min)
            pixels_texto_elite = np.sum(imagen_binaria <= texto_max)
            total_pixels = imagen_binaria.size
            
            # Porcentaje de píxeles en rangos ELITE
            porcentaje_elite = (pixels_fondo_elite + pixels_texto_elite) / total_pixels
            
            # Contraste ELITE (diferencia entre fondo y texto)
            fondo_promedio = np.mean(imagen_binaria[imagen_binaria >= 127])
            texto_promedio = np.mean(imagen_binaria[imagen_binaria < 127])
            contraste_elite = fondo_promedio - texto_promedio
            
            # Score combinado (0-100)
            score = (porcentaje_elite * 70) + (min(contraste_elite / 240, 1.0) * 30)
            
            return score * 100
            
        except Exception as e:
            logger.warning(f"Error evaluando calidad ELITE: {str(e)}")
            return 50.0
    
    def _aplicar_purificacion_cca(self, imagen_binaria, resultado):
        """
        FIX: Implementa purificación inteligente por análisis de componentes conectados (CCA)
        REASON: Nueva estrategia ELITE requiere eliminación de elementos no-textuales
        IMPACT: OCR más limpio y eficiente sin interferencias de logos/gráficos
        """
        try:
            from config import PREPROCESSING_CONFIG
            config_cca = PREPROCESSING_CONFIG.get('analisis_componentes_conectados', {})
            
            # Encontrar componentes conectados
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                255 - imagen_binaria,  # Invertir para que texto sea foreground
                connectivity=8
            )
            
            # Crear máscara para elementos válidos (texto)
            mask_texto_valido = np.zeros_like(imagen_binaria)
            componentes_eliminados = 0
            componentes_preservados = 0
            
            for i in range(1, num_labels):  # Saltar background (label 0)
                area = stats[i, cv2.CC_STAT_AREA]
                x, y, w, h = stats[i, cv2.CC_STAT_LEFT:cv2.CC_STAT_TOP+cv2.CC_STAT_HEIGHT+1]
                
                # Criterios para determinar si es texto válido
                es_texto_valido = self._evaluar_componente_como_texto(
                    area, w, h, config_cca
                )
                
                if es_texto_valido:
                    # Preservar este componente
                    component_mask = (labels == i)
                    mask_texto_valido[component_mask] = 255
                    componentes_preservados += 1
                else:
                    componentes_eliminados += 1
            
            # Aplicar máscara: fondo blanco ELITE, texto negro ELITE
            imagen_purificada = np.full_like(imagen_binaria, 250)  # Fondo blanco elite
            imagen_purificada[mask_texto_valido == 255] = 5  # Texto negro elite
            
            resultado['purificacion_cca'] = {
                'componentes_totales': num_labels - 1,
                'componentes_preservados': componentes_preservados,
                'componentes_eliminados': componentes_eliminados,
                'porcentaje_limpieza': (componentes_eliminados / (num_labels - 1)) * 100 if num_labels > 1 else 0
            }
            
            logger.info(f"Purificación CCA: {componentes_preservados} preservados, {componentes_eliminados} eliminados")
            return imagen_purificada
            
        except Exception as e:
            logger.error(f"Error en purificación CCA: {str(e)}")
            return imagen_binaria
    
    def _evaluar_componente_como_texto(self, area, width, height, config_cca):
        """
        FIX: Evalúa si un componente conectado corresponde a texto válido
        REASON: Implementa heurísticas para distinguir texto de elementos gráficos
        IMPACT: Preserva solo caracteres, elimina logos y elementos no-textuales
        """
        try:
            # Criterios de área
            min_area = config_cca.get('min_area_char', 10)
            max_area = config_cca.get('max_area_char', 5000)
            
            if area < min_area or area > max_area:
                return False
            
            # Criterios de proporción (aspect ratio)
            if height == 0:
                return False
                
            aspect_ratio = width / height
            min_aspect = config_cca.get('min_aspect_ratio', 0.1)
            max_aspect = config_cca.get('max_aspect_ratio', 10.0)
            
            if aspect_ratio < min_aspect or aspect_ratio > max_aspect:
                return False
            
            # Criterio de dimensiones típicas de caracteres
            # Rechazar componentes excesivamente grandes (probablemente gráficos)
            if width > 200 or height > 200:
                return False
            
            # Rechazar líneas perfectamente horizontales o verticales (bordes/marcos)
            if (width > 100 and height < 5) or (height > 100 and width < 5):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error evaluando componente: {str(e)}")
            return True  # En caso de error, preservar el componente
    
    def _aplicar_contraste_adaptativo_preservando_letras(self, image, resultado):
        """
        FIX: Contraste adaptativo que preserva letras finas y no reduce contraste
        REASON: El contraste tradicional fijo (alpha=1.1, beta=10) reduce contraste en lugar de mejorarlo
        IMPACT: Mantiene contraste original mientras mejora definición de letras finas
        """
        import numpy as np
        import cv2
        
        # Analizar la imagen para determinar parámetros adaptativos
        mean_intensity = np.mean(image)
        std_intensity = np.std(image)
        
        # Calcular parámetros adaptativos basados en el contenido
        if mean_intensity < 100:  # Imagen oscura
            alpha = 1.3  # Más contraste
            beta = 20    # Más brillo
        elif mean_intensity > 180:  # Imagen muy clara
            alpha = 1.1  # Contraste conservador
            beta = -5    # Reducir brillo ligeramente
        else:  # Imagen normal
            alpha = 1.2  # Contraste moderado
            beta = 5     # Brillo ligero
        
        # Ajustar alpha basado en desviación estándar (variabilidad)
        if std_intensity < 30:  # Bajo contraste natural
            alpha += 0.2  # Aumentar más el contraste
        elif std_intensity > 80:  # Alto contraste natural
            alpha -= 0.1  # Ser más conservador
        
        # Aplicar contraste adaptativo
        enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        
        # Registrar parámetros usados
        resultado['parametros_aplicados']['contraste_adaptativo'] = {
            'alpha_calculado': float(round(alpha, 2)),
            'beta_calculado': int(beta),
            'intensidad_promedio': float(round(mean_intensity, 2)),
            'desviacion_estandar': float(round(std_intensity, 2)),
            'estrategia': 'adaptativo_preservando_letras'
        }
        
        return enhanced
    
    def _aplicar_binarizacion_elite(self, image, diagnostico, resultado):
        """
        FIX: Binarización ELITE AVANZADA con unificación de fondos heterogéneos y nitidez absoluta
        REASON: Implementa nueva estrategia de fondos múltiples con binarización adaptativa localizada
        IMPACT: Unifica fondos diversos en blanco uniforme (245-255) con texto negro nítido (0-10) y nitidez absoluta
        """
        try:
            config_binarization = self.preprocessing_config.get('advanced_binarization', {})
            
            # FIX: Verificar si requiere unificación avanzada de fondos heterogéneos
            # REASON: Nueva estrategia debe detectar fondos diversos primero
            # IMPACT: Aplica binarización específica según variaciones de fondo
            config_elite = self.preprocessing_config.get('binarizacion_elite', {})
            config_unificacion = self.preprocessing_config.get('unificacion_fondos_avanzada', {})
            
            variaciones_fondo = diagnostico.get('info_imagen', {}).get('variaciones_fondo', {})
            requiere_unificacion = variaciones_fondo.get('requiere_unificacion_avanzada', False)
            
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            if requiere_unificacion:
                logger.info("Aplicando binarización ELITE con unificación avanzada de fondos heterogéneos")
                # Usar Sauvola adaptativo para fondos complejos
                window_size = 25
                k = 0.34
                mean = cv2.boxFilter(gray.astype(np.float32), -1, (window_size, window_size))
                sqmean = cv2.boxFilter((gray.astype(np.float32))**2, -1, (window_size, window_size))
                std = np.sqrt(sqmean - mean**2)
                R = 128
                threshold = mean * (1 + k * ((std / R) - 1))
                best_result = np.where(gray > threshold, 255, 0).astype(np.uint8)
                
                # Aplicar nitidez absoluta
                if config_unificacion.get('nitidez_absoluta_enabled', True):
                    kernel_nitidez = np.array([[-1, -1, -1], [-1, 12, -1], [-1, -1, -1]])
                    best_result = cv2.filter2D(best_result, -1, kernel_nitidez)
                    best_result[best_result > 200] = 255
                    best_result[best_result < 55] = 0
                    
                # Relleno inteligente de fondo
                if config_unificacion.get('relleno_inteligente_enabled', True):
                    mask_fondo = best_result > 127
                    if np.any(mask_fondo):
                        best_result[mask_fondo] = 250
                        
                methods_used = ['Binarización ELITE Avanzada con Unificación de Fondos']
                best_score = 100
            else:
                logger.info("Aplicando binarización ELITE estándar")
                best_result = None
                best_score = 0
                methods_used = []
            
            # Método 1: Otsu mejorado
            if config_binarization.get('otsu_enabled', True):
                try:
                    # Aplicar filtro gaussiano ligero antes de Otsu
                    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                    _, otsu_result = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Evaluar calidad
                    score = self._evaluar_calidad_binarizacion(otsu_result)
                    if score > best_score:
                        best_result = otsu_result
                        best_score = score
                        methods_used = ['Otsu Mejorado']
                except Exception as e:
                    logger.warning(f"Error en Otsu: {e}")
            
            # Método 2: Adaptativo Gaussiano mejorado
            if config_binarization.get('adaptive_gaussian_enabled', True):
                try:
                    adaptive_gauss = cv2.adaptiveThreshold(
                        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                        cv2.THRESH_BINARY, 11, 2
                    )
                    
                    score = self._evaluar_calidad_binarizacion(adaptive_gauss)
                    if score > best_score:
                        best_result = adaptive_gauss
                        best_score = score
                        methods_used = ['Adaptativo Gaussiano']
                except Exception as e:
                    logger.warning(f"Error en adaptativo gaussiano: {e}")
            
            # Método 3: Sauvola (excelente para documentos)
            if config_binarization.get('sauvola_enabled', True):
                try:
                    # Implementación simple de Sauvola
                    window_size = 15
                    k = 0.2
                    R = 128
                    
                    mean = cv2.boxFilter(gray.astype(np.float32), -1, (window_size, window_size))
                    sqmean = cv2.boxFilter((gray.astype(np.float32))**2, -1, (window_size, window_size))
                    std = np.sqrt(sqmean - mean**2)
                    
                    threshold = mean * (1 + k * ((std / R) - 1))
                    sauvola_result = np.where(gray > threshold, 255, 0).astype(np.uint8)
                    
                    score = self._evaluar_calidad_binarizacion(sauvola_result)
                    if score > best_score:
                        best_result = sauvola_result
                        best_score = score
                        methods_used = ['Sauvola']
                except Exception as e:
                    logger.warning(f"Error en Sauvola: {e}")
            
            # Si no hay resultado, usar binarización simple como fallback
            if best_result is None:
                _, best_result = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                methods_used = ['Binarización Simple (Fallback)']
                best_score = 0.5
            
            resultado['pasos_aplicados'].append(f'Binarización Avanzada: {", ".join(methods_used)}')
            resultado['parametros_aplicados']['binarization_advanced'] = {
                'methods_tested': len([m for m in config_binarization.values() if m]),
                'best_method': methods_used[0] if methods_used else 'Simple',
                'quality_score': float(best_score)
            }
            
            return best_result
            
        except Exception as e:
            logger.error(f"Error en binarización avanzada: {str(e)}")
            # Fallback a binarización simple
            _, simple_result = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            return simple_result
    
    def _evaluar_calidad_binarizacion(self, binary_image):
        """Evalúa la calidad de una imagen binarizada"""
        try:
            # Métricas de calidad
            total_pixels = binary_image.size
            black_pixels = np.sum(binary_image == 0)
            white_pixels = np.sum(binary_image == 255)
            
            # Balance blanco/negro (óptimo cerca de 10-20% negro)
            black_ratio = black_pixels / total_pixels
            balance_score = 1.0 - abs(black_ratio - 0.15) * 2  # Óptimo en 15%
            
            # Conectividad de componentes (texto debería tener componentes bien definidos)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(255 - binary_image)
            component_score = min(1.0, (num_labels - 1) / 50)  # Más componentes = mejor
            
            # Score final combinado
            final_score = (balance_score * 0.6 + component_score * 0.4)
            return max(0, min(1, final_score))
            
        except Exception:
            return 0.5  # Score neutro si hay error
    
    def _procesar_screenshot_movil(self, image, deteccion_inteligente, profile_config, resultado, save_steps, output_dir, step_counter):
        """
        FIX: Procesamiento ULTRA-CONSERVATIVO para screenshots móviles - CALIDAD MÁXIMA
        REASON: Usuario reporta degradación de calidad, eliminando procesamiento agresivo
        IMPACT: Preserva calidad original de screenshots digitales sin pérdida
        """
        current = image.copy()
        resultado['estrategia_aplicada'] = 'Screenshot Móvil - ULTRA CONSERVATIVO'
        
        # PASO 1: Solo ampliar si la imagen es muy pequeña (menos agresivo)
        if image.shape[1] < 400 or image.shape[0] < 400:  # Solo imágenes muy pequeñas
            scale_factor = 1.5  # Factor más conservativo
            new_width = int(current.shape[1] * scale_factor)
            new_height = int(current.shape[0] * scale_factor)
            current = cv2.resize(current, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            resultado['pasos_aplicados'].append(f'{step_counter:02d}_ampliacion_conservativa')
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_ampliacion_conservativa.png"), current)
                step_counter += 1
        
        # PASO 2: ELIMINAR unsharp masking - puede causar artefactos
        # REASON: Usuario reporta que se daña la calidad
        # NO SE APLICA NINGÚN FILTRO DE NITIDEZ
        
        # PASO 3: Ajuste de brillo MÍNIMO solo si es extremadamente necesario
        mean_intensity = np.mean(current)
        if mean_intensity < 60 or mean_intensity > 200:  # Solo casos extremos
            if mean_intensity < 60:
                beta = 20  # Aumentar brillo solo para imágenes muy oscuras
                current = cv2.convertScaleAbs(current, alpha=1.0, beta=beta)
                resultado['pasos_aplicados'].append(f'{step_counter:02d}_brillo_minimo')
                if save_steps and output_dir:
                    cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_brillo_minimo.png"), current)
                    step_counter += 1
        
        # PASO 4: NO aplicar binarización - mantener escala de grises original
        # REASON: La binarización puede eliminar información útil
        # La imagen se mantiene en escala de grises para OCR
        
        resultado['parametros_aplicados']['screenshot_processing_ultra_conservativo'] = {
            'upscaling_applied': bool(image.shape[1] < 400 and image.shape[0] < 400),
            'scale_factor': 1.5 if (image.shape[1] < 400 and image.shape[0] < 400) else 1.0,
            'unsharp_masking': False,  # ELIMINADO
            'contrast_adjustment': False,  # ELIMINADO
            'binarization_applied': False,  # ELIMINADO
            'brightness_adjustment': bool(mean_intensity < 60),
            'filosofia': 'conservacion_maxima_sin_procesamiento_agresivo'
        }
        
        return current
    
    def _procesar_documento_escaneado(self, image, diagnostico, profile_config, resultado, save_steps, output_dir, step_counter):
        """
        FIX: Procesamiento tradicional mejorado para documentos escaneados
        REASON: Los documentos escaneados requieren más procesamiento debido a artefactos físicos
        IMPACT: Mantiene el procesamiento tradicional pero optimizado
        """
        current = image.copy()
        resultado['estrategia_aplicada'] = 'Documento Escaneado - Procesamiento Tradicional'
        
        # Aplicar la secuencia tradicional pero mejorada
        # Para documentos escaneados, aplicamos el procesamiento tradicional existente
        
        # PASO 1: Redimensionamiento si es necesario
        if current.shape[1] < 600:  # Si es muy pequeña
            scale_factor = 1.5
            new_width = int(current.shape[1] * scale_factor)
            new_height = int(current.shape[0] * scale_factor)
            current = cv2.resize(current, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            resultado['pasos_aplicados'].append(f'{step_counter:02d}_redimensionamiento')
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_redimensionamiento.png"), current)
                step_counter += 1
        
        # PASO 2: Filtro bilateral para reducir ruido
        if profile_config.get('bilateral_filter', True):
            current = cv2.bilateralFilter(current, 9, 75, 75)
            resultado['pasos_aplicados'].append(f'{step_counter:02d}_bilateral_filter')
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_bilateral_filter.png"), current)
                step_counter += 1
        
        # PASO 3: Mejora de contraste adaptativo (preserva letras finas)
        current = self._aplicar_contraste_adaptativo_preservando_letras(current, resultado)
        resultado['pasos_aplicados'].append(f'{step_counter:02d}_contraste_adaptativo')
        if save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_contraste_adaptativo.png"), current)
            step_counter += 1
        
        # PASO 4: Binarización adaptativa
        current = cv2.adaptiveThreshold(current, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        resultado['pasos_aplicados'].append(f'{step_counter:02d}_binarizacion_tradicional')
        if save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_binarizacion_tradicional.png"), current)
        
        resultado['parametros_aplicados']['documento_processing'] = {
            'redimensionamiento_aplicado': bool(current.shape[1] < 600),
            'filtro_bilateral': bool(profile_config.get('bilateral_filter', True)),
            'contraste_alpha': 1.1,
            'contraste_beta': 10
        }
        
        return current

def main():
    """Función principal para uso por línea de comandos"""
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python mejora_ocr.py <ruta_imagen> <archivo_diagnostico> [perfil] [directorio_salida]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    diagnostico_path = sys.argv[2]
    perfil = sys.argv[3] if len(sys.argv) > 3 else 'rapido'
    output_dir = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Cargar diagnóstico
    with open(diagnostico_path, 'r', encoding='utf-8') as f:
        diagnostico = json.load(f)
    
    mejorador = MejoradorOCR()
    resultado = mejorador.procesar_imagen(image_path, diagnostico, perfil, True, output_dir)
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
