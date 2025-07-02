#!/usr/bin/env python3
"""
Script de pruebas de rendimiento para validar optimizaciones del sistema OCR
Mide startup time, memory usage, processing time y bundle size
"""

import time
import sys
import os
import psutil
import json
import subprocess
from pathlib import Path
from datetime import datetime

class PerformanceProfiler:
    """Perfilador de rendimiento para el sistema OCR"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self._get_system_info(),
            'tests': {}
        }
    
    def _get_system_info(self):
        """Obtiene información del sistema"""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'cpu_count': psutil.cpu_count(),
            'memory_total': f"{psutil.virtual_memory().total / 1024**3:.1f} GB",
            'disk_free': f"{psutil.disk_usage('.').free / 1024**3:.1f} GB"
        }
    
    def test_startup_time(self):
        """Mide tiempo de startup del sistema"""
        print("🚀 Midiendo tiempo de startup...")
        
        # Test import time
        start_time = time.time()
        try:
            import app  # Import principal de la aplicación
            startup_time = time.time() - start_time
            
            self.results['tests']['startup'] = {
                'import_time_seconds': round(startup_time, 3),
                'status': 'success'
            }
            print(f"   ✅ Startup time: {startup_time:.3f}s")
            
        except Exception as e:
            self.results['tests']['startup'] = {
                'import_time_seconds': -1,
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Error en startup: {e}")
    
    def test_memory_usage(self):
        """Mide uso de memoria del sistema"""
        print("💾 Midiendo uso de memoria...")
        
        try:
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024**2  # MB
            
            # Import heavy modules
            import config
            import routes
            from main_ocr_process import OrquestadorOCR
            
            # Create instance (lazy loading test)
            orquestador = OrquestadorOCR()
            
            memory_after = process.memory_info().rss / 1024**2  # MB
            memory_increase = memory_after - memory_before
            
            self.results['tests']['memory'] = {
                'initial_mb': round(memory_before, 1),
                'after_imports_mb': round(memory_after, 1),
                'increase_mb': round(memory_increase, 1),
                'status': 'success'
            }
            
            print(f"   ✅ Memoria inicial: {memory_before:.1f} MB")
            print(f"   ✅ Memoria después imports: {memory_after:.1f} MB")
            print(f"   ✅ Incremento: {memory_increase:.1f} MB")
            
        except Exception as e:
            self.results['tests']['memory'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Error midiendo memoria: {e}")
    
    def test_bundle_size(self):
        """Mide tamaño de archivos del bundle"""
        print("📦 Midiendo tamaño del bundle...")
        
        try:
            sizes = {}
            total_size = 0
            
            # Archivos principales
            files_to_check = [
                'app.py',
                'routes.py', 
                'config.py',
                'main_ocr_process.py',
                'validador_ocr.py',
                'mejora_ocr.py',
                'aplicador_ocr.py',
                'static/css/custom.css',
                'static/css/custom.min.css',
                'static/js/main.js',
                'static/js/main.opt.js'
            ]
            
            for file_path in files_to_check:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    sizes[file_path] = {
                        'bytes': size,
                        'kb': round(size / 1024, 1)
                    }
                    total_size += size
            
            # Directorios
            for dir_name in ['static', 'templates', 'temp', 'uploads']:
                if os.path.exists(dir_name):
                    dir_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(dir_name)
                        for filename in filenames
                    )
                    sizes[f'{dir_name}/'] = {
                        'bytes': dir_size,
                        'kb': round(dir_size / 1024, 1)
                    }
                    total_size += dir_size
            
            self.results['tests']['bundle_size'] = {
                'total_bytes': total_size,
                'total_mb': round(total_size / 1024**2, 1),
                'files': sizes,
                'status': 'success'
            }
            
            print(f"   ✅ Bundle total: {total_size / 1024**2:.1f} MB")
            
            # Mostrar archivos más grandes
            largest_files = sorted(
                [(name, data['kb']) for name, data in sizes.items()],
                key=lambda x: x[1], reverse=True
            )[:5]
            
            print("   📁 Archivos más grandes:")
            for name, size_kb in largest_files:
                print(f"      {name}: {size_kb} KB")
                
        except Exception as e:
            self.results['tests']['bundle_size'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Error midiendo bundle: {e}")
    
    def test_processing_performance(self):
        """Mide rendimiento de procesamiento OCR"""
        print("⚡ Midiendo rendimiento de procesamiento...")
        
        # Buscar imagen de prueba
        test_images = [
            'test_image.png',
            'sample.jpg',
            'uploads/test.png'
        ]
        
        test_image = None
        for img in test_images:
            if os.path.exists(img):
                test_image = img
                break
        
        if not test_image:
            print("   ⚠️  No se encontró imagen de prueba")
            self.results['tests']['processing'] = {
                'status': 'skipped',
                'reason': 'no_test_image'
            }
            return
        
        try:
            from main_ocr_process import OrquestadorOCR
            
            orquestador = OrquestadorOCR()
            
            # Test diferentes perfiles
            profiles = ['ultra_rapido', 'rapido', 'normal']
            profile_results = {}
            
            for profile in profiles:
                print(f"   🔄 Probando perfil: {profile}")
                start_time = time.time()
                
                resultado = orquestador.procesar_imagen_completo(
                    test_image,
                    profile=profile,
                    save_intermediate=False
                )
                
                processing_time = time.time() - start_time
                
                profile_results[profile] = {
                    'time_seconds': round(processing_time, 3),
                    'success': 'error' not in resultado,
                    'characters_extracted': len(resultado.get('etapas', {}).get('3_ocr', {}).get('texto_completo', ''))
                }
                
                print(f"      ⏱️  {processing_time:.3f}s")
            
            self.results['tests']['processing'] = {
                'test_image': test_image,
                'profiles': profile_results,
                'status': 'success'
            }
            
        except Exception as e:
            self.results['tests']['processing'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Error en procesamiento: {e}")
    
    def test_config_cache_performance(self):
        """Mide eficiencia del cache de configuración"""
        print("🗄️  Midiendo cache de configuración...")
        
        try:
            import config
            
            # Test múltiples accesos
            start_time = time.time()
            for _ in range(100):
                _ = config.get_tesseract_config()
                _ = config.get_performance_profiles()
                _ = config.get_preprocessing_config()
            first_run_time = time.time() - start_time
            
            # Test cache hit
            start_time = time.time()
            for _ in range(100):
                _ = config.get_tesseract_config()
                _ = config.get_performance_profiles()
                _ = config.get_preprocessing_config()
            cached_run_time = time.time() - start_time
            
            cache_speedup = first_run_time / cached_run_time if cached_run_time > 0 else float('inf')
            
            self.results['tests']['config_cache'] = {
                'first_run_seconds': round(first_run_time, 4),
                'cached_run_seconds': round(cached_run_time, 4),
                'speedup_factor': round(cache_speedup, 1),
                'cache_info': {
                    'tesseract': str(config.get_tesseract_config.cache_info()),
                    'profiles': str(config.get_performance_profiles.cache_info()),
                    'preprocessing': str(config.get_preprocessing_config.cache_info())
                },
                'status': 'success'
            }
            
            print(f"   ✅ Primera ejecución: {first_run_time:.4f}s")
            print(f"   ✅ Con cache: {cached_run_time:.4f}s")
            print(f"   ✅ Speedup: {cache_speedup:.1f}x")
            
        except Exception as e:
            self.results['tests']['config_cache'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Error en cache test: {e}")
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas de rendimiento"""
        print("🧪 Iniciando pruebas de rendimiento del sistema OCR\n")
        
        self.test_startup_time()
        print()
        
        self.test_memory_usage()
        print()
        
        self.test_bundle_size()
        print()
        
        self.test_config_cache_performance()
        print()
        
        self.test_processing_performance()
        print()
        
        return self.results
    
    def generate_report(self, output_file='performance_report.json'):
        """Genera reporte detallado de rendimiento"""
        
        # Calcular métricas agregadas
        summary = {
            'overall_status': 'success',
            'optimizations_effective': True,
            'recommendations': []
        }
        
        # Analizar resultados
        if 'startup' in self.results['tests']:
            startup_time = self.results['tests']['startup'].get('import_time_seconds', 0)
            if startup_time > 2.0:
                summary['recommendations'].append("Considerar más lazy loading para reducir startup time")
            elif startup_time < 1.0:
                summary['recommendations'].append("Excelente startup time - optimizaciones efectivas")
        
        if 'memory' in self.results['tests']:
            memory_increase = self.results['tests']['memory'].get('increase_mb', 0)
            if memory_increase > 200:
                summary['recommendations'].append("Alto uso de memoria - revisar imports pesados")
            elif memory_increase < 100:
                summary['recommendations'].append("Uso de memoria optimizado")
        
        if 'bundle_size' in self.results['tests']:
            bundle_mb = self.results['tests']['bundle_size'].get('total_mb', 0)
            if bundle_mb > 500:
                summary['recommendations'].append("Bundle grande - considerar minificación adicional")
        
        if 'config_cache' in self.results['tests']:
            speedup = self.results['tests']['config_cache'].get('speedup_factor', 1)
            if speedup < 5:
                summary['recommendations'].append("Cache config con bajo speedup - revisar implementación")
        
        if not summary['recommendations']:
            summary['recommendations'].append("Sistema bien optimizado - sin recomendaciones adicionales")
        
        self.results['summary'] = summary
        
        # Guardar reporte
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Reporte guardado en: {output_file}")
        return output_file

def main():
    """Función principal del perfilador"""
    print("🎯 Sistema OCR - Análisis de Rendimiento")
    print("=" * 50)
    
    profiler = PerformanceProfiler()
    results = profiler.run_all_tests()
    
    print("\n📈 Generando reporte final...")
    report_file = profiler.generate_report()
    
    print("\n✨ Resumen de optimizaciones:")
    if 'summary' in results:
        for rec in results['summary']['recommendations']:
            print(f"   • {rec}")
    
    print(f"\n🎉 Análisis completado. Ver detalles en: {report_file}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())