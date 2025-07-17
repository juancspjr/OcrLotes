#!/usr/bin/env python3
"""
Test script para demostrar el sistema asíncrono de alto volumen OCR
Muestra cómo usar tanto el sistema de archivos como la API HTTP
"""

import os
import json
import time
import shutil
import requests
from datetime import datetime

def test_file_system_approach():
    """
    Test 1: Demostrar ingesta por sistema de archivos
    Simula recibos de pago móvil con metadata de WhatsApp
    """
    print("🔧 Test 1: Sistema de archivos asíncrono")
    
    # Verificar que existe una imagen de test
    test_image = "test_factura.png"
    if not os.path.exists(test_image):
        print(f"❌ Imagen de test {test_image} no encontrada")
        return
    
    # Generar metadata de WhatsApp simulado
    metadata_examples = [
        {
            'request_id': '20250705-A_123456789012345@s.whatsapp.net_JuanPerez_18-30.png',
            'caption': 'Pago móvil Banesco por comida'
        },
        {
            'request_id': '20250705-B_987654321098765@s.whatsapp.net_MariaGomez_19-15.png', 
            'caption': 'Transferencia Mercantil para gasolina'
        }
    ]
    
    # Crear directorio inbox si no existe
    inbox_dir = "data/inbox"
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Copiar imagen con diferentes nombres y captions
    for i, meta in enumerate(metadata_examples):
        # Copiar imagen
        dest_path = os.path.join(inbox_dir, meta['request_id'])
        shutil.copy2(test_image, dest_path)
        
        # Crear archivo caption
        caption_path = dest_path.replace('.png', '.caption.txt')
        with open(caption_path, 'w', encoding='utf-8') as f:
            f.write(meta['caption'])
        
        print(f"✅ Imagen {i+1} colocada en inbox: {meta['request_id']}")
        print(f"   Caption: {meta['caption']}")
    
    print(f"\n⏱️  Imágenes en cola. El worker procesará automáticamente...")
    print("   Verificar resultados en data/results/ en ~30 segundos")

def test_http_api_approach():
    """
    Test 2: Demostrar ingesta por API HTTP
    Simula integración con n8n u otros sistemas web
    """
    print("\n🌐 Test 2: API HTTP asíncrona")
    
    # URL del servidor (ajustar si está en otro puerto)
    base_url = "http://localhost:5000"
    
    # Verificar que el servidor está corriendo
    try:
        response = requests.get(f"{base_url}/api/ocr/status", timeout=5)
        print("✅ Servidor disponible")
        print(f"   Status: {response.json().get('status')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Servidor no disponible: {e}")
        return
    
    # Verificar imagen de test
    test_image = "test_factura.png"
    if not os.path.exists(test_image):
        print(f"❌ Imagen de test {test_image} no encontrada")
        return
    
    # Preparar datos de prueba
    timestamp = datetime.now().strftime("%H-%M")
    form_data = {
        'sorteo_fecha': '20250705',
        'sorteo_conteo': 'C',
        'sender_id': '987654321098765@s.whatsapp.net',
        'sender_name': 'TestAPI',
        'hora_min': timestamp,
        'caption': 'Test de API HTTP - Pago móvil provincial',
        'additional_data': json.dumps({
            'test_mode': True,
            'source': 'automated_test',
            'priority': 'normal'
        })
    }
    
    # Abrir imagen
    with open(test_image, 'rb') as img_file:
        files = {'image': ('test_api.png', img_file, 'image/png')}
        
        try:
            # Enviar imagen
            response = requests.post(
                f"{base_url}/api/ocr/process_image",
                data=form_data,
                files=files,
                timeout=10
            )
            
            if response.status_code == 202:
                result = response.json()
                request_id = result['request_id']
                print("✅ Imagen enviada exitosamente")
                print(f"   Request ID: {request_id}")
                print(f"   Endpoint de consulta: {result['check_result_endpoint']}")
                
                # Esperar y consultar resultado
                print("\n⏱️  Esperando procesamiento...")
                return request_id.replace('.png', '')
                
            else:
                print(f"❌ Error enviando imagen: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")

def check_api_result(request_id):
    """
    Test 3: Consultar resultado de API HTTP
    """
    if not request_id:
        return
        
    print(f"\n🔍 Test 3: Consultando resultado para {request_id}")
    
    base_url = "http://localhost:5000"
    max_attempts = 6
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/api/ocr/result/{request_id}", timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                if status == 'completed':
                    print("✅ Procesamiento completado")
                    ocr_result = result.get('result', {})
                    
                    # Mostrar información clave
                    print(f"   Status: {ocr_result.get('processing_status')}")
                    print(f"   Texto extraído: {len(ocr_result.get('full_raw_ocr_text', ''))} caracteres")
                    print(f"   Campos extraídos: {len(ocr_result.get('extracted_fields', []))}")
                    
                    # Mostrar campos extraídos
                    for field in ocr_result.get('extracted_fields', []):
                        field_name = field.get('field_name')
                        value = field.get('value')
                        confidence = field.get('confidence', 0)
                        print(f"   - {field_name}: {value} (confianza: {confidence:.2f})")
                    
                    return True
                    
                elif status == 'processing':
                    print(f"   Aún procesando... (intento {attempt + 1}/{max_attempts})")
                    time.sleep(5)
                    
                elif status == 'error':
                    print(f"❌ Error en procesamiento: {result.get('message')}")
                    return False
                    
            else:
                print(f"   Error consultando: {response.status_code}")
                time.sleep(5)
                
        except requests.exceptions.RequestException as e:
            print(f"   Error de conexión: {e}")
            time.sleep(5)
    
    print("⏰ Timeout esperando resultado")
    return False

def test_system_monitoring():
    """
    Test 4: Monitorear estado del sistema
    """
    print("\n📊 Test 4: Monitoreo del sistema")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/api/ocr/status", timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            print("✅ Estado del sistema:")
            print(f"   Status general: {status.get('status')}")
            
            queue_status = status.get('queue_status', {})
            print(f"   Cola inbox: {queue_status.get('inbox', 0)} imágenes")
            print(f"   Procesando: {queue_status.get('processing', 0)} imágenes")
            print(f"   Procesadas: {queue_status.get('processed', 0)} imágenes")
            print(f"   Errores: {queue_status.get('errors', 0)} imágenes")
            print(f"   Resultados: {queue_status.get('results_available', 0)} disponibles")
            
            system_info = status.get('system_info', {})
            print(f"   Worker: {'✅ Activo' if system_info.get('worker_running') else '❌ Inactivo'}")
            print(f"   OCR: {'✅ Cargado' if system_info.get('ocr_components_loaded') else '❌ No cargado'}")
            print(f"   Versión: {system_info.get('version', 'desconocida')}")
            
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

def main():
    """Ejecutar todos los tests del sistema asíncrono"""
    print("🚀 Testing Sistema OCR Asíncrono de Alto Volumen")
    print("=" * 60)
    
    # Test 1: Sistema de archivos
    test_file_system_approach()
    
    # Test 2: API HTTP
    request_id = test_http_api_approach()
    
    # Test 3: Consultar resultado (si se envió por API)
    if request_id:
        check_api_result(request_id)
    
    # Test 4: Monitoreo
    test_system_monitoring()
    
    print("\n" + "=" * 60)
    print("✅ Tests completados")
    print("\nPuedes verificar:")
    print("- Resultados en data/results/")
    print("- Imágenes procesadas en data/processed/")
    print("- Logs del sistema en la consola del servidor")
    print("- Estado en tiempo real: http://localhost:5000/api/ocr/status")

if __name__ == "__main__":
    main()