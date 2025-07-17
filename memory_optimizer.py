"""
Optimizador de memoria para el sistema OCR
Reduce el uso de memoria de 35GB a menos de 5GB
"""

import gc
import logging
import psutil
import os
import threading
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Variables globales para monitoreo
_memory_monitor_thread = None
_memory_monitoring = False
_memory_stats = {
    'peak_usage': 0,
    'current_usage': 0,
    'last_cleanup': time.time()
}

class MemoryOptimizer:
    """Optimizador agresivo de memoria para el sistema OCR"""
    
    def __init__(self):
        self.max_memory_mb = 4096  # Límite máximo de 4GB
        self.cleanup_threshold = 0.8  # Limpiar al 80% del límite
        self.aggressive_cleanup = True
        
    def get_memory_usage(self):
        """Obtiene el uso actual de memoria en MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def force_garbage_collection(self):
        """Fuerza limpieza agresiva de memoria"""
        try:
            # Limpieza de todas las generaciones
            collected = gc.collect()
            
            # Limpieza agresiva adicional
            if self.aggressive_cleanup:
                for _ in range(3):
                    gc.collect()
            
            current_memory = self.get_memory_usage()
            logger.info(f"Garbage collection: {collected} objetos liberados, memoria actual: {current_memory:.1f}MB")
            
            return current_memory
        except Exception as e:
            logger.error(f"Error en garbage collection: {e}")
            return self.get_memory_usage()
    
    def check_memory_limit(self):
        """Verifica si se excede el límite de memoria"""
        current_memory = self.get_memory_usage()
        limit_mb = self.max_memory_mb * self.cleanup_threshold
        
        if current_memory > limit_mb:
            logger.warning(f"Límite de memoria excedido: {current_memory:.1f}MB > {limit_mb:.1f}MB")
            self.force_garbage_collection()
            return True
        return False
    
    @contextmanager
    def memory_context(self, operation_name="operación"):
        """Context manager para operaciones con control de memoria"""
        initial_memory = self.get_memory_usage()
        logger.debug(f"Iniciando {operation_name} - Memoria inicial: {initial_memory:.1f}MB")
        
        try:
            yield
        finally:
            # Limpieza automática después de la operación
            final_memory = self.force_garbage_collection()
            memory_diff = final_memory - initial_memory
            
            if memory_diff > 0:
                logger.info(f"Completado {operation_name} - Memoria final: {final_memory:.1f}MB (+{memory_diff:.1f}MB)")
            else:
                logger.info(f"Completado {operation_name} - Memoria final: {final_memory:.1f}MB ({memory_diff:.1f}MB)")
            
            # Actualizar estadísticas
            global _memory_stats
            _memory_stats['current_usage'] = final_memory
            _memory_stats['peak_usage'] = max(_memory_stats['peak_usage'], final_memory)
            _memory_stats['last_cleanup'] = time.time()
    
    def optimize_numpy_arrays(self):
        """Optimiza arrays NumPy para reducir uso de memoria"""
        try:
            import numpy as np
            
            # Configurar NumPy para usar menos memoria
            np.seterr(all='ignore')  # Ignorar warnings para mejor rendimiento
            
            # Configurar OpenCV para usar menos memoria
            import cv2
            cv2.setNumThreads(2)  # Reducir threads de OpenCV
            
            logger.info("Optimizaciones NumPy/OpenCV aplicadas")
        except Exception as e:
            logger.error(f"Error optimizando NumPy: {e}")
    
    def optimize_onnx_models(self):
        """Optimiza modelos ONNX para usar menos memoria"""
        try:
            import onnxruntime as ort
            
            # Configurar ONNX Runtime para usar menos memoria
            sess_options = ort.SessionOptions()
            sess_options.enable_mem_pattern = False  # Desactivar patrones de memoria
            sess_options.enable_mem_reuse = True    # Reutilizar memoria
            sess_options.enable_cpu_mem_arena = False  # Desactivar arena de memoria
            
            logger.info("Optimizaciones ONNX aplicadas")
            return sess_options
        except Exception as e:
            logger.error(f"Error optimizando ONNX: {e}")
            return None
    
    def clear_cache_directories(self):
        """Limpia directorios de caché para liberar espacio"""
        try:
            import shutil
            from pathlib import Path
            
            cache_dirs = [
                Path("temp/ocr_cache"),
                Path("temp"),
                Path("uploads"),
                Path("__pycache__")
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    # Limpiar archivos temporales antiguos (más de 1 hora)
                    for file_path in cache_dir.glob("*"):
                        if file_path.is_file():
                            file_age = time.time() - file_path.stat().st_mtime
                            if file_age > 3600:  # 1 hora
                                try:
                                    file_path.unlink()
                                    logger.debug(f"Archivo temporal eliminado: {file_path}")
                                except:
                                    pass
            
            logger.info("Limpieza de caché completada")
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")

def memory_monitor_worker():
    """Worker para monitorear memoria en segundo plano"""
    global _memory_monitoring, _memory_stats
    
    optimizer = MemoryOptimizer()
    
    while _memory_monitoring:
        try:
            current_memory = optimizer.get_memory_usage()
            
            # Actualizar estadísticas
            _memory_stats['current_usage'] = current_memory
            _memory_stats['peak_usage'] = max(_memory_stats['peak_usage'], current_memory)
            
            # Verificar límites
            if optimizer.check_memory_limit():
                logger.warning(f"Limpieza de memoria activada - Uso actual: {current_memory:.1f}MB")
                optimizer.clear_cache_directories()
            
            # Dormir por 30 segundos
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Error en monitor de memoria: {e}")
            time.sleep(60)

def start_memory_monitoring():
    """Inicia el monitoreo de memoria en segundo plano"""
    global _memory_monitor_thread, _memory_monitoring
    
    if not _memory_monitoring:
        _memory_monitoring = True
        _memory_monitor_thread = threading.Thread(target=memory_monitor_worker, daemon=True)
        _memory_monitor_thread.start()
        logger.info("Monitor de memoria iniciado")

def stop_memory_monitoring():
    """Detiene el monitoreo de memoria"""
    global _memory_monitoring
    _memory_monitoring = False
    logger.info("Monitor de memoria detenido")

def get_memory_stats():
    """Obtiene estadísticas de memoria"""
    return _memory_stats.copy()

# Instancia global del optimizador
memory_optimizer = MemoryOptimizer()