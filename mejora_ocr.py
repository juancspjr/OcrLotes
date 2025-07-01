"""
Módulo de mejora y preprocesamiento adaptativo de imágenes para OCR
Aplica técnicas avanzadas de procesamiento basadas en diagnóstico
"""

import cv2
import numpy as np
import json
import logging
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
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
            return resultado_procesamiento
            
        except Exception as e:
            logger.error(f"Error en procesamiento de imagen: {str(e)}")
            return {'error': str(e)}
    
    def _aplicar_secuencia_procesamiento(self, image, diagnostico, profile_config, resultado, save_steps, output_dir):
        """Aplica la secuencia completa de procesamiento"""
        current = image.copy()
        step_counter = 2
        
        # 1. Redimensionamiento si es necesario
        if max(current.shape) > self.preprocessing_config['resize_max_dimension']:
            current = self._aplicar_redimensionamiento(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_redimensionado.png"), current)
                step_counter += 1
        
        # 2. Corrección de sesgo (deskew) si es necesario
        if (profile_config['deskew'] and 
            diagnostico.get('geometria_orientacion', {}).get('requiere_deskew', False)):
            current = self._aplicar_deskew(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_deskew.png"), current)
                step_counter += 1
        
        # 3. Filtro bilateral para reducir ruido preservando bordes
        if profile_config['bilateral_filter']:
            current = self._aplicar_filtro_bilateral(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_bilateral.png"), current)
                step_counter += 1
        
        # 4. Eliminación de ruido gaussiano
        if profile_config['noise_removal_iterations'] > 0:
            current = self._aplicar_eliminacion_ruido(current, profile_config, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_denoise.png"), current)
                step_counter += 1
        
        # 5. Mejora de contraste adaptativa
        current = self._aplicar_mejora_contraste(current, diagnostico, resultado)
        if save_steps and output_dir:
            cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_contraste.png"), current)
            step_counter += 1
        
        # 6. Binarización adaptativa
        if profile_config['adaptive_threshold']:
            current = self._aplicar_binarizacion_adaptativa(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_binarizacion.png"), current)
                step_counter += 1
        
        # 7. Operaciones morfológicas para limpiar
        if profile_config['morphology_operations']:
            current = self._aplicar_morfologia(current, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_morfologia.png"), current)
                step_counter += 1
        
        # 8. Nitidez final si es necesario
        if profile_config['sharpening']:
            current = self._aplicar_nitidez(current, diagnostico, resultado)
            if save_steps and output_dir:
                cv2.imwrite(str(Path(output_dir) / f"{step_counter:02d}_nitidez.png"), current)
                step_counter += 1
        
        return current
    
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
        """Corrige el sesgo de la imagen"""
        # FIX: Conservación extrema de caracteres - deskew solo para documentos escaneados
        # REASON: Las capturas de pantalla ya están perfectamente alineadas, deskew introduce distorsión
        # IMPACT: Elimina rotaciones innecesarias que degradan la calidad de texto digital
        
        geometria = diagnostico.get('geometria_orientacion', {})
        angle = geometria.get('sesgo_estimado', 0)
        
        # Detección inteligente: solo aplicar deskew si hay sesgo significativo Y no es captura de pantalla
        imagen_info = diagnostico.get('imagen_info', {})
        width = imagen_info.get('ancho', 0)
        height = imagen_info.get('alto', 0)
        
        # Heurística para detectar capturas de pantalla (proporciones típicas de pantalla)
        aspect_ratio = width / height if height > 0 else 1
        is_screenshot = (
            aspect_ratio > 1.5 or  # Pantalla wide
            width > 1000 or        # Resolución alta típica de screenshots
            height > 600           # Resolución mínima de screenshots
        )
        
        # Solo aplicar deskew si:
        # 1. Hay sesgo significativo (>2 grados para ser más conservador)
        # 2. NO es una captura de pantalla
        # 3. O el sesgo es extremo (>5 grados) incluso en screenshots
        should_deskew = (
            abs(angle) > 2.0 and not is_screenshot
        ) or abs(angle) > 5.0
        
        if should_deskew:
            h, w = image.shape
            center = (w // 2, h // 2)
            
            # Crear matriz de rotación
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Calcular nuevas dimensiones
            cos = np.abs(M[0, 0])
            sin = np.abs(M[0, 1])
            new_w = int((h * sin) + (w * cos))
            new_h = int((h * cos) + (w * sin))
            
            # Ajustar matriz de traslación
            M[0, 2] += (new_w / 2) - center[0]
            M[1, 2] += (new_h / 2) - center[1]
            
            # Aplicar rotación con interpolación de alta calidad
            rotated = cv2.warpAffine(image, M, (new_w, new_h), 
                                   flags=cv2.INTER_LANCZOS4,  # Mejor calidad
                                   borderMode=cv2.BORDER_REPLICATE)
            
            resultado['pasos_aplicados'].append('Corrección de sesgo')
            resultado['parametros_aplicados']['deskew'] = {
                'angulo_corregido': round(angle, 2),
                'dimensiones_nuevas': (new_w, new_h),
                'tipo_imagen': 'escaneada' if not is_screenshot else 'screenshot_sesgo_extremo'
            }
            
            return rotated
        else:
            # Log por qué no se aplicó deskew
            resultado['parametros_aplicados']['deskew_omitido'] = {
                'razon': 'captura_de_pantalla' if is_screenshot else 'sesgo_minimo',
                'angulo_detectado': round(angle, 2),
                'es_screenshot': is_screenshot,
                'dimensiones': f"{width}x{height}"
            }
        
        return image
    
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
        """Aplica binarización adaptativa"""
        # Usar parámetros adaptativos basados en la imagen
        calidad = diagnostico.get('calidad_imagen', {})
        brillo = calidad.get('brillo_promedio', 128)
        
        # Ajustar parámetros según brillo
        if brillo < 80:
            block_size, C = 15, 5
        elif brillo > 180:
            block_size, C = 9, 1
        else:
            block_size, C = 11, 2
        
        # Asegurar que block_size sea impar
        if block_size % 2 == 0:
            block_size += 1
        
        binary = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, block_size, C
        )
        
        resultado['pasos_aplicados'].append('Binarización adaptativa')
        resultado['parametros_aplicados']['binarizacion'] = {
            'block_size': block_size,
            'C': C,
            'brillo_detectado': round(brillo, 1)
        }
        
        return binary
    
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
