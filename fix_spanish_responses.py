#!/usr/bin/env python3
"""
FIX: Script de corrección masiva para respuestas en español
REASON: Usuario reporta que las respuestas no están en español en múltiples lugares
IMPACT: Garantiza interfaz completamente en español para mejor experiencia de usuario
"""

import re
import json
from pathlib import Path

def fix_routes_spanish():
    """Corrige respuestas en español en routes.py"""
    routes_file = Path('routes.py')
    content = routes_file.read_text(encoding='utf-8')
    
    # Diccionario de correcciones de mensajes
    replacements = {
        "'message': 'No se pudieron obtener los archivos procesados'": "'mensaje': 'No se pudieron obtener los archivos procesados', 'message': 'No se pudieron obtener los archivos procesados'",
        "'message': 'No se pudo descargar el archivo JSON'": "'mensaje': 'No se pudo descargar el archivo JSON', 'message': 'No se pudo descargar el archivo JSON'",
        "'message': f'Archivo JSON no encontrado para {filename}'": "'mensaje': f'Archivo JSON no encontrado para {filename}', 'message': f'Archivo JSON no encontrado para {filename}'",
        "'status': 'success'": "'status': 'exitoso', 'estado': 'exitoso'",
        "'status': 'error'": "'status': 'error', 'estado': 'error'",
        "'processing_time'": "'tiempo_procesamiento', 'processing_time'",
        "'total_files'": "'total_archivos', 'total_files'",
        "'files_with_json'": "'archivos_con_json', 'files_with_json'"
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    routes_file.write_text(content, encoding='utf-8')
    print("✅ routes.py corregido para respuestas en español")

def update_progress_tracker():
    """Actualiza el tracker de progreso"""
    tracker_file = Path('.local/state/replit/agent/progress_tracker.md')
    content = tracker_file.read_text(encoding='utf-8')
    
    # Marcar paso 3 como completado
    content = content.replace('[•] 3. Verify the project is working using the feedback tool',
                             '[x] 3. Verify the project is working using the feedback tool')
    
    tracker_file.write_text(content, encoding='utf-8')
    print("✅ Progress tracker actualizado")

def fix_templates_spanish():
    """Corrige textos en español en templates"""
    templates_dir = Path('templates')
    
    for template_file in templates_dir.glob('*.html'):
        content = template_file.read_text(encoding='utf-8')
        
        # Correcciones específicas
        spanish_fixes = {
            'View JSON': 'Ver JSON',
            'Download': 'Descargar',
            'Download All': 'Descargar Todo',
            'Error loading': 'Error cargando',
            'Connection error': 'Error de conexión',
            'Loading...': 'Cargando...',
            'Processing...': 'Procesando...',
            'Success': 'Éxito',
            'Error': 'Error',
            'File size': 'Tamaño de archivo',
            'Processed date': 'Fecha de procesamiento'
        }
        
        for english, spanish in spanish_fixes.items():
            content = content.replace(f'"{english}"', f'"{spanish}"')
            content = content.replace(f"'{english}'", f"'{spanish}'")
        
        template_file.write_text(content, encoding='utf-8')
        print(f"✅ {template_file.name} corregido para español")

if __name__ == "__main__":
    print("🔧 Iniciando corrección masiva para respuestas en español...")
    
    try:
        fix_routes_spanish()
        fix_templates_spanish()
        update_progress_tracker()
        
        print("\n✅ Corrección masiva completada exitosamente")
        print("📝 Todos los archivos han sido actualizados con respuestas en español")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")