#!/usr/bin/env python3
"""
Script para crear archivo de prueba con formato WhatsApp
FIX: Crear archivo de prueba para validar sistema de metadatos WhatsApp
REASON: Validar que el sistema funciona con formato WhatsApp correcto
IMPACT: Verificación completa del sistema con datos reales
"""

import os
import shutil
from PIL import Image
import json

def create_test_whatsapp_file():
    """
    Crear archivo de prueba con formato WhatsApp correcto
    Formato: 20250620-A--214056942235719@lid_Juanc_17-30.png
    """
    
    # Crear directorio de prueba si no existe
    test_dir = "temp/test_whatsapp"
    os.makedirs(test_dir, exist_ok=True)
    
    # Crear imagen de prueba simple
    img = Image.new('RGB', (300, 200), color='white')
    
    # Nombre de archivo en formato WhatsApp
    test_filename = "20250620-A--214056942235719@lid_Juanc_17-30.png"
    test_path = os.path.join(test_dir, test_filename)
    
    # Guardar imagen
    img.save(test_path)
    
    # Crear archivo de metadatos asociado
    metadata = {
        "filename_original": test_filename,
        "numerosorteo": "A",
        "idWhatsapp": "214056942235719@lid",
        "nombre": "Juanc",
        "horamin": "17-30",
        "caption": "Pago móvil realizado exitosamente",
        "otro_valor": "subir"
    }
    
    metadata_path = test_path.replace('.png', '.metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo de prueba creado: {test_path}")
    print(f"✅ Metadatos creados: {metadata_path}")
    print(f"📱 Formato WhatsApp: {test_filename}")
    print(f"   - Código sorteo: A")
    print(f"   - ID WhatsApp: 214056942235719@lid")
    print(f"   - Nombre: Juanc")
    print(f"   - Hora:Minuto: 17-30")
    
    return test_path, metadata_path

if __name__ == "__main__":
    create_test_whatsapp_file()