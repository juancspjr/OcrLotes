#!/usr/bin/env python3
"""
Script de prueba para validar MANDATO CRÍTICO #2: Lógica de Oro basada en coordenadas
Valida la implementación de texto_total_ocr ordenado y concepto_empresarial refinado
"""

import requests
import json
import time

def test_logica_oro():
    """Prueba la lógica de oro con archivos nuevos"""
    print("🔬 INICIANDO PRUEBA DE LÓGICA DE ORO - MANDATO CRÍTICO #2")
    
    # Crear archivo de prueba con formato WhatsApp
    test_filename = f"20250707-TEST--{int(time.time())}@lid_TestLogicaOro_07-36.png"
    
    # Copiar un archivo existente para prueba
    import shutil
    import os
    from pathlib import Path
    
    # Buscar archivos existentes en uploads
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        existing_files = list(uploads_dir.glob("*.png"))
        if existing_files:
            source_file = existing_files[0]
            target_file = uploads_dir / test_filename
            
            # Copiar archivo para prueba
            shutil.copy2(source_file, target_file)
            print(f"📁 Archivo de prueba creado: {test_filename}")
            
            # Procesar lote
            print("⚙️ Procesando lote...")
            response = requests.post("http://localhost:5000/api/ocr/process_batch")
            
            if response.status_code == 200:
                result = response.json()
                request_id = result.get('request_id', '')
                print(f"✅ Lote procesado. Request ID: {request_id}")
                
                # Esperar un momento
                time.sleep(2)
                
                # Extraer resultados
                print("📊 Extrayendo resultados...")
                extract_response = requests.get("http://localhost:5000/api/extract_results")
                
                if extract_response.status_code == 200:
                    extract_data = extract_response.json()
                    
                    # Buscar nuestro archivo de prueba
                    for archivo in extract_data.get('archivos_procesados', []):
                        if test_filename in archivo.get('nombre_archivo', ''):
                            print(f"\n🎯 VALIDACIÓN MANDATO #2 - ARCHIVO: {archivo['nombre_archivo']}")
                            
                            # Validar texto_total_ocr
                            texto_total_ocr = archivo.get('texto_total_ocr', '')
                            concepto = archivo.get('concepto', '')
                            
                            print(f"📝 TEXTO_TOTAL_OCR ({len(texto_total_ocr)} chars):")
                            print(f"   {texto_total_ocr[:200]}...")
                            
                            print(f"🎯 CONCEPTO ({len(concepto)} chars): '{concepto}'")
                            
                            # Validar criterios del mandato
                            if len(texto_total_ocr) > len(concepto):
                                print("✅ CRITERIO #1: texto_total_ocr > concepto ✓")
                            else:
                                print("❌ CRITERIO #1: texto_total_ocr debe ser mayor que concepto")
                            
                            if len(concepto) <= 50:
                                print(f"✅ CRITERIO #2: concepto ≤ 50 chars ({len(concepto)}) ✓")
                            else:
                                print(f"❌ CRITERIO #2: concepto debe ser ≤ 50 chars (actual: {len(concepto)})")
                            
                            if concepto and not concepto.isdigit():
                                print("✅ CRITERIO #3: concepto no es solo números ✓")
                            else:
                                print("❌ CRITERIO #3: concepto no debe ser solo números")
                            
                            return True
                    
                    print("❌ Archivo de prueba no encontrado en resultados")
                else:
                    print(f"❌ Error extrayendo resultados: {extract_response.status_code}")
            else:
                print(f"❌ Error procesando lote: {response.status_code}")
            
            # Limpiar archivo de prueba
            if target_file.exists():
                target_file.unlink()
                print(f"🧹 Archivo de prueba eliminado: {test_filename}")
        else:
            print("❌ No hay archivos existentes para copiar")
    else:
        print("❌ Directorio uploads no existe")
    
    return False

if __name__ == "__main__":
    success = test_logica_oro()
    exit(0 if success else 1)