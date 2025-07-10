"""
Módulo de procesamiento espacial para OCR
Implementa lógica de oro espacial con líneas lógicas y búsqueda geométrica
"""

import logging
import re
import math
from typing import List, Dict, Any, Optional, Tuple

# Configurar logging
logger = logging.getLogger(__name__)


def get_logical_lines(words_with_coordinates: List[Dict], geometry_config: Dict) -> List[List[Dict]]:
    """
    Agrupa palabras en líneas lógicas basadas en coordenadas geométricas
    
    Args:
        words_with_coordinates: Lista de palabras con coordenadas y texto
        geometry_config: Configuración de tolerancias geométricas
        
    Returns:
        Lista de líneas lógicas, cada línea es una lista de palabras
    """
    try:
        if not words_with_coordinates:
            logger.debug("No hay palabras con coordenadas para procesar")
            return []
            
        # Obtener tolerancias de configuración
        y_tolerance = geometry_config.get('y_tolerance', 15)
        x_spacing_threshold = geometry_config.get('x_spacing_threshold', 100)
        
        # Ordenar palabras por coordenada Y primero, luego por X
        sorted_words = sorted(words_with_coordinates, key=lambda w: (
            w.get('coordinates', [0, 0, 0, 0])[1],  # y1
            w.get('coordinates', [0, 0, 0, 0])[0]   # x1
        ))
        
        logical_lines = []
        current_line = []
        current_y = None
        
        for word in sorted_words:
            coords = word.get('coordinates', [0, 0, 0, 0])
            if len(coords) < 4:
                continue
                
            word_y = coords[1]  # y1
            
            # Si es la primera palabra o está en la misma línea Y
            if current_y is None or abs(word_y - current_y) <= y_tolerance:
                current_line.append(word)
                current_y = word_y if current_y is None else current_y
            else:
                # Nueva línea lógica
                if current_line:
                    # Ordenar palabras en la línea por X
                    current_line.sort(key=lambda w: w.get('coordinates', [0, 0, 0, 0])[0])
                    logical_lines.append(current_line)
                
                current_line = [word]
                current_y = word_y
        
        # Agregar la última línea
        if current_line:
            current_line.sort(key=lambda w: w.get('coordinates', [0, 0, 0, 0])[0])
            logical_lines.append(current_line)
        
        logger.debug(f"Generadas {len(logical_lines)} líneas lógicas de {len(words_with_coordinates)} palabras")
        return logical_lines
        
    except Exception as e:
        logger.error(f"Error generando líneas lógicas: {e}", exc_info=True)
        return []


def find_value_spatially(logical_lines: List[List[Dict]], keyword_geometry: List[float], 
                        spatial_config: Dict, geometry_config: Dict) -> Optional[str]:
    """
    Busca un valor espacialmente relacionado con una palabra clave
    
    Args:
        logical_lines: Líneas lógicas generadas
        keyword_geometry: Coordenadas de la palabra clave [x1, y1, x2, y2]
        spatial_config: Configuración de búsqueda espacial
        geometry_config: Configuración geométrica general
        
    Returns:
        Valor encontrado o None
    """
    try:
        if not logical_lines or not keyword_geometry or len(keyword_geometry) < 4:
            return None
            
        # Obtener configuración espacial
        search_direction = spatial_config.get('search_direction', 'horizontal_right')
        search_radius = spatial_config.get('search_radius', 200)
        value_patterns = spatial_config.get('value_patterns', [])
        
        keyword_x1, keyword_y1, keyword_x2, keyword_y2 = keyword_geometry
        keyword_center_x = (keyword_x1 + keyword_x2) / 2
        keyword_center_y = (keyword_y1 + keyword_y2) / 2
        
        # Buscar en líneas lógicas
        for line in logical_lines:
            for word in line:
                coords = word.get('coordinates', [0, 0, 0, 0])
                if len(coords) < 4:
                    continue
                    
                word_x1, word_y1, word_x2, word_y2 = coords
                word_center_x = (word_x1 + word_x2) / 2
                word_center_y = (word_y1 + word_y2) / 2
                
                # Calcular distancia
                distance = math.sqrt((word_center_x - keyword_center_x)**2 + 
                                   (word_center_y - keyword_center_y)**2)
                
                if distance > search_radius:
                    continue
                
                # Verificar dirección de búsqueda
                if search_direction == 'horizontal_right':
                    if word_center_x <= keyword_center_x:
                        continue
                elif search_direction == 'horizontal_left':
                    if word_center_x >= keyword_center_x:
                        continue
                elif search_direction == 'vertical_below':
                    if word_center_y <= keyword_center_y:
                        continue
                elif search_direction == 'vertical_above':
                    if word_center_y >= keyword_center_y:
                        continue
                
                # Verificar patrones de valor
                word_text = word.get('text', word.get('texto', ''))
                if not word_text:
                    continue
                
                # Si no hay patrones específicos, devolver el primer texto encontrado
                if not value_patterns:
                    return word_text.strip()
                
                # Verificar contra patrones
                for pattern in value_patterns:
                    if re.search(pattern, word_text):
                        return word_text.strip()
        
        return None
        
    except Exception as e:
        logger.error(f"Error en búsqueda espacial: {e}", exc_info=True)
        return None


def calculate_spatial_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calcula la distancia euclidiana entre dos puntos
    
    Args:
        point1: Coordenadas del primer punto (x, y)
        point2: Coordenadas del segundo punto (x, y)
        
    Returns:
        Distancia euclidiana
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def find_words_in_region(words_with_coordinates: List[Dict], 
                        region: Tuple[float, float, float, float]) -> List[Dict]:
    """
    Encuentra palabras dentro de una región específica
    
    Args:
        words_with_coordinates: Lista de palabras con coordenadas
        region: Región de búsqueda (x1, y1, x2, y2)
        
    Returns:
        Lista de palabras dentro de la región
    """
    try:
        region_x1, region_y1, region_x2, region_y2 = region
        words_in_region = []
        
        for word in words_with_coordinates:
            coords = word.get('coordinates', [0, 0, 0, 0])
            if len(coords) < 4:
                continue
                
            word_x1, word_y1, word_x2, word_y2 = coords
            word_center_x = (word_x1 + word_x2) / 2
            word_center_y = (word_y1 + word_y2) / 2
            
            # Verificar si el centro de la palabra está dentro de la región
            if (region_x1 <= word_center_x <= region_x2 and 
                region_y1 <= word_center_y <= region_y2):
                words_in_region.append(word)
        
        return words_in_region
        
    except Exception as e:
        logger.error(f"Error encontrando palabras en región: {e}", exc_info=True)
        return []


def group_words_by_proximity(words_with_coordinates: List[Dict], 
                            proximity_threshold: float = 50) -> List[List[Dict]]:
    """
    Agrupa palabras por proximidad espacial
    
    Args:
        words_with_coordinates: Lista de palabras con coordenadas
        proximity_threshold: Umbral de proximidad en píxeles
        
    Returns:
        Lista de grupos de palabras próximas
    """
    try:
        if not words_with_coordinates:
            return []
            
        groups = []
        remaining_words = words_with_coordinates.copy()
        
        while remaining_words:
            current_group = [remaining_words.pop(0)]
            
            i = 0
            while i < len(remaining_words):
                word = remaining_words[i]
                word_coords = word.get('coordinates', [0, 0, 0, 0])
                if len(word_coords) < 4:
                    i += 1
                    continue
                    
                word_center = ((word_coords[0] + word_coords[2]) / 2, 
                              (word_coords[1] + word_coords[3]) / 2)
                
                # Verificar proximidad con cualquier palabra del grupo actual
                is_close = False
                for group_word in current_group:
                    group_coords = group_word.get('coordinates', [0, 0, 0, 0])
                    if len(group_coords) < 4:
                        continue
                        
                    group_center = ((group_coords[0] + group_coords[2]) / 2, 
                                   (group_coords[1] + group_coords[3]) / 2)
                    
                    distance = calculate_spatial_distance(word_center, group_center)
                    if distance <= proximity_threshold:
                        is_close = True
                        break
                
                if is_close:
                    current_group.append(remaining_words.pop(i))
                else:
                    i += 1
            
            groups.append(current_group)
        
        return groups
        
    except Exception as e:
        logger.error(f"Error agrupando palabras por proximidad: {e}", exc_info=True)
        return []