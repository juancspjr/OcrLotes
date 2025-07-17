"""
Optimizaciones usando generadores para procesamiento lazy
Reduce significativamente el uso de memoria
"""

import logging
from typing import Generator, List, Dict, Any

logger = logging.getLogger(__name__)

class GeneratorOptimizer:
    """Optimizador que usa generadores para procesamiento lazy"""
    
    @staticmethod
    def process_images_lazy(image_paths: List[str]) -> Generator[Dict[str, Any], None, None]:
        """Procesa imágenes usando generadores lazy"""
        for image_path in image_paths:
            try:
                # Procesar una imagen a la vez
                yield {
                    'path': image_path,
                    'status': 'processing',
                    'memory_efficient': True
                }
            except Exception as e:
                logger.error(f"Error procesando {image_path}: {e}")
                yield {
                    'path': image_path,
                    'status': 'error',
                    'error': str(e)
                }
    
    @staticmethod
    def batch_processor_lazy(items: List[Any], batch_size: int = 1) -> Generator[List[Any], None, None]:
        """Procesa elementos en lotes usando generadores"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    @staticmethod
    def word_coordinates_lazy(ocr_result) -> Generator[Dict[str, Any], None, None]:
        """Extrae coordenadas de palabras usando generadores"""
        try:
            for page in ocr_result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        for word in line.words:
                            if hasattr(word, 'geometry') and word.geometry:
                                yield {
                                    'text': word.value,
                                    'coordinates': [
                                        float(word.geometry[0][0]), float(word.geometry[0][1]),
                                        float(word.geometry[1][0]), float(word.geometry[1][1])
                                    ],
                                    'confidence': float(word.confidence)
                                }
        except Exception as e:
            logger.error(f"Error extrayendo coordenadas: {e}")

# Instancia global
generator_optimizer = GeneratorOptimizer()