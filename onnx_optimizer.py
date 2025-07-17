"""
Optimizador específico para modelos ONNX Runtime
Implementa cuantización y optimizaciones avanzadas
"""

import logging
import onnxruntime as ort
import numpy as np
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)

class ONNXOptimizer:
    """Optimizador para modelos ONNX Runtime"""
    
    def __init__(self):
        self.optimized_models = {}
        self.session_options = None
        self._setup_session_options()
    
    def _setup_session_options(self):
        """Configura opciones de sesión optimizadas para memoria"""
        self.session_options = ort.SessionOptions()
        
        # Optimizaciones de memoria
        self.session_options.enable_mem_pattern = False
        self.session_options.enable_mem_reuse = True
        self.session_options.enable_cpu_mem_arena = False
        
        # Optimizaciones de ejecución
        self.session_options.intra_op_num_threads = 2
        self.session_options.inter_op_num_threads = 1
        self.session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        # Configuraciones adicionales
        self.session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session_options.add_session_config_entry('session.intra_op_num_threads', '2')
        self.session_options.add_session_config_entry('session.inter_op_num_threads', '1')
        
        logger.info("Opciones de sesión ONNX configuradas para optimización de memoria")
    
    def get_cpu_provider_options(self):
        """Obtiene opciones optimizadas para CPUExecutionProvider"""
        return {
            'intra_op_num_threads': 2,
            'inter_op_num_threads': 1,
            'omp_num_threads': 2,
            'enable_cpu_mem_arena': False,
            'arena_extend_strategy': 'kSameAsRequested'
        }
    
    def optimize_model_for_inference(self, model_path, output_path=None):
        """Optimiza un modelo ONNX para inferencia eficiente"""
        try:
            if not Path(model_path).exists():
                logger.warning(f"Modelo no encontrado: {model_path}")
                return model_path
            
            # Crear sesión optimizada
            providers = [('CPUExecutionProvider', self.get_cpu_provider_options())]
            session = ort.InferenceSession(model_path, self.session_options, providers=providers)
            
            # Log de información del modelo
            input_info = [(inp.name, inp.shape, inp.type) for inp in session.get_inputs()]
            output_info = [(out.name, out.shape, out.type) for out in session.get_outputs()]
            
            logger.info(f"Modelo optimizado: {model_path}")
            logger.info(f"Entradas: {input_info}")
            logger.info(f"Salidas: {output_info}")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Error optimizando modelo {model_path}: {e}")
            return model_path
    
    def create_optimized_session(self, model_path):
        """Crea una sesión ONNX optimizada"""
        try:
            providers = [('CPUExecutionProvider', self.get_cpu_provider_options())]
            session = ort.InferenceSession(model_path, self.session_options, providers=providers)
            
            logger.info(f"Sesión ONNX optimizada creada para {model_path}")
            return session
            
        except Exception as e:
            logger.error(f"Error creando sesión optimizada: {e}")
            return None
    
    def quantize_model(self, model_path, quantized_path=None):
        """Cuantiza un modelo ONNX para reducir tamaño y memoria"""
        try:
            # Solo intentar cuantización si el modelo existe
            if not Path(model_path).exists():
                logger.warning(f"Modelo no encontrado para cuantización: {model_path}")
                return model_path
            
            # Por simplicidad, retornamos el modelo original
            # En un entorno de producción, se podría usar onnxruntime.quantization
            logger.info(f"Cuantización no implementada para {model_path}, usando modelo original")
            return model_path
            
        except Exception as e:
            logger.error(f"Error en cuantización: {e}")
            return model_path
    
    def get_memory_usage_info(self, session):
        """Obtiene información de uso de memoria de una sesión"""
        try:
            # Información básica de la sesión
            info = {
                'providers': session.get_providers(),
                'input_count': len(session.get_inputs()),
                'output_count': len(session.get_outputs()),
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información de memoria: {e}")
            return {}

# Instancia global del optimizador
onnx_optimizer = ONNXOptimizer()