"""
Orquestador principal del sistema OCR
Coordina todos los módulos y gestiona el flujo completo de procesamiento
"""

import os
import json
import shutil
import logging
import tempfile
import argparse
from pathlib import Path
from datetime import datetime
import uuid

# Importar módulos del sistema
import config
from validador_ocr import ValidadorOCR
from mejora_ocr import MejoradorOCR
from aplicador_ocr import AplicadorOCR

# Configurar logging
logging.basicConfig(**config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class OrquestadorOCR:
    """Clase principal que orquesta todo el proceso de OCR"""
    
    def __init__(self):
        self.validador = ValidadorOCR()
        self.mejorador = MejoradorOCR()
        self.aplicador = AplicadorOCR()
        
    def procesar_imagen_completo(self, image_path, language='spa', profile='rapido', 
                                save_intermediate=False, output_dir=None):
        """
        Ejecuta el proceso completo de OCR con todos los módulos
        
        Args:
            image_path: Ruta a la imagen de entrada
            language: Idioma para OCR
            profile: Perfil de rendimiento a usar
            save_intermediate: Si guardar archivos intermedios
            output_dir: Directorio de salida (si None, usa temporal)
            
        Returns:
            dict: Resultado completo con todos los datos del proceso
        """
        # Generar ID único para esta ejecución
        execution_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear directorio temporal único
        if output_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix=f"ocr_{execution_id}_"))
        else:
            temp_dir = Path(output_dir) / f"ocr_{execution_id}_{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Iniciando procesamiento OCR completo. ID: {execution_id}")
        logger.info(f"Directorio temporal: {temp_dir}")
        
        try:
            # Resultado consolidado
            resultado_completo = {
                'execution_id': execution_id,
                'timestamp': timestamp,
                'input_image': str(image_path),
                'temp_directory': str(temp_dir),
                'parametros': {
                    'language': language,
                    'profile': profile,
                    'save_intermediate': save_intermediate
                },
                'etapas': {},
                'archivos_generados': [],
                'resumen_final': {},
                'tiempo_total': 0
            }
            
            import time
            start_time = time.time()
            
            # ETAPA 1: Validación y diagnóstico
            logger.info("ETAPA 1: Validación y diagnóstico de imagen")
            resultado_completo['etapas']['1_validacion'] = self._ejecutar_validacion(
                image_path, temp_dir, save_intermediate
            )
            
            if 'error' in resultado_completo['etapas']['1_validacion']:
                raise Exception(f"Error en validación: {resultado_completo['etapas']['1_validacion']['error']}")
            
            # ETAPA 2: Mejora y preprocesamiento
            logger.info("ETAPA 2: Mejora y preprocesamiento adaptativo")
            resultado_completo['etapas']['2_mejora'] = self._ejecutar_mejora(
                image_path, resultado_completo['etapas']['1_validacion']['diagnostico'],
                profile, temp_dir, save_intermediate
            )
            
            if 'error' in resultado_completo['etapas']['2_mejora']:
                raise Exception(f"Error en mejora: {resultado_completo['etapas']['2_mejora']['error']}")
            
            # ETAPA 3: Aplicación de OCR
            logger.info("ETAPA 3: Aplicación de OCR y extracción de datos")
            imagen_mejorada = resultado_completo['etapas']['2_mejora']['imagen_mejorada']
            resultado_completo['etapas']['3_ocr'] = self._ejecutar_ocr(
                imagen_mejorada, language, temp_dir, save_intermediate
            )
            
            if 'error' in resultado_completo['etapas']['3_ocr']:
                raise Exception(f"Error en OCR: {resultado_completo['etapas']['3_ocr']['error']}")
            
            # ETAPA 4: Consolidación y análisis final
            logger.info("ETAPA 4: Consolidación de resultados")
            resultado_completo['resumen_final'] = self._generar_resumen_final(resultado_completo)
            
            # Calcular tiempo total
            resultado_completo['tiempo_total'] = round(time.time() - start_time, 3)
            
            # Guardar resultado consolidado
            resultado_json_path = temp_dir / "resultado_completo.json"
            with open(resultado_json_path, 'w', encoding='utf-8') as f:
                json.dump(resultado_completo, f, indent=2, ensure_ascii=False)
            
            resultado_completo['archivos_generados'].append(str(resultado_json_path))
            
            # Generar reporte HTML si se solicita
            if save_intermediate:
                reporte_html = self._generar_reporte_html(resultado_completo, temp_dir)
                resultado_completo['archivos_generados'].append(reporte_html)
            
            logger.info(f"Procesamiento completado exitosamente en {resultado_completo['tiempo_total']}s")
            
            # Limpiar archivos temporales si no se solicita guardarlos
            if not save_intermediate and output_dir is None:
                self._limpiar_archivos_temporales(temp_dir, resultado_completo)
            
            return resultado_completo
            
        except Exception as e:
            logger.error(f"Error en procesamiento OCR: {str(e)}")
            resultado_completo['error'] = str(e)
            resultado_completo['tiempo_total'] = round(time.time() - start_time, 3)
            return resultado_completo
        
    def _ejecutar_validacion(self, image_path, temp_dir, save_intermediate):
        """Ejecuta la etapa de validación"""
        try:
            # Copiar imagen original al directorio temporal
            imagen_original = temp_dir / "00_imagen_original.png"
            shutil.copy2(image_path, imagen_original)
            
            # Ejecutar validación
            import time
            start_time = time.time()
            
            diagnostico = self.validador.analizar_imagen(image_path)
            
            tiempo_validacion = round(time.time() - start_time, 3)
            
            # Guardar diagnóstico
            if save_intermediate:
                diagnostico_path = temp_dir / "diagnostico.json"
                with open(diagnostico_path, 'w', encoding='utf-8') as f:
                    json.dump(diagnostico, f, indent=2, ensure_ascii=False)
            
            return {
                'tiempo': tiempo_validacion,
                'diagnostico': diagnostico,
                'imagen_original': str(imagen_original),
                'archivo_diagnostico': str(temp_dir / "diagnostico.json") if save_intermediate else None
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ejecutar_mejora(self, image_path, diagnostico, profile, temp_dir, save_intermediate):
        """Ejecuta la etapa de mejora"""
        try:
            import time
            start_time = time.time()
            
            resultado_mejora = self.mejorador.procesar_imagen(
                image_path, diagnostico, profile, save_intermediate, temp_dir
            )
            
            tiempo_mejora = round(time.time() - start_time, 3)
            resultado_mejora['tiempo'] = tiempo_mejora
            
            # Guardar resultado de mejora
            if save_intermediate:
                mejora_path = temp_dir / "resultado_mejora.json"
                with open(mejora_path, 'w', encoding='utf-8') as f:
                    json.dump(resultado_mejora, f, indent=2, ensure_ascii=False)
                resultado_mejora['archivo_resultado'] = str(mejora_path)
            
            return resultado_mejora
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ejecutar_ocr(self, imagen_mejorada, language, temp_dir, save_intermediate):
        """Ejecuta la etapa de OCR"""
        try:
            import time
            start_time = time.time()
            
            resultado_ocr = self.aplicador.extraer_texto(
                imagen_mejorada, language, 'default', True
            )
            
            tiempo_ocr = round(time.time() - start_time, 3)
            resultado_ocr['tiempo'] = tiempo_ocr
            
            # Guardar resultado de OCR
            if save_intermediate:
                ocr_path = temp_dir / "resultado_ocr.json"
                with open(ocr_path, 'w', encoding='utf-8') as f:
                    json.dump(resultado_ocr, f, indent=2, ensure_ascii=False)
                resultado_ocr['archivo_resultado'] = str(ocr_path)
                
                # Guardar texto extraído
                texto_path = temp_dir / "texto_extraido.txt"
                with open(texto_path, 'w', encoding='utf-8') as f:
                    f.write(resultado_ocr.get('texto_completo', ''))
                resultado_ocr['archivo_texto'] = str(texto_path)
            
            return resultado_ocr
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generar_resumen_final(self, resultado_completo):
        """Genera un resumen final del procesamiento"""
        try:
            # Extraer métricas clave
            etapas = resultado_completo['etapas']
            
            # Información de la imagen original
            info_original = etapas.get('1_validacion', {}).get('diagnostico', {}).get('imagen_info', {})
            
            # Métricas de calidad
            calidad_original = etapas.get('1_validacion', {}).get('diagnostico', {}).get('puntuacion_general', {})
            
            # Información de mejoras aplicadas
            mejoras = etapas.get('2_mejora', {})
            pasos_aplicados = mejoras.get('pasos_aplicados', [])
            
            # Resultados de OCR
            ocr_resultado = etapas.get('3_ocr', {})
            confianza_ocr = ocr_resultado.get('confianza_promedio', {})
            
            # Datos financieros extraídos
            datos_financieros = ocr_resultado.get('datos_financieros', {})
            resumen_financiero = datos_financieros.get('resumen_extraido', {})
            
            resumen = {
                'imagen_original': {
                    'dimensiones': f"{info_original.get('ancho', 0)}x{info_original.get('alto', 0)}",
                    'calidad_inicial': calidad_original.get('categoria', 'Desconocida'),
                    'puntuacion_calidad': calidad_original.get('total', 0)
                },
                'procesamiento_aplicado': {
                    'perfil_usado': mejoras.get('perfil_usado', 'desconocido'),
                    'pasos_ejecutados': len(pasos_aplicados),
                    'lista_pasos': pasos_aplicados,
                    'tiempo_procesamiento': mejoras.get('tiempo_procesamiento', 0)
                },
                'resultados_ocr': {
                    'caracteres_extraidos': len(ocr_resultado.get('texto_completo', '')),
                    'palabras_detectadas': len(ocr_resultado.get('palabras_detectadas', [])),
                    'confianza_promedio': confianza_ocr.get('simple', 0),
                    'confianza_ponderada': confianza_ocr.get('ponderada', 0),
                    'calidad_extraccion': ocr_resultado.get('calidad_extraccion', {}).get('categoria', 'Desconocida')
                },
                'datos_financieros': {
                    'tipo_documento': datos_financieros.get('analisis_documento', {}).get('tipo', 'desconocido'),
                    'elementos_encontrados': resumen_financiero.get('total_elementos', 0),
                    'completitud': resumen_financiero.get('completitud_porcentaje', 0),
                    'montos_encontrados': resumen_financiero.get('montos_encontrados', 0),
                    'fechas_encontradas': resumen_financiero.get('fechas_encontradas', 0)
                },
                'rendimiento': {
                    'tiempo_total': resultado_completo['tiempo_total'],
                    'tiempo_validacion': etapas.get('1_validacion', {}).get('tiempo', 0),
                    'tiempo_mejora': etapas.get('2_mejora', {}).get('tiempo', 0),
                    'tiempo_ocr': etapas.get('3_ocr', {}).get('tiempo', 0)
                },
                'calificacion_final': self._calcular_calificacion_final(etapas),
                'recomendaciones': self._generar_recomendaciones_finales(etapas)
            }
            
            return resumen
            
        except Exception as e:
            logger.error(f"Error generando resumen final: {str(e)}")
            return {'error': str(e)}
    
    def _calcular_calificacion_final(self, etapas):
        """Calcula una calificación final del proceso"""
        try:
            # Obtener métricas clave
            calidad_imagen = etapas.get('1_validacion', {}).get('diagnostico', {}).get('puntuacion_general', {}).get('total', 0)
            confianza_ocr = etapas.get('3_ocr', {}).get('confianza_promedio', {}).get('simple', 0)
            completitud = etapas.get('3_ocr', {}).get('datos_financieros', {}).get('resumen_extraido', {}).get('completitud_porcentaje', 0)
            
            # Calcular calificación ponderada
            calificacion = (calidad_imagen * 0.3 + confianza_ocr * 0.4 + completitud * 0.3)
            
            if calificacion >= 80:
                categoria = 'Excelente'
            elif calificacion >= 65:
                categoria = 'Buena'
            elif calificacion >= 50:
                categoria = 'Regular'
            else:
                categoria = 'Deficiente'
            
            return {
                'puntuacion': round(calificacion, 1),
                'categoria': categoria,
                'componentes': {
                    'calidad_imagen': round(calidad_imagen, 1),
                    'confianza_ocr': round(confianza_ocr, 1),
                    'completitud_datos': round(completitud, 1)
                }
            }
            
        except Exception:
            return {'puntuacion': 0, 'categoria': 'Error', 'componentes': {}}
    
    def _generar_recomendaciones_finales(self, etapas):
        """Genera recomendaciones finales basadas en todo el proceso"""
        recomendaciones = []
        
        try:
            # Analizar calidad de imagen original
            calidad_original = etapas.get('1_validacion', {}).get('diagnostico', {}).get('puntuacion_general', {}).get('total', 0)
            if calidad_original < 50:
                recomendaciones.append("Mejorar calidad de imagen de entrada (iluminación, enfoque)")
            
            # Analizar confianza de OCR
            confianza_ocr = etapas.get('3_ocr', {}).get('confianza_promedio', {}).get('simple', 0)
            if confianza_ocr < 70:
                recomendaciones.append("Considerar usar perfil 'Normal' para mejor precisión")
            
            # Analizar completitud de datos
            completitud = etapas.get('3_ocr', {}).get('datos_financieros', {}).get('resumen_extraido', {}).get('completitud_porcentaje', 0)
            if completitud < 80:
                recomendaciones.append("Revisar manualmente los datos críticos extraídos")
            
            # Analizar errores de OCR
            errores_ocr = etapas.get('3_ocr', {}).get('calidad_extraccion', {}).get('errores_detectados', [])
            if len(errores_ocr) > 2:
                recomendaciones.append("Verificar texto extraído por posibles errores de reconocimiento")
            
            if not recomendaciones:
                recomendaciones.append("Procesamiento exitoso, resultados confiables")
            
        except Exception:
            recomendaciones.append("Error generando recomendaciones")
        
        return recomendaciones
    
    def _generar_reporte_html(self, resultado_completo, temp_dir):
        """Genera un reporte HTML con los resultados"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reporte OCR - {resultado_completo['execution_id']}</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background: #2c3e50; color: white; padding: 20px; }}
                    .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                    .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; }}
                    .success {{ color: green; }}
                    .warning {{ color: orange; }}
                    .error {{ color: red; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Reporte de Procesamiento OCR</h1>
                    <p>ID: {resultado_completo['execution_id']} | Fecha: {resultado_completo['timestamp']}</p>
                </div>
                
                <div class="section">
                    <h2>Resumen Ejecutivo</h2>
                    <div class="metric">
                        <strong>Calificación Final:</strong> 
                        {resultado_completo['resumen_final']['calificacion_final']['puntuacion']} 
                        ({resultado_completo['resumen_final']['calificacion_final']['categoria']})
                    </div>
                    <div class="metric">
                        <strong>Tiempo Total:</strong> {resultado_completo['tiempo_total']}s
                    </div>
                    <div class="metric">
                        <strong>Caracteres Extraídos:</strong> 
                        {resultado_completo['resumen_final']['resultados_ocr']['caracteres_extraidos']}
                    </div>
                </div>
                
                <div class="section">
                    <h2>Texto Extraído</h2>
                    <pre style="background: #f8f9fa; padding: 15px; white-space: pre-wrap;">
{resultado_completo['etapas']['3_ocr'].get('texto_completo', 'No disponible')[:1000]}
                    </pre>
                </div>
            </body>
            </html>
            """
            
            reporte_path = temp_dir / "reporte.html"
            with open(reporte_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(reporte_path)
            
        except Exception as e:
            logger.error(f"Error generando reporte HTML: {str(e)}")
            return None
    
    def _limpiar_archivos_temporales(self, temp_dir, resultado_completo):
        """Limpia archivos temporales innecesarios"""
        try:
            # Mantener solo archivos críticos
            archivos_mantener = [
                'resultado_completo.json',
                'imagen_mejorada.png',
                'texto_extraido.txt'
            ]
            
            for archivo in temp_dir.iterdir():
                if archivo.name not in archivos_mantener:
                    if archivo.is_file():
                        archivo.unlink()
            
            logger.info(f"Archivos temporales limpiados: {temp_dir}")
            
        except Exception as e:
            logger.warning(f"Error limpiando archivos temporales: {str(e)}")

def main():
    """Función principal para uso por línea de comandos"""
    parser = argparse.ArgumentParser(description='Sistema OCR de Bajos Recursos')
    parser.add_argument('image_path', help='Ruta a la imagen de entrada')
    parser.add_argument('--language', '-l', default='spa', help='Idioma para OCR (default: spa)')
    parser.add_argument('--profile', '-p', default='rapido', 
                       choices=['ultra_rapido', 'rapido', 'normal'],
                       help='Perfil de rendimiento (default: rapido)')
    parser.add_argument('--save-intermediate', '-s', action='store_true',
                       help='Guardar archivos intermedios')
    parser.add_argument('--output-dir', '-o', help='Directorio de salida')
    parser.add_argument('--json-only', '-j', action='store_true',
                       help='Solo mostrar resultado JSON')
    
    args = parser.parse_args()
    
    # Validar archivo de entrada
    if not os.path.exists(args.image_path):
        print(f"Error: Archivo no encontrado: {args.image_path}")
        return 1
    
    # Crear orquestador y procesar
    orquestador = OrquestadorOCR()
    
    resultado = orquestador.procesar_imagen_completo(
        args.image_path,
        args.language,
        args.profile,
        args.save_intermediate,
        args.output_dir
    )
    
    if args.json_only:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        # Mostrar resumen en consola
        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
            return 1
        
        resumen = resultado['resumen_final']
        print("\n" + "="*60)
        print(f"  📄 SISTEMA OCR - RESULTADO FINAL")
        print("="*60)
        print(f"🔍 ID Ejecución: {resultado['execution_id']}")
        print(f"⏱️  Tiempo Total: {resultado['tiempo_total']}s")
        print(f"📊 Calificación: {resumen['calificacion_final']['puntuacion']} ({resumen['calificacion_final']['categoria']})")
        print(f"📝 Caracteres: {resumen['resultados_ocr']['caracteres_extraidos']}")
        print(f"🎯 Confianza OCR: {resumen['resultados_ocr']['confianza_promedio']:.1f}%")
        print(f"💰 Tipo Documento: {resumen['datos_financieros']['tipo_documento']}")
        print(f"✅ Elementos Financieros: {resumen['datos_financieros']['elementos_encontrados']}")
        
        if args.save_intermediate:
            print(f"📁 Archivos guardados en: {resultado['temp_directory']}")
        
        print("\n📋 Recomendaciones:")
        for rec in resumen['recomendaciones']:
            print(f"   • {rec}")
        
        print("\n" + "="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    exit(main())
