"""
Optimizaciones avanzadas para ONNX Runtime
Implementa cuantización, optimización de grafos y técnicas de vanguardia
"""

import os
import logging
import tempfile
from pathlib import Path
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
from onnxruntime.quantization.calibrate import create_calibrator
import numpy as np

logger = logging.getLogger(__name__)

class AdvancedONNXOptimizer:
    """Optimizador avanzado para modelos ONNX"""
    
    def __init__(self):
        self.optimized_models_cache = {}
        self.quantization_cache = {}
        self.session_cache = {}
        
    def optimize_model_graph(self, model_path, output_path=None):
        """Optimiza el grafo del modelo ONNX"""
        try:
            if output_path is None:
                output_path = str(Path(model_path).with_suffix('.optimized.onnx'))
            
            # Cargar modelo
            model = onnx.load(model_path)
            
            # Optimizaciones básicas del grafo
            from onnx import optimizer
            
            # Aplicar optimizaciones comunes
            optimized_model = optimizer.optimize(model, [
                'eliminate_deadend',
                'eliminate_identity',
                'eliminate_nop_dropout',
                'eliminate_nop_pad',
                'eliminate_unused_initializer',
                'extract_constant_to_initializer',
                'fuse_add_bias_into_conv',
                'fuse_bn_into_conv',
                'fuse_consecutive_concats',
                'fuse_consecutive_log_softmax',
                'fuse_consecutive_reduce_unsqueeze',
                'fuse_consecutive_squeezes',
                'fuse_consecutive_transposes',
                'fuse_matmul_add_bias_into_gemm',
                'fuse_pad_into_conv',
                'fuse_transpose_into_gemm',
                'lift_lexical_references'
            ])
            
            # Guardar modelo optimizado
            onnx.save(optimized_model, output_path)
            
            # Validar modelo optimizado
            onnx.checker.check_model(optimized_model)
            
            logger.info(f"✅ Modelo optimizado guardado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error optimizando modelo {model_path}: {e}")
            return model_path
    
    def quantize_model_dynamic(self, model_path, output_path=None):
        """Aplica cuantización dinámica al modelo"""
        try:
            if output_path is None:
                output_path = str(Path(model_path).with_suffix('.quantized.onnx'))
            
            # Verificar si el modelo existe
            if not Path(model_path).exists():
                logger.warning(f"Modelo no encontrado: {model_path}")
                return model_path
            
            # Aplicar cuantización dinámica
            quantize_dynamic(
                model_input=model_path,
                model_output=output_path,
                weight_type=QuantType.QUInt8,
                optimize_model=True,
                use_external_data_format=False
            )
            
            # Verificar tamaño del modelo
            original_size = Path(model_path).stat().st_size / 1024 / 1024
            quantized_size = Path(output_path).stat().st_size / 1024 / 1024
            
            logger.info(f"✅ Modelo cuantizado: {original_size:.1f}MB → {quantized_size:.1f}MB")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error cuantizando modelo {model_path}: {e}")
            return model_path
    
    def create_optimized_session(self, model_path, enable_all_optimizations=True):
        """Crea sesión ONNX con optimizaciones avanzadas"""
        try:
            # Verificar caché
            cache_key = f"{model_path}_{enable_all_optimizations}"
            if cache_key in self.session_cache:
                return self.session_cache[cache_key]
            
            # Configurar opciones de sesión
            session_options = ort.SessionOptions()
            
            # Optimizaciones de memoria
            session_options.enable_mem_pattern = False
            session_options.enable_mem_reuse = True
            session_options.enable_cpu_mem_arena = False
            
            # Optimizaciones de ejecución
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            session_options.intra_op_num_threads = 2
            session_options.inter_op_num_threads = 1
            
            # Nivel de optimización del grafo
            if enable_all_optimizations:
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            else:
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
            
            # Configuraciones específicas del proveedor
            provider_options = {
                'CPUExecutionProvider': {
                    'intra_op_num_threads': 2,
                    'inter_op_num_threads': 1,
                    'omp_num_threads': 2,
                    'enable_cpu_mem_arena': False
                }
            }
            
            providers = [('CPUExecutionProvider', provider_options['CPUExecutionProvider'])]
            
            # Crear sesión
            session = ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=providers
            )
            
            # Guardar en caché
            self.session_cache[cache_key] = session
            
            logger.info(f"✅ Sesión optimizada creada: {model_path}")
            return session
            
        except Exception as e:
            logger.error(f"❌ Error creando sesión optimizada: {e}")
            return None
    
    def optimize_model_pipeline(self, model_path):
        """Pipeline completo de optimización"""
        try:
            logger.info(f"🔄 Iniciando pipeline de optimización: {model_path}")
            
            # Paso 1: Optimización del grafo
            optimized_path = self.optimize_model_graph(model_path)
            
            # Paso 2: Cuantización dinámica
            quantized_path = self.quantize_model_dynamic(optimized_path)
            
            # Paso 3: Crear sesión optimizada
            session = self.create_optimized_session(quantized_path)
            
            # Información de la sesión
            if session:
                inputs = [(inp.name, inp.shape, inp.type) for inp in session.get_inputs()]
                outputs = [(out.name, out.shape, out.type) for out in session.get_outputs()]
                
                logger.info(f"📊 Modelo optimizado - Entradas: {len(inputs)}, Salidas: {len(outputs)}")
            
            return {
                'original_path': model_path,
                'optimized_path': optimized_path,
                'quantized_path': quantized_path,
                'session': session,
                'optimization_successful': session is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Error en pipeline de optimización: {e}")
            return {
                'original_path': model_path,
                'optimization_successful': False,
                'error': str(e)
            }
    
    def get_model_info(self, model_path):
        """Obtiene información detallada del modelo"""
        try:
            model = onnx.load(model_path)
            
            # Información básica
            info = {
                'model_version': model.model_version,
                'producer_name': model.producer_name,
                'producer_version': model.producer_version,
                'domain': model.domain,
                'graph_name': model.graph.name,
                'node_count': len(model.graph.node),
                'input_count': len(model.graph.input),
                'output_count': len(model.graph.output),
                'initializer_count': len(model.graph.initializer)
            }
            
            # Información de los nodos
            node_types = {}
            for node in model.graph.node:
                node_types[node.op_type] = node_types.get(node.op_type, 0) + 1
            
            info['node_types'] = node_types
            
            # Tamaño del archivo
            info['file_size_mb'] = Path(model_path).stat().st_size / 1024 / 1024
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo información del modelo: {e}")
            return {}
    
    def benchmark_model_performance(self, session, input_shape=(1, 3, 224, 224)):
        """Benchmark del rendimiento del modelo"""
        try:
            # Crear datos de prueba
            input_name = session.get_inputs()[0].name
            dummy_input = np.random.randn(*input_shape).astype(np.float32)
            
            # Warm-up
            for _ in range(3):
                session.run(None, {input_name: dummy_input})
            
            # Benchmark
            times = []
            for _ in range(10):
                start_time = time.time()
                session.run(None, {input_name: dummy_input})
                times.append(time.time() - start_time)
            
            return {
                'avg_inference_time': np.mean(times),
                'min_inference_time': np.min(times),
                'max_inference_time': np.max(times),
                'std_inference_time': np.std(times)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en benchmark: {e}")
            return {}

# Instancia global
advanced_onnx_optimizer = AdvancedONNXOptimizer()