"""
Módulo de aplicación de OCR con Tesseract
Extrae texto y datos estructurados con validación de confianza
"""

import cv2
import pytesseract
import json
import re
import logging
from pathlib import Path
import numpy as np
from PIL import Image
import config

# Configurar logging
# FIX: Configuración directa para evitar problemas con tipos de datos en LOGGING_CONFIG
# REASON: Algunos valores en config.LOGGING_CONFIG pueden no ser compatibles con logging.basicConfig
# IMPACT: Garantiza inicialización correcta del logging sin errores de tipo
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AplicadorOCR:
    """Clase para aplicar OCR y extraer datos estructurados"""
    
    def __init__(self):
        self.tesseract_configs = config.TESSERACT_CONFIG
        self.financial_patterns = config.FINANCIAL_PATTERNS
        # FIX: Usar configuración de alta confianza por defecto
        self.confidence_config = config.OCR_CONFIDENCE_CONFIG
        self.quality_thresholds = getattr(config, 'OCR_QUALITY_THRESHOLDS', {})
        
    def extraer_texto(self, image_path, language='spa', config_mode='high_confidence', extract_financial=True, deteccion_inteligente=None):
        """
        Extrae texto de una imagen usando Tesseract OCR con procesamiento dual-pass
        
        Args:
            image_path: Ruta a la imagen procesada
            language: Idioma para OCR
            config_mode: Configuración de Tesseract a usar
            extract_financial: Si extraer datos financieros específicos
            deteccion_inteligente: Información de detección inteligente
            
        Returns:
            dict: Resultados de OCR con texto y datos estructurados, incluyendo dual-pass
        """
        try:
            # Cargar imagen
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"No se puede cargar la imagen: {image_path}")
            
            # Convertir a PIL para Tesseract
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image_rgb)
            else:
                pil_image = Image.fromarray(image)
            
            # FIX: Seleccionar configuración de Tesseract basada en detección inteligente
            # REASON: Optimizar OCR según tipo de imagen detectado
            # IMPACT: Mejora significativa en precisión para screenshots vs documentos escaneados
            if deteccion_inteligente and deteccion_inteligente.get('tipo_imagen') == 'screenshot_movil':
                tesseract_config = self.tesseract_configs.get('screenshot_optimized', self.tesseract_configs['high_confidence'])
                logger.info("Usando configuración optimizada para screenshot móvil")
            else:
                tesseract_config = self.tesseract_configs.get(config_mode, self.tesseract_configs['default'])
            
            logger.info(f"Iniciando OCR con idioma: {language}, modo: {config_mode}")
            
            # FIX: NUEVO - Procesamiento dual-pass con detección de zonas grises
            # REASON: Usuario requiere conservación extrema de caracteres y procesamiento especializado de zonas grises
            # IMPACT: Maximiza extracción de texto y preserva símbolos/espacios
            
            # FIX: Usar configuración especializada para dual-pass que preserva todos los símbolos
            # REASON: Usuario requiere conservación extrema de espacios y símbolos */.- etc.
            # IMPACT: Máxima preservación de caracteres y símbolos en el texto extraído
            tesseract_config_dual = self.tesseract_configs.get('dual_pass_optimized', tesseract_config)
            
            # Ejecutar procesamiento dual-pass
            resultado_dual_pass = self._procesar_dual_pass(image_path, language, config_mode, tesseract_config_dual)
            
            # FIX: Extraer y limpiar texto principal del dual-pass
            # REASON: Aplicar limpieza también al texto del primer pass
            # IMPACT: Consistencia en la limpieza de todo el texto extraído
            texto_completo_crudo = resultado_dual_pass['texto_final_concatenado']
            texto_completo = self._limpiar_y_espaciar_texto(texto_completo_crudo)
            
            # Usar datos OCR del primer pass para estadísticas detalladas
            ocr_data = resultado_dual_pass['primer_pass']['ocr_data']
            
            # Procesar resultados consolidados
            resultado_ocr = {
                'texto_completo': texto_completo,
                # FIX: NUEVO - Incluir información del procesamiento dual-pass
                'dual_pass_info': {
                    'primer_pass_caracteres': resultado_dual_pass['primer_pass']['caracteres'],
                    'segundo_pass_caracteres': resultado_dual_pass['segundo_pass']['caracteres_adicionales'],
                    'zonas_grises_detectadas': resultado_dual_pass['zonas_grises_detectadas'],
                    'zonas_procesadas': resultado_dual_pass['segundo_pass']['zonas_procesadas'],
                    'elementos_detectados': resultado_dual_pass['elementos_detectados']
                },
                'estadisticas_ocr': self._analizar_estadisticas_ocr(ocr_data),
                'palabras_detectadas': self._extraer_palabras_con_confianza(ocr_data),
                'confianza_promedio': self._calcular_confianza_promedio(ocr_data),
                'calidad_extraccion': self._evaluar_calidad_extraccion(ocr_data, texto_completo)
            }
            
            # Extraer datos financieros si se solicita
            if extract_financial:
                resultado_ocr['datos_financieros'] = self._extraer_datos_financieros(texto_completo)
            
            logger.info(f"OCR dual-pass completado. Texto final: {len(resultado_ocr['texto_completo'])} caracteres")
            return resultado_ocr
            
        except Exception as e:
            logger.error(f"Error en OCR: {str(e)}")
            return {'error': str(e)}
    
    def _analizar_estadisticas_ocr(self, ocr_data):
        """Analiza estadísticas detalladas de los resultados de OCR"""
        total_words = len(ocr_data['text'])
        valid_words = [i for i, text in enumerate(ocr_data['text']) if text.strip()]
        
        confidences = [ocr_data['conf'][i] for i in valid_words if ocr_data['conf'][i] != -1]
        
        if not confidences:
            return {
                'total_palabras': 0,
                'palabras_validas': 0,
                'confianza_promedio': 0,
                'confianza_minima': 0,
                'confianza_maxima': 0,
                'palabras_alta_confianza': 0
            }
        
        return {
            'total_palabras': total_words,
            'palabras_validas': len(valid_words),
            'confianza_promedio': round(np.mean(confidences), 2),
            'confianza_minima': min(confidences),
            'confianza_maxima': max(confidences),
            'palabras_alta_confianza': len([c for c in confidences if c > self.quality_thresholds['good_confidence']]),
            'palabras_baja_confianza': len([c for c in confidences if c < self.quality_thresholds['min_confidence']]),
            'distribucion_confianza': self._calcular_distribucion_confianza(confidences)
        }
    
    def _extraer_palabras_con_confianza(self, ocr_data):
        """Extrae palabras individuales con sus niveles de confianza"""
        palabras = []
        
        for i, text in enumerate(ocr_data['text']):
            if text.strip() and ocr_data['conf'][i] != -1:
                palabra_info = {
                    'texto': text.strip(),
                    'confianza': ocr_data['conf'][i],
                    'posicion': {
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    },
                    'categoria_confianza': self._categorizar_confianza(ocr_data['conf'][i])
                }
                palabras.append(palabra_info)
        
        # Ordenar por confianza descendente
        palabras.sort(key=lambda x: x['confianza'], reverse=True)
        
        return palabras[:50]  # Limitar a 50 palabras principales
    
    def _calcular_confianza_promedio(self, ocr_data):
        """Calcula la confianza promedio ponderada"""
        confidences = [conf for conf in ocr_data['conf'] if conf != -1]
        
        if not confidences:
            return 0
        
        # Confianza promedio simple
        avg_confidence = np.mean(confidences)
        
        # Confianza ponderada por longitud de texto
        weighted_sum = 0
        total_chars = 0
        
        for i, text in enumerate(ocr_data['text']):
            if text.strip() and ocr_data['conf'][i] != -1:
                char_count = len(text.strip())
                weighted_sum += ocr_data['conf'][i] * char_count
                total_chars += char_count
        
        weighted_confidence = weighted_sum / total_chars if total_chars > 0 else 0
        
        return {
            'simple': round(avg_confidence, 2),
            'ponderada': round(weighted_confidence, 2),
            'palabras_evaluadas': len(confidences)
        }
    
    def _evaluar_calidad_extraccion(self, ocr_data, texto_completo):
        """Evalúa la calidad general de la extracción"""
        # Calcular métricas de calidad
        total_chars = len(texto_completo.replace(' ', '').replace('\n', ''))
        total_words = len(texto_completo.split())
        
        # Detectar posibles errores comunes
        errores_comunes = self._detectar_errores_ocr(texto_completo)
        
        # Evaluar densidad de información
        densidad_info = total_chars / len(texto_completo) if len(texto_completo) > 0 else 0
        
        # Calcular puntuación de calidad
        confidences = [conf for conf in ocr_data['conf'] if conf != -1]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        calidad_score = self._calcular_score_calidad(avg_confidence, total_words, errores_comunes)
        
        return {
            'caracteres_totales': total_chars,
            'palabras_totales': total_words,
            'densidad_informacion': round(densidad_info, 3),
            'errores_detectados': errores_comunes,
            'puntuacion_calidad': calidad_score,
            'categoria': self._categorizar_calidad(calidad_score),
            'recomendaciones': self._generar_recomendaciones_calidad(calidad_score, errores_comunes)
        }
    
    def _extraer_datos_financieros(self, texto):
        """Extrae datos financieros específicos del texto"""
        datos_financieros = {}
        
        for pattern_name, pattern in self.financial_patterns.items():
            matches = re.findall(pattern, texto, re.IGNORECASE)
            if matches:
                datos_financieros[pattern_name] = [
                    {
                        'valor': match if isinstance(match, str) else match[0] if match else '',
                        'posicion_texto': texto.lower().find(match.lower() if isinstance(match, str) else match[0].lower())
                    }
                    for match in matches[:5]  # Limitar a 5 coincidencias por tipo
                ]
        
        # Análisis específico para documentos bancarios
        datos_financieros['analisis_documento'] = self._analizar_tipo_documento(texto)
        
        # Extraer información clave estructurada
        datos_financieros['resumen_extraido'] = self._generar_resumen_financiero(datos_financieros)
        
        return datos_financieros
    
    def _analizar_tipo_documento(self, texto):
        """Analiza el tipo de documento financiero"""
        texto_lower = texto.lower()
        
        tipos_documento = {
            'factura': ['factura', 'invoice', 'fact.', 'fac.'],
            'recibo_pago': ['recibo', 'comprobante', 'voucher', 'receipt'],
            'transferencia': ['transferencia', 'transfer', 'envío', 'envio'],
            'estado_cuenta': ['estado', 'balance', 'saldo', 'cuenta'],
            'nota_credito': ['nota de crédito', 'nota credito', 'credit note'],
            'nota_debito': ['nota de débito', 'nota debito', 'debit note']
        }
        
        tipo_detectado = 'desconocido'
        confianza_tipo = 0
        
        for tipo, keywords in tipos_documento.items():
            matches = sum(1 for keyword in keywords if keyword in texto_lower)
            if matches > 0:
                confianza_actual = matches / len(keywords)
                if confianza_actual > confianza_tipo:
                    tipo_detectado = tipo
                    confianza_tipo = confianza_actual
        
        return {
            'tipo': tipo_detectado,
            'confianza': round(confianza_tipo * 100, 1),
            'keywords_encontradas': [kw for kw in tipos_documento.get(tipo_detectado, []) if kw in texto_lower]
        }
    
    def _generar_resumen_financiero(self, datos_financieros):
        """Genera un resumen de los datos financieros extraídos"""
        resumen = {
            'montos_encontrados': len(datos_financieros.get('amount', [])),
            'fechas_encontradas': len(datos_financieros.get('date', [])),
            'referencias_encontradas': len(datos_financieros.get('reference', [])),
            'cuentas_encontradas': len(datos_financieros.get('account', [])),
            'telefonos_encontrados': len(datos_financieros.get('phone', [])),
            'total_elementos': 0
        }
        
        # Calcular total de elementos encontrados
        for key in ['amount', 'date', 'reference', 'account', 'phone', 'rif', 'cedula']:
            resumen['total_elementos'] += len(datos_financieros.get(key, []))
        
        # Determinar completitud del documento
        elementos_criticos = ['amount', 'date']
        completitud = sum(1 for elem in elementos_criticos if datos_financieros.get(elem))
        resumen['completitud_porcentaje'] = int((completitud / len(elementos_criticos)) * 100)
        
        return resumen
    
    def _detectar_errores_ocr(self, texto):
        """Detecta errores comunes de OCR"""
        errores = []
        
        # Detectar caracteres extraños o mal reconocidos
        caracteres_sospechosos = re.findall(r'[|@#$%^&*+=<>{}[\]\\]', texto)
        if caracteres_sospechosos:
            errores.append(f"Caracteres sospechosos: {len(set(caracteres_sospechosos))}")
        
        # Detectar números mal formateados
        numeros_mal_formados = re.findall(r'\d[a-zA-Z]\d|\d\s[a-zA-Z]\s\d', texto)
        if numeros_mal_formados:
            errores.append(f"Números mal formateados: {len(numeros_mal_formados)}")
        
        # Detectar palabras muy cortas (posibles errores)
        palabras = texto.split()
        palabras_cortas = [p for p in palabras if len(p) == 1 and p.isalpha()]
        if len(palabras_cortas) > len(palabras) * 0.2:  # Más del 20% son palabras de 1 letra
            errores.append(f"Exceso de palabras de 1 letra: {len(palabras_cortas)}")
        
        # Detectar espaciado inconsistente
        espacios_multiples = len(re.findall(r'\s{3,}', texto))
        if espacios_multiples > 5:
            errores.append(f"Espaciado inconsistente: {espacios_multiples} casos")
        
        return errores
    
    def _calcular_distribucion_confianza(self, confidences):
        """Calcula la distribución de confianza en rangos"""
        ranges = {
            'excelente (90-100)': 0,
            'buena (70-89)': 0,
            'regular (50-69)': 0,
            'baja (30-49)': 0,
            'muy_baja (0-29)': 0
        }
        
        for conf in confidences:
            if conf >= 90:
                ranges['excelente (90-100)'] += 1
            elif conf >= 70:
                ranges['buena (70-89)'] += 1
            elif conf >= 50:
                ranges['regular (50-69)'] += 1
            elif conf >= 30:
                ranges['baja (30-49)'] += 1
            else:
                ranges['muy_baja (0-29)'] += 1
        
        return ranges
    
    def _categorizar_confianza(self, confidence):
        """Categoriza el nivel de confianza"""
        if confidence >= self.quality_thresholds['excellent_confidence']:
            return 'excelente'
        elif confidence >= self.quality_thresholds['good_confidence']:
            return 'buena'
        elif confidence >= self.quality_thresholds['min_confidence']:
            return 'aceptable'
        else:
            return 'baja'
    
    def _calcular_score_calidad(self, avg_confidence, total_words, errores):
        """Calcula un score de calidad general"""
        score = avg_confidence  # Base: confianza promedio
        
        # Penalizar por errores
        score -= len(errores) * 10
        
        # Bonificar por cantidad de palabras (hasta un límite)
        word_bonus = min(total_words * 2, 20)
        score += word_bonus
        
        # Normalizar entre 0-100
        return max(0, min(100, score))
    
    def _categorizar_calidad(self, score):
        """Categoriza la calidad basada en el score"""
        if score >= 80:
            return 'Excelente'
        elif score >= 60:
            return 'Buena'
        elif score >= 40:
            return 'Regular'
        else:
            return 'Deficiente'
    
    def _generar_recomendaciones_calidad(self, score, errores):
        """Genera recomendaciones para mejorar la calidad"""
        recomendaciones = []
        
        if score < 50:
            recomendaciones.append("Considere mejorar la calidad de la imagen de entrada")
            recomendaciones.append("Verifique la iluminación y el contraste")
        
        if 'Caracteres sospechosos' in str(errores):
            recomendaciones.append("Revisar manualmente caracteres especiales detectados")
        
        if 'Números mal formateados' in str(errores):
            recomendaciones.append("Verificar números importantes manualmente")
        
        if len(errores) > 3:
            recomendaciones.append("Usar perfil de procesamiento 'Normal' para mejor calidad")
        
        if not recomendaciones:
            recomendaciones.append("Calidad de extracción satisfactoria")
        
        return recomendaciones

    def _detectar_zonas_grises(self, image):
        """
        FIX: Detecta zonas grises en la imagen final para procesamiento dual-pass
        REASON: Usuario requiere detección específica de zonas grises para segundo pase de OCR
        IMPACT: Permite procesamiento especializado de áreas con fondo gris que pueden contener texto adicional
        """
        try:
            # Convertir a escala de grises si no lo está
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # FIX: Detección mejorada de zonas grises con múltiples rangos
            # REASON: La zona gris principal "104,54 Bs" requiere un rango más amplio de detección
            # IMPACT: Captura correcta de todas las zonas grises, incluyendo la zona principal
            
            # Detectar zonas grises con rango ampliado (80-200) para capturar más variaciones
            gray_mask_primary = np.zeros_like(gray)
            gray_mask_primary[(gray >= 80) & (gray <= 200)] = 255
            
            # Detectar zonas grises específicas (rango medio 120-170 para zonas típicas)
            gray_mask_secondary = np.zeros_like(gray)
            gray_mask_secondary[(gray >= 120) & (gray <= 170)] = 255
            
            # Combinar ambas máscaras para detección completa
            gray_mask = cv2.bitwise_or(gray_mask_primary, gray_mask_secondary)
            
            # Aplicar operaciones morfológicas más agresivas para capturar zonas completas
            kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            
            # Cerrar huecos en las zonas grises
            gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_CLOSE, kernel_large)
            # Limpiar ruido pequeño
            gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_OPEN, kernel_small)
            # Dilatar para capturar bordes completos
            gray_mask = cv2.dilate(gray_mask, kernel_small, iterations=2)
            
            # Encontrar contornos de las zonas grises
            contours, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # FIX: Área mínima reducida para capturar zonas más pequeñas pero importantes
            # REASON: La zona principal puede ser más pequeña de lo esperado
            # IMPACT: Captura zonas grises importantes que antes se perdían
            min_area = 500  # Reducido de 1000 a 500 píxeles cuadrados
            gray_regions = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    # Agregar padding para capturar texto completo
                    padding = 10
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(image.shape[1] - x, w + 2*padding)
                    h = min(image.shape[0] - y, h + 2*padding)
                    
                    gray_regions.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'region_image': image[y:y+h, x:x+w]
                    })
            
            logger.info(f"Detectadas {len(gray_regions)} zonas grises para procesamiento secundario")
            return gray_regions
            
        except Exception as e:
            logger.error(f"Error detectando zonas grises: {e}")
            return []
    
    def _detectar_logos_figuras(self, image):
        """
        FIX: Detecta y separa logos/figuras del texto para preservar caracteres
        REASON: Usuario requiere separación de elementos gráficos vs texto
        IMPACT: Mejora precisión OCR al evitar interferencia de elementos no textuales
        """
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Detectar bordes para identificar figuras/logos
            edges = cv2.Canny(gray, 50, 150)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Clasificar contornos como texto vs figuras/logos
            text_regions = []
            figure_regions = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Heurísticas para clasificar:
                # - Texto: relación de aspecto moderada, área pequeña-mediana
                # - Figuras/logos: área grande o relación de aspecto extrema
                if area < 5000 and 0.1 < aspect_ratio < 10:
                    # Probablemente texto
                    text_regions.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'type': 'text'
                    })
                else:
                    # Probablemente figura/logo
                    figure_regions.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'type': 'figure'
                    })
            
            logger.info(f"Detectadas {len(text_regions)} regiones de texto y {len(figure_regions)} figuras/logos")
            
            return {
                'text_regions': text_regions,
                'figure_regions': figure_regions
            }
            
        except Exception as e:
            logger.error(f"Error detectando logos/figuras: {e}")
            return {'text_regions': [], 'figure_regions': []}
    
    def _procesar_dual_pass(self, image_path, language, config_mode, tesseract_config):
        """
        FIX: Implementa procesamiento dual-pass OCR (imagen completa + zonas grises)
        REASON: Usuario requiere procesamiento especializado de zonas grises adicionales
        IMPACT: Maximiza extracción de texto al procesar tanto la imagen completa como zonas específicas
        """
        try:
            # Cargar imagen
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"No se puede cargar imagen para dual-pass: {image_path}")
            
            # PRIMER PASS: OCR completo de toda la imagen
            logger.info("Ejecutando PRIMER PASS: OCR completo de imagen")
            
            # Usar método original para OCR completo
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # OCR con datos detallados para primer pass
            ocr_data_full = pytesseract.image_to_data(
                pil_image, 
                lang=language, 
                config=tesseract_config, 
                output_type=pytesseract.Output.DICT
            )
            
            # Texto completo del primer pass
            texto_primer_pass = pytesseract.image_to_string(
                pil_image, 
                lang=language, 
                config=tesseract_config
            ).strip()
            
            # DETECTAR ZONAS GRISES para segundo pass
            zonas_grises = self._detectar_zonas_grises(image)
            
            # DETECTAR LOGOS/FIGURAS para separación
            elementos_detectados = self._detectar_logos_figuras(image)
            
            resultado_dual = {
                'primer_pass': {
                    'texto': texto_primer_pass,
                    'caracteres': len(texto_primer_pass),
                    'ocr_data': ocr_data_full
                },
                'segundo_pass': {
                    'texto': '',
                    'zonas_procesadas': 0,
                    'caracteres_adicionales': 0
                },
                'texto_final_concatenado': texto_primer_pass,
                'elementos_detectados': elementos_detectados,
                'zonas_grises_detectadas': len(zonas_grises)
            }
            
            # SEGUNDO PASS: Solo si se detectaron zonas grises
            if zonas_grises:
                logger.info(f"Ejecutando SEGUNDO PASS: Procesando {len(zonas_grises)} zonas grises")
                
                textos_segundo_pass = []
                
                for i, zona in enumerate(zonas_grises):
                    try:
                        # Extraer imagen de la zona gris
                        zona_image = zona['region_image']
                        
                        # Convertir para PIL
                        zona_pil = Image.fromarray(cv2.cvtColor(zona_image, cv2.COLOR_BGR2RGB))
                        
                        # OCR específico de la zona gris
                        texto_zona = pytesseract.image_to_string(
                            zona_pil,
                            lang=language,
                            config=tesseract_config
                        ).strip()
                        
                        if texto_zona:  # Solo agregar si hay texto
                            textos_segundo_pass.append(texto_zona)
                            logger.info(f"Zona gris {i+1}: Extraídos {len(texto_zona)} caracteres")
                    
                    except Exception as e:
                        logger.warning(f"Error procesando zona gris {i+1}: {e}")
                        continue
                
                # FIX: Consolidar y limpiar texto del segundo pass con mejor espaciado
                # REASON: Usuario requiere elementos no textuales separados con espacios
                # IMPACT: Mejora legibilidad y preserva estructura del texto
                texto_segundo_pass_crudo = ' '.join(textos_segundo_pass)
                texto_segundo_pass = self._limpiar_y_espaciar_texto(texto_segundo_pass_crudo)
                
                # Actualizar resultado
                resultado_dual['segundo_pass'] = {
                    'texto': texto_segundo_pass,
                    'zonas_procesadas': len(textos_segundo_pass),
                    'caracteres_adicionales': len(texto_segundo_pass)
                }
                
                # CONCATENAR RESULTADOS: Primer pass + Segundo pass
                if texto_segundo_pass:
                    resultado_dual['texto_final_concatenado'] = f"{texto_primer_pass}\n\n--- TEXTO DE ZONAS GRISES ---\n{texto_segundo_pass}"
                
                logger.info(f"Dual-pass completado: {len(texto_primer_pass)} + {len(texto_segundo_pass)} = {len(resultado_dual['texto_final_concatenado'])} caracteres totales")
            
            else:
                logger.info("No se detectaron zonas grises, usando solo resultado del primer pass")
            
            return resultado_dual
            
        except Exception as e:
            logger.error(f"Error en procesamiento dual-pass: {e}")
            # Fallback: retornar solo texto básico
            return {
                'primer_pass': {'texto': '', 'caracteres': 0, 'ocr_data': {}},
                'segundo_pass': {'texto': '', 'zonas_procesadas': 0, 'caracteres_adicionales': 0},
                'texto_final_concatenado': '',
                'elementos_detectados': {'text_regions': [], 'figure_regions': []},
                'zonas_grises_detectadas': 0,
                'error': str(e)
            }
    
    def _limpiar_y_espaciar_texto(self, texto):
        """
        FIX: Limpia y mejora el espaciado del texto extraído
        REASON: Usuario requiere elementos no textuales separados con espacios apropiados
        IMPACT: Mejora legibilidad y preserva estructura del texto manteniendo símbolos
        """
        if not texto:
            return texto
            
        # FIX: Preservar símbolos pero mejorar espaciado
        # REASON: Usuario quiere conservar */.- pero con mejor separación
        # IMPACT: Texto más legible sin perder información
        
        # Separar elementos pegados con espacios
        import re
        
        # Agregar espacio antes y después de números largos
        texto = re.sub(r'(\d{4,})', r' \1 ', texto)
        
        # Separar fechas pegadas
        texto = re.sub(r'(\d{1,2}/\d{1,2}/\d{4})', r' \1 ', texto)
        
        # Separar códigos de operación
        texto = re.sub(r'(\d{11,})', r' \1 ', texto)
        
        # Agregar espacio después de símbolos importantes
        texto = re.sub(r'([*/.:-])([A-Za-z])', r'\1 \2', texto)
        
        # Agregar espacio antes de símbolos si están pegados a letras
        texto = re.sub(r'([A-Za-z])([*/.:-])', r'\1 \2', texto)
        
        # Limpiar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto)
        
        # Limpiar espacios al inicio y final
        texto = texto.strip()
        
        return texto

def main():
    """Función principal para uso por línea de comandos"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python aplicador_ocr.py <ruta_imagen> [idioma] [modo_config]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'spa'
    config_mode = sys.argv[3] if len(sys.argv) > 3 else 'default'
    
    aplicador = AplicadorOCR()
    resultado = aplicador.extraer_texto(image_path, language, config_mode, True)
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
