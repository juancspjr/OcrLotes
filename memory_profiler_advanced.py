"""
Perfilador avanzado de memoria para el sistema OCR
Implementa tracemalloc, memory_profiler y análisis de objetos
"""

import gc
import tracemalloc
import logging
import psutil
import os
import threading
import time
from datetime import datetime
from pathlib import Path
try:
    import objgraph
except ImportError:
    objgraph = None
import json

logger = logging.getLogger(__name__)

class AdvancedMemoryProfiler:
    """Perfilador avanzado de memoria con análisis detallado"""
    
    def __init__(self):
        self.snapshots = []
        self.profiling_active = False
        self.baseline_snapshot = None
        self.reports_dir = Path("temp/memory_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def start_profiling(self):
        """Inicia el perfilado de memoria avanzado"""
        if not self.profiling_active:
            tracemalloc.start()
            self.profiling_active = True
            self.baseline_snapshot = tracemalloc.take_snapshot()
            logger.info("Perfilado de memoria avanzado iniciado")
    
    def take_snapshot(self, label=""):
        """Toma una instantánea de memoria"""
        if self.profiling_active:
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append({
                'timestamp': datetime.now(),
                'label': label,
                'snapshot': snapshot,
                'memory_usage': self._get_memory_usage()
            })
            return snapshot
        return None
    
    def _get_memory_usage(self):
        """Obtiene información detallada del uso de memoria"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Memoria física
            'vms_mb': memory_info.vms / 1024 / 1024,  # Memoria virtual
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'total_mb': psutil.virtual_memory().total / 1024 / 1024
        }
    
    def analyze_top_memory_consumers(self, limit=10):
        """Analiza los mayores consumidores de memoria"""
        if not self.profiling_active or not self.snapshots:
            return []
        
        current_snapshot = self.snapshots[-1]['snapshot']
        top_stats = current_snapshot.statistics('lineno')
        
        results = []
        for stat in top_stats[:limit]:
            results.append({
                'file': stat.traceback.format()[0],
                'size_mb': stat.size / 1024 / 1024,
                'count': stat.count,
                'average_size': stat.size / stat.count if stat.count > 0 else 0
            })
        
        return results
    
    def compare_snapshots(self, snapshot1_idx=0, snapshot2_idx=-1):
        """Compara dos instantáneas de memoria"""
        if len(self.snapshots) < 2:
            return None
        
        snap1 = self.snapshots[snapshot1_idx]['snapshot']
        snap2 = self.snapshots[snapshot2_idx]['snapshot']
        
        top_stats = snap2.compare_to(snap1, 'lineno')
        
        results = []
        for stat in top_stats[:10]:
            results.append({
                'file': stat.traceback.format()[0],
                'size_diff_mb': stat.size_diff / 1024 / 1024,
                'count_diff': stat.count_diff,
                'current_size_mb': stat.size / 1024 / 1024
            })
        
        return results
    
    def analyze_object_growth(self):
        """Analiza el crecimiento de objetos en memoria"""
        if objgraph is None:
            return []
        
        try:
            # Tipos de objetos más comunes
            most_common = objgraph.most_common_types(limit=15)
            
            # Buscar objetos que crecen
            growth_info = []
            for obj_type, count in most_common:
                if count > 100:  # Solo objetos con más de 100 instancias
                    growth_info.append({
                        'type': obj_type,
                        'count': count,
                        'refs': len(objgraph.by_type(obj_type)[:10])  # Muestra de referencias
                    })
            
            return growth_info
        except Exception as e:
            logger.error(f"Error analizando crecimiento de objetos: {e}")
            return []
    
    def generate_memory_report(self):
        """Genera un reporte completo de memoria"""
        if not self.profiling_active:
            return None
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_memory': self._get_memory_usage(),
            'top_consumers': self.analyze_top_memory_consumers(),
            'object_growth': self.analyze_object_growth(),
            'snapshot_count': len(self.snapshots)
        }
        
        if len(self.snapshots) >= 2:
            report['memory_diff'] = self.compare_snapshots()
        
        # Guardar reporte
        report_file = self.reports_dir / f"memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte de memoria guardado: {report_file}")
        return report
    
    def optimize_based_on_analysis(self):
        """Optimiza memoria basándose en el análisis"""
        report = self.generate_memory_report()
        if not report:
            return
        
        optimizations = []
        
        # Verificar alto uso de memoria
        if report['current_memory']['rss_mb'] > 400:
            optimizations.append("Memoria RSS alta - activar limpieza agresiva")
            gc.collect()
        
        # Verificar objetos con crecimiento
        for obj_info in report['object_growth']:
            if obj_info['count'] > 1000:
                optimizations.append(f"Alto número de {obj_info['type']} - revisar liberación")
        
        # Verificar diferencias de memoria
        if 'memory_diff' in report:
            for diff in report['memory_diff']:
                if diff['size_diff_mb'] > 10:
                    optimizations.append(f"Crecimiento de {diff['size_diff_mb']:.1f}MB en {diff['file']}")
        
        logger.info(f"Optimizaciones recomendadas: {len(optimizations)}")
        for opt in optimizations:
            logger.info(f"  - {opt}")
        
        return optimizations
    
    def stop_profiling(self):
        """Detiene el perfilado de memoria"""
        if self.profiling_active:
            self.generate_memory_report()
            tracemalloc.stop()
            self.profiling_active = False
            logger.info("Perfilado de memoria detenido")

# Instancia global del perfilador
advanced_profiler = AdvancedMemoryProfiler()

# Decorador para perfilar funciones específicas
def profile_memory(func):
    """Decorador para perfilar memoria de funciones específicas"""
    def wrapper(*args, **kwargs):
        advanced_profiler.take_snapshot(f"antes_{func.__name__}")
        result = func(*args, **kwargs)
        advanced_profiler.take_snapshot(f"después_{func.__name__}")
        return result
    return wrapper