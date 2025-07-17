#!/usr/bin/env python3
"""
Validación rigurosa de optimizaciones de memoria - Fase 3
Pruebas de regresión de precisión, carga y estrés
"""

import os
import sys
import time
import json
import psutil
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import tracemalloc
from memory_profiler_advanced import advanced_profiler
from memory_optimizer import memory_optimizer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('temp/validation_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemoryOptimizationValidator:
    """Validador riguroso de optimizaciones de memoria"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.current_metrics = {}
        self.test_results = []
        self.validation_report = {}
        self.test_images_dir = Path("test_images_200")
        
    def measure_baseline_performance(self):
        """Mide el rendimiento base del sistema"""
        logger.info("📊 Midiendo rendimiento base del sistema...")
        
        # Iniciar perfilado
        advanced_profiler.start_profiling()
        tracemalloc.start()
        
        # Métricas iniciales
        process = psutil.Process()
        start_time = time.time()
        
        self.baseline_metrics = {
            'timestamp': datetime.now().isoformat(),
            'memory_rss_mb': process.memory_info().rss / 1024 / 1024,
            'memory_vms_mb': process.memory_info().vms / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'threads': process.num_threads(),
            'file_descriptors': process.num_fds(),
            'start_time': start_time
        }
        
        # Snapshot inicial
        snapshot = tracemalloc.take_snapshot()
        self.baseline_metrics['tracemalloc_snapshot'] = snapshot
        
        logger.info(f"✅ Métricas base: {self.baseline_metrics['memory_rss_mb']:.1f}MB RSS")
        
    def test_ocr_precision_regression(self):
        """Prueba regresión de precisión del OCR"""
        logger.info("🔍 Ejecutando pruebas de regresión de precisión...")
        
        try:
            # Procesar muestra de imágenes conocidas
            test_images = list(self.test_images_dir.glob("*.jpg"))[:5]
            
            precision_results = []
            
            for img_path in test_images:
                start_time = time.time()
                
                # Procesar con OCR
                from main_ocr_process import OrquestadorOCR
                orchestrator = OrquestadorOCR()
                
                result = orchestrator.procesar_imagen_completa(str(img_path))
                processing_time = time.time() - start_time
                
                # Métricas de precisión
                precision_data = {
                    'image': img_path.name,
                    'processing_time': processing_time,
                    'text_length': len(result.get('texto_completo', '')),
                    'word_count': len(result.get('coordenadas_palabras', [])),
                    'confidence_avg': self._calculate_avg_confidence(result),
                    'fields_extracted': len(result.get('campos_extraidos', {})),
                    'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024
                }
                
                precision_results.append(precision_data)
                logger.info(f"  ✓ {img_path.name}: {precision_data['confidence_avg']:.3f} confianza")
            
            # Validar precisión
            avg_confidence = sum(r['confidence_avg'] for r in precision_results) / len(precision_results)
            avg_processing_time = sum(r['processing_time'] for r in precision_results) / len(precision_results)
            
            self.test_results.append({
                'test_type': 'precision_regression',
                'status': 'PASSED' if avg_confidence > 0.85 else 'FAILED',
                'metrics': {
                    'avg_confidence': avg_confidence,
                    'avg_processing_time': avg_processing_time,
                    'images_tested': len(precision_results),
                    'results': precision_results
                }
            })
            
            logger.info(f"✅ Precisión promedio: {avg_confidence:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Error en prueba de precisión: {e}")
            self.test_results.append({
                'test_type': 'precision_regression',
                'status': 'ERROR',
                'error': str(e)
            })
    
    def test_memory_load_stress(self):
        """Prueba de carga y estrés de memoria"""
        logger.info("🔥 Ejecutando pruebas de carga y estrés...")
        
        try:
            # Monitorear memoria durante procesamiento intensivo
            memory_samples = []
            start_time = time.time()
            
            # Procesar múltiples imágenes en secuencia
            test_images = list(self.test_images_dir.glob("*.jpg"))[:10]
            
            for i, img_path in enumerate(test_images):
                # Tomar muestra de memoria
                process = psutil.Process()
                memory_sample = {
                    'iteration': i,
                    'timestamp': time.time() - start_time,
                    'rss_mb': process.memory_info().rss / 1024 / 1024,
                    'vms_mb': process.memory_info().vms / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'available_mb': psutil.virtual_memory().available / 1024 / 1024
                }
                memory_samples.append(memory_sample)
                
                # Procesar imagen
                from main_ocr_process import OrquestadorOCR
                orchestrator = OrquestadorOCR()
                orchestrator.procesar_imagen_completa(str(img_path))
                
                # Forzar garbage collection
                import gc
                gc.collect()
                
                logger.info(f"  🔄 Procesada {i+1}/{len(test_images)}: {memory_sample['rss_mb']:.1f}MB")
            
            # Analizar resultados
            max_memory = max(s['rss_mb'] for s in memory_samples)
            min_memory = min(s['rss_mb'] for s in memory_samples)
            avg_memory = sum(s['rss_mb'] for s in memory_samples) / len(memory_samples)
            
            # Verificar si hubo swap
            swap_used = psutil.swap_memory().used / 1024 / 1024
            
            self.test_results.append({
                'test_type': 'memory_load_stress',
                'status': 'PASSED' if max_memory < 500 and swap_used < 10 else 'WARNING',
                'metrics': {
                    'max_memory_mb': max_memory,
                    'min_memory_mb': min_memory,
                    'avg_memory_mb': avg_memory,
                    'memory_variation_mb': max_memory - min_memory,
                    'swap_used_mb': swap_used,
                    'images_processed': len(test_images),
                    'memory_samples': memory_samples
                }
            })
            
            logger.info(f"✅ Memoria máxima: {max_memory:.1f}MB, Variación: {max_memory - min_memory:.1f}MB")
            
        except Exception as e:
            logger.error(f"❌ Error en prueba de carga: {e}")
            self.test_results.append({
                'test_type': 'memory_load_stress',
                'status': 'ERROR',
                'error': str(e)
            })
    
    def test_system_stability(self):
        """Prueba estabilidad del sistema"""
        logger.info("🛡️ Ejecutando pruebas de estabilidad...")
        
        try:
            stability_metrics = []
            
            # Ejecutar múltiples ciclos de procesamiento
            for cycle in range(3):
                logger.info(f"  🔄 Ciclo de estabilidad {cycle + 1}/3")
                
                cycle_start = time.time()
                
                # Procesar lote de imágenes
                test_images = list(self.test_images_dir.glob("*.jpg"))[:5]
                
                for img_path in test_images:
                    from main_ocr_process import OrquestadorOCR
                    orchestrator = OrquestadorOCR()
                    orchestrator.procesar_imagen_completa(str(img_path))
                
                cycle_end = time.time()
                
                # Métricas del ciclo
                process = psutil.Process()
                cycle_metrics = {
                    'cycle': cycle,
                    'duration': cycle_end - cycle_start,
                    'memory_rss_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'threads': process.num_threads()
                }
                stability_metrics.append(cycle_metrics)
                
                # Pausa entre ciclos
                time.sleep(1)
            
            # Analizar estabilidad
            memory_consistency = all(
                abs(m['memory_rss_mb'] - stability_metrics[0]['memory_rss_mb']) < 50
                for m in stability_metrics
            )
            
            self.test_results.append({
                'test_type': 'system_stability',
                'status': 'PASSED' if memory_consistency else 'WARNING',
                'metrics': {
                    'cycles_completed': len(stability_metrics),
                    'memory_consistent': memory_consistency,
                    'cycle_metrics': stability_metrics
                }
            })
            
            logger.info(f"✅ Estabilidad: {'Consistente' if memory_consistency else 'Variable'}")
            
        except Exception as e:
            logger.error(f"❌ Error en prueba de estabilidad: {e}")
            self.test_results.append({
                'test_type': 'system_stability',
                'status': 'ERROR',
                'error': str(e)
            })
    
    def _calculate_avg_confidence(self, result):
        """Calcula confianza promedio de un resultado OCR"""
        coords = result.get('coordenadas_palabras', [])
        if not coords:
            return 0.0
        
        confidences = [w.get('confidence', 0) for w in coords if 'confidence' in w]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def generate_validation_report(self):
        """Genera reporte completo de validación"""
        logger.info("📋 Generando reporte de validación...")
        
        # Tomar snapshot final
        advanced_profiler.take_snapshot("validation_complete")
        final_report = advanced_profiler.generate_memory_report()
        
        # Métricas finales
        process = psutil.Process()
        final_metrics = {
            'timestamp': datetime.now().isoformat(),
            'memory_rss_mb': process.memory_info().rss / 1024 / 1024,
            'memory_vms_mb': process.memory_info().vms / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'threads': process.num_threads()
        }
        
        # Compilar reporte
        self.validation_report = {
            'validation_timestamp': datetime.now().isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'python_version': sys.version
            },
            'baseline_metrics': self.baseline_metrics,
            'final_metrics': final_metrics,
            'test_results': self.test_results,
            'memory_optimization_summary': {
                'initial_memory_mb': self.baseline_metrics.get('memory_rss_mb', 0),
                'final_memory_mb': final_metrics['memory_rss_mb'],
                'memory_reduction_mb': self.baseline_metrics.get('memory_rss_mb', 0) - final_metrics['memory_rss_mb'],
                'optimization_effective': final_metrics['memory_rss_mb'] < 450
            },
            'advanced_profiler_report': final_report
        }
        
        # Guardar reporte
        report_path = Path("temp/memory_optimization_validation_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Reporte guardado: {report_path}")
        return self.validation_report
    
    def run_full_validation(self):
        """Ejecuta validación completa"""
        logger.info("🚀 Iniciando validación completa de optimizaciones...")
        
        try:
            # Fase 1: Métricas base
            self.measure_baseline_performance()
            
            # Fase 2: Pruebas de precisión
            self.test_ocr_precision_regression()
            
            # Fase 3: Pruebas de carga
            self.test_memory_load_stress()
            
            # Fase 4: Pruebas de estabilidad
            self.test_system_stability()
            
            # Fase 5: Reporte final
            report = self.generate_validation_report()
            
            # Resumen de resultados
            passed_tests = sum(1 for t in self.test_results if t['status'] == 'PASSED')
            total_tests = len(self.test_results)
            
            logger.info(f"🎯 Validación completada: {passed_tests}/{total_tests} pruebas exitosas")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error en validación completa: {e}")
            raise

if __name__ == "__main__":
    validator = MemoryOptimizationValidator()
    report = validator.run_full_validation()
    
    print(f"\n🎉 REPORTE DE VALIDACIÓN COMPLETADO")
    print(f"Memoria inicial: {report['baseline_metrics']['memory_rss_mb']:.1f}MB")
    print(f"Memoria final: {report['final_metrics']['memory_rss_mb']:.1f}MB")
    print(f"Optimización efectiva: {report['memory_optimization_summary']['optimization_effective']}")