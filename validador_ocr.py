"""
Módulo de validación y diagnóstico de imágenes para OCR
Analiza la calidad de la imagen y proporciona métricas detalladas
"""

import cv2
import numpy as np
import json
import logging
from pathlib import Path
from skimage import measure, filters
from PIL import Image, ImageStat
import config

# Configurar logging
# FIX: Configuración directa para evitar problemas con tipos de datos en LOGGING_CONFIG
# REASON: Algunos valores en config.LOGGING_CONFIG pueden no ser compatibles con logging.basicConfig
# IMPACT: Garantiza inicialización correcta del logging sin errores de tipo
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidadorOCR:
    """Clase para validar y diagnosticar la calidad de imágenes para OCR"""
    
    def __init__(self):
        self.thresholds = config.IMAGE_QUALITY_THRESHOLDS
        
    def analizar_imagen(self, image_path):
        """
        Analiza una imagen y genera un diagnóstico completo
        
        Args:
            image_path: Ruta a la imagen a analizar
            
        Returns:
            dict: Diccionario con métricas y diagnósticos
        """
        try:
            # Cargar imagen
            image_cv = cv2.imread(str(image_path))
            image_pil = Image.open(image_path)
            
            if image_cv is None:
                raise ValueError(f"No se puede cargar la imagen: {image_path}")
            
            # Convertir a escala de grises para análisis
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            
            # Realizar todas las mediciones
            diagnostico = {
                'imagen_info': self._obtener_info_basica(image_pil, gray),
                'calidad_imagen': self._analizar_calidad(gray),
                'deteccion_texto': self._detectar_regiones_texto(gray),
                'ruido_artefactos': self._analizar_ruido(gray),
                'geometria_orientacion': self._analizar_geometria(gray),
                'deteccion_inteligente': self._detectar_tipo_imagen_inteligente(gray, image_pil),  # FIX: Nueva detección inteligente
                'recomendaciones': {}
            }
            
            # Generar recomendaciones basadas en el análisis
            diagnostico['recomendaciones'] = self._generar_recomendaciones(diagnostico)
            
            # Calcular puntuación general
            diagnostico['puntuacion_general'] = self._calcular_puntuacion_general(diagnostico)
            
            logger.info(f"Análisis completado para {image_path}")
            return diagnostico
            
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {str(e)}")
            return {'error': str(e)}
    
    def _obtener_info_basica(self, image_pil, gray):
        """Obtiene información básica de la imagen"""
        stats = ImageStat.Stat(image_pil)
        
        # FIX: Convertir todos los valores NumPy a tipos nativos de Python para serialización JSON
        # REASON: Los tipos uint8, int64, float64 de NumPy no son serializables por JSON
        # IMPACT: Permite que el diagnóstico se serialice correctamente sin errores
        # FIX: Agregar análisis de histograma para binarización ELITE
        # REASON: Necesario para determinar rangos de fondo y texto según nueva estrategia
        # IMPACT: Permite binarización optimizada con rangos precisos
        histogram = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        
        return {
            'ancho': int(gray.shape[1]),
            'alto': int(gray.shape[0]),
            'resolucion_total': int(gray.shape[0] * gray.shape[1]),
            'canales': len(image_pil.getbands()),
            'modo': image_pil.mode,
            'formato': image_pil.format if image_pil.format else 'unknown',
            'brillo_promedio': float(np.mean(gray)),
            'desviacion_brillo': float(np.std(gray)),
            'rango_dinamico': float(np.max(gray) - np.min(gray)),
            'histogram': histogram.tolist(),  # Convertir a lista para JSON
            'histogram_analysis': self._analizar_histograma_para_binarizacion(histogram)
        }
    
    def _analizar_calidad(self, gray):
        """Analiza la calidad general de la imagen"""
        # Calcular contraste usando desviación estándar
        contraste = np.std(gray)
        
        # Detectar blur usando varianza del Laplaciano
        blur_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calcular histograma para analizar distribución de intensidades
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_normalized = hist.flatten() / hist.sum()
        
        # Entropía como medida de información
        entropy = -np.sum(hist_normalized * np.log2(hist_normalized + 1e-7))
        
        # Gradiente promedio como medida de nitidez
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradiente_promedio = np.mean(np.sqrt(sobel_x**2 + sobel_y**2))
        
        return {
            'contraste': float(contraste),
            'blur_variance': float(blur_variance),
            'entropy': float(entropy),
            'gradiente_promedio': float(gradiente_promedio),
            'brillo_promedio': float(np.mean(gray)),
            'uniformidad_brillo': float(np.std(gray)),
            'calificacion_calidad': self._calificar_calidad(contraste, blur_variance, entropy)
        }
    
    def _detectar_regiones_texto(self, gray):
        """Detecta y analiza regiones que podrían contener texto"""
        # Aplicar detección de bordes para encontrar regiones con texto
        edges = cv2.Canny(gray, 50, 150)
        
        # Operaciones morfológicas para conectar componentes de texto
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analizar contornos para identificar posibles regiones de texto
        text_regions = []
        total_text_area = 0
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / h if h > 0 else 0
            
            # Filtrar regiones que podrían ser texto (ratio y tamaño apropiados)
            if (area > 100 and 0.1 < aspect_ratio < 10 and 
                w > 10 and h > 5 and h < gray.shape[0] * 0.3):
                text_regions.append({
                    'x': int(x), 'y': int(y), 
                    'width': int(w), 'height': int(h),
                    'area': int(area),
                    'aspect_ratio': float(aspect_ratio)
                })
                total_text_area += area
        
        # Calcular densidad de texto
        image_area = gray.shape[0] * gray.shape[1]
        text_density = total_text_area / image_area if image_area > 0 else 0
        
        return {
            'regiones_detectadas': len(text_regions),
            'area_total_texto': int(total_text_area),
            'densidad_texto': float(text_density),
            'regiones': text_regions[:20],  # Limitar a 20 regiones para el JSON
            'cobertura_texto_porcentaje': float(text_density * 100)
        }
    
    def _analizar_ruido(self, gray):
        """Analiza el nivel de ruido en la imagen"""
        # Aplicar filtro Gaussiano y calcular diferencia
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = cv2.absdiff(gray, blurred)
        
        # Calcular métricas de ruido
        noise_level = np.mean(noise)
        noise_std = np.std(noise)
        
        # Detectar píxeles con ruido significativo
        noise_threshold = np.mean(noise) + 2 * np.std(noise)
        noisy_pixels = np.sum(noise > noise_threshold)
        noise_percentage = (noisy_pixels / (gray.shape[0] * gray.shape[1])) * 100
        
        # Analizar uniformidad usando filtro de mediana
        median_filtered = cv2.medianBlur(gray, 5)
        uniformity = np.mean(cv2.absdiff(gray, median_filtered))
        
        return {
            'nivel_ruido': float(noise_level),
            'desviacion_ruido': float(noise_std),
            'porcentaje_pixeles_ruidosos': float(noise_percentage),
            'uniformidad': float(uniformity),
            'calificacion_ruido': self._calificar_ruido(noise_level, noise_percentage)
        }
    
    def _analizar_geometria(self, gray):
        """Analiza la geometría y orientación de la imagen"""
        # Detectar líneas principales usando transformada de Hough
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        angles = []
        if lines is not None:
            for line in lines[:50]:  # Limitar análisis a 50 líneas principales
                rho, theta = line[0]
                angle = np.degrees(theta) - 90  # Convertir a ángulo de inclinación
                angles.append(angle)
        
        # Calcular sesgo predominante
        if angles:
            angle_hist, bins = np.histogram(angles, bins=36, range=(-90, 90))
            dominant_angle_idx = np.argmax(angle_hist)
            estimated_skew = float((bins[dominant_angle_idx] + bins[dominant_angle_idx + 1]) / 2)
        else:
            estimated_skew = 0.0
        
        # Detectar simetría
        height, width = gray.shape
        left_half = gray[:, :width//2]
        right_half = cv2.flip(gray[:, width//2:], 1)
        
        # Redimensionar para comparación
        min_width = min(left_half.shape[1], right_half.shape[1])
        left_resized = cv2.resize(left_half, (min_width, height))
        right_resized = cv2.resize(right_half, (min_width, height))
        
        symmetry_score = cv2.matchTemplate(left_resized, right_resized, cv2.TM_CCOEFF_NORMED)[0][0]
        
        return {
            'sesgo_estimado': float(estimated_skew),
            'lineas_detectadas': len(angles),
            'simetria_horizontal': float(symmetry_score),
            'relacion_aspecto': float(gray.shape[1] / gray.shape[0]),
            'requiere_deskew': bool(abs(estimated_skew) > 2),
            'orientacion_correcta': bool(abs(estimated_skew) < 5)
        }
    
    def _calificar_calidad(self, contraste, blur_variance, entropy):
        """Califica la calidad general de la imagen"""
        score = 0
        
        # Puntuación por contraste
        if contraste > 60:
            score += 40
        elif contraste > 30:
            score += 25
        elif contraste > 15:
            score += 10
        
        # Puntuación por nitidez (blur)
        if blur_variance > 500:
            score += 40
        elif blur_variance > 100:
            score += 25
        elif blur_variance > 50:
            score += 10
        
        # Puntuación por entropía (contenido de información)
        if entropy > 6:
            score += 20
        elif entropy > 4:
            score += 15
        elif entropy > 2:
            score += 5
        
        return min(100, score)
    
    def _detectar_tipo_imagen_inteligente(self, gray, image_pil):
        """
        FIX: Implementa detección inteligente de tipo de imagen (screenshot vs documento escaneado)
        REASON: Necesario para aplicar rutas de procesamiento especializadas según el tipo de imagen
        IMPACT: Mejora dramática en la precisión OCR al aplicar técnicas específicas para cada tipo
        """
        # Análisis de histograma para detectar esquema de color
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Detectar si es texto claro sobre fondo oscuro
        dark_pixels = np.sum(hist[:128])  # Píxeles oscuros
        light_pixels = np.sum(hist[128:])  # Píxeles claros
        total_pixels = gray.shape[0] * gray.shape[1]
        
        dark_percentage = (dark_pixels / total_pixels) * 100
        light_percentage = (light_pixels / total_pixels) * 100
        
        # Determinar esquema de color
        if dark_percentage > 70 and light_percentage < 30:
            esquema_color = "texto_claro_fondo_oscuro"
            inversion_requerida = True
        else:
            esquema_color = "texto_oscuro_fondo_claro" 
            inversion_requerida = False
        
        # Detectar elementos de UI móvil
        height, width = gray.shape
        aspect_ratio = width / height
        
        # Analizar bandas uniformes en bordes (barras de estado/navegación)
        top_band = gray[:min(50, height//10), :]
        bottom_band = gray[max(height-50, height-height//10):, :]
        
        top_uniformity = np.std(top_band) < 10  # Muy poca variación = barra uniforme
        bottom_uniformity = np.std(bottom_band) < 10
        
        ui_elements_detectados = top_uniformity or bottom_uniformity
        
        # Determinar tipo de imagen
        # Screenshots móviles típicamente tienen aspect ratio vertical y elementos UI
        is_mobile_screenshot = (
            (aspect_ratio < 0.8 and ui_elements_detectados) or  # Vertical con UI
            (esquema_color == "texto_claro_fondo_oscuro") or    # Tema oscuro
            (width < 500 and height > 800)  # Dimensiones típicas de móvil
        )
        
        tipo_imagen = "screenshot_movil" if is_mobile_screenshot else "documento_escaneado"
        
        # Análisis adicional de calidad digital vs escaneado
        # Los screenshots tienen bordes más definidos y menos ruido
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (width * height)
        
        # Los documentos escaneados tienen más ruido y bordes menos definidos
        noise_estimate = np.std(cv2.GaussianBlur(gray, (3, 3), 0) - gray)
        
        calidad_digital = edge_density > 0.02 and noise_estimate < 3
        
        return {
            'tipo_imagen': tipo_imagen,
            'esquema_color': esquema_color,
            'inversion_requerida': bool(inversion_requerida),
            'ui_elements_detectados': bool(ui_elements_detectados),
            'aspect_ratio': float(aspect_ratio),
            'calidad_digital': bool(calidad_digital),
            'dark_percentage': float(dark_percentage),
            'light_percentage': float(light_percentage),
            'edge_density': float(edge_density),
            'noise_estimate': float(noise_estimate),
            'confianza_deteccion': float(
                (0.4 if ui_elements_detectados else 0) +
                (0.3 if esquema_color == "texto_claro_fondo_oscuro" else 0) +
                (0.2 if aspect_ratio < 0.8 else 0) +
                (0.1 if calidad_digital else 0)
            )
        }
    
    def _calificar_ruido(self, noise_level, noise_percentage):
        """Califica el nivel de ruido en la imagen"""
        if noise_percentage < 5 and noise_level < 10:
            return "Bajo"
        elif noise_percentage < 15 and noise_level < 25:
            return "Moderado"
        else:
            return "Alto"
    
    def _generar_recomendaciones(self, diagnostico):
        """Genera recomendaciones basadas en el diagnóstico"""
        recomendaciones = {
            'perfil_recomendado': 'rapido',
            'aplicar_deskew': False,
            'nivel_denoise': 'moderado',
            'ajuste_contraste': False,
            'filtro_bilateral': True,
            'prioridades': []
        }
        
        calidad = diagnostico['calidad_imagen']
        ruido = diagnostico['ruido_artefactos']
        geometria = diagnostico['geometria_orientacion']
        
        # Determinar perfil recomendado
        if calidad['calificacion_calidad'] > 80 and ruido['calificacion_ruido'] == 'Bajo':
            recomendaciones['perfil_recomendado'] = 'ultra_rapido'
        elif calidad['calificacion_calidad'] < 40 or ruido['calificacion_ruido'] == 'Alto':
            recomendaciones['perfil_recomendado'] = 'normal'
        
        # Recomendaciones específicas
        if geometria['requiere_deskew']:
            recomendaciones['aplicar_deskew'] = True
            recomendaciones['prioridades'].append('Corrección de sesgo necesaria')
        
        if calidad['contraste'] < 30:
            recomendaciones['ajuste_contraste'] = True
            recomendaciones['prioridades'].append('Mejorar contraste')
        
        if ruido['calificacion_ruido'] == 'Alto':
            recomendaciones['nivel_denoise'] = 'agresivo'
            recomendaciones['prioridades'].append('Reducción de ruido intensiva')
        
        if calidad['blur_variance'] < 100:
            recomendaciones['prioridades'].append('Aplicar nitidez')
        
        return recomendaciones
    
    def _calcular_puntuacion_general(self, diagnostico):
        """Calcula una puntuación general de la imagen"""
        pesos = {
            'calidad': 0.4,
            'texto': 0.3,
            'ruido': 0.2,
            'geometria': 0.1
        }
        
        # Puntuaciones individuales
        score_calidad = diagnostico['calidad_imagen']['calificacion_calidad']
        score_texto = min(100, diagnostico['deteccion_texto']['densidad_texto'] * 500)
        score_ruido = 100 if diagnostico['ruido_artefactos']['calificacion_ruido'] == 'Bajo' else \
                     60 if diagnostico['ruido_artefactos']['calificacion_ruido'] == 'Moderado' else 20
        score_geometria = 100 if diagnostico['geometria_orientacion']['orientacion_correcta'] else 50
        
        # Puntuación ponderada
        puntuacion_total = (
            score_calidad * pesos['calidad'] +
            score_texto * pesos['texto'] +
            score_ruido * pesos['ruido'] +
            score_geometria * pesos['geometria']
        )
        
        return {
            'total': round(puntuacion_total, 1),
            'calidad': round(score_calidad, 1),
            'texto': round(score_texto, 1),
            'ruido': round(score_ruido, 1),
            'geometria': round(score_geometria, 1),
            'categoria': self._categorizar_puntuacion(puntuacion_total)
        }
    
    def _categorizar_puntuacion(self, puntuacion):
        """Categoriza la puntuación en niveles descriptivos"""
        if puntuacion >= 80:
            return 'Excelente'
        elif puntuacion >= 60:
            return 'Buena'
        elif puntuacion >= 40:
            return 'Regular'
        else:
            return 'Deficiente'
    
    def _analizar_histograma_para_binarizacion(self, histogram):
        """
        FIX: Analiza histograma para determinar rangos óptimos de binarización ELITE
        REASON: Nueva estrategia requiere análisis de tonalidades para fondo blanco y texto negro
        IMPACT: Permite binarización precisa con rangos 245-255 fondo, 0-10 texto
        """
        total_pixels = np.sum(histogram)
        
        # Encontrar picos en el histograma
        picos = []
        for i in range(1, 255):
            if histogram[i] > histogram[i-1] and histogram[i] > histogram[i+1]:
                if histogram[i] > total_pixels * 0.01:  # Al menos 1% del total
                    picos.append((i, histogram[i]))
        
        # Ordenar picos por intensidad de píxeles
        picos.sort(key=lambda x: x[1], reverse=True)
        
        # Identificar rango de fondo (tonos claros) y texto (tonos oscuros)
        fondo_candidato = 255  # Blanco por defecto
        texto_candidato = 0    # Negro por defecto
        
        if len(picos) >= 2:
            # El pico más alto probablemente es el fondo
            fondo_candidato = picos[0][0]
            # El segundo pico más alto probablemente es el texto
            texto_candidato = picos[1][0]
            
            # Asegurar que fondo > texto (fondo más claro que texto)
            if fondo_candidato < texto_candidato:
                fondo_candidato, texto_candidato = texto_candidato, fondo_candidato
        
        # Calcular distribución de intensidades
        intensidades_oscuras = np.sum(histogram[0:85])  # 0-84
        intensidades_medias = np.sum(histogram[85:171])  # 85-170
        intensidades_claras = np.sum(histogram[171:256])  # 171-255
        
        return {
            'picos_principales': [(int(pos), int(intensidad)) for pos, intensidad in picos[:3]],
            'rango_fondo_sugerido': int(fondo_candidato),
            'rango_texto_sugerido': int(texto_candidato),
            'distribucion': {
                'oscuras': float(intensidades_oscuras / total_pixels),
                'medias': float(intensidades_medias / total_pixels),
                'claras': float(intensidades_claras / total_pixels)
            },
            'requiere_inversion': bool(intensidades_oscuras > intensidades_claras),
            'bimodal': len(picos) >= 2 and picos[0][1] > total_pixels * 0.1
        }

def main():
    """Función principal para uso por línea de comandos"""
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python validador_ocr.py <ruta_imagen>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    validador = ValidadorOCR()
    resultado = validador.analizar_imagen(image_path)
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
