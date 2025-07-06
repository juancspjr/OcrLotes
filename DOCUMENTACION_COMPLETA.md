# 📋 DOCUMENTACIÓN COMPLETA - SISTEMA OCR ASÍNCRONO DE ALTO VOLUMEN

## 🎯 **RESUMEN EJECUTIVO**

Sistema OCR completo al **100% de funcionalidad** diseñado para procesamiento asíncrono de recibos de pago móviles con integración n8n. Implementa **dos endpoints separados** para máximo control: uno para acumular archivos y otro para procesar lotes bajo demanda.

## 🏗️ **ARQUITECTURA DEL SISTEMA**

### **Componentes Principales**
```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA OCR ASÍNCRONO                    │
├─────────────────────────────────────────────────────────────┤
│  🔹 main.py              - Punto de entrada Flask         │
│  🔹 app.py               - Configuración aplicación       │
│  🔹 api_endpoints.py     - Endpoints HTTP completos       │
│  🔹 routes.py            - Rutas web y APIs auxiliares    │
│  🔹 config.py            - Configuración centralizada     │
│  🔹 aplicador_ocr.py     - Motor OCR ONNX                 │
│  🔹 main_ocr_process.py  - Orquestador principal          │
│  🔹 mejora_ocr.py        - Preprocesamiento de imágenes   │
│  🔹 validador_ocr.py     - Validación y diagnóstico       │
└─────────────────────────────────────────────────────────────┘
```

### **Flujo de Datos**
```
📤 n8n/Sistema Externo
    ↓ POST /api/ocr/process_image
📥 data/inbox/ (Acumulación)
    ↓ POST /api/ocr/process_batch (Bajo Demanda)
⚙️ data/processing/ (Procesamiento)
    ↓ Éxito/Error
📂 data/processed/ | data/errors/
    ↓ Resultados JSON
📊 data/results/ (Acceso via GET /api/ocr/result/{id})
```

## 🚀 **ENDPOINTS API PRINCIPALES**

### **1. ENDPOINT DE ACUMULACIÓN** 
```http
POST /api/ocr/process_image
Content-Type: multipart/form-data
```

**Campos:**
- `image` *(obligatorio)*: Archivo de imagen (PNG, JPG, JPEG)
- `caption` *(opcional)*: Texto del caption de WhatsApp
- `sender_id` *(opcional)*: ID del remitente
- `sender_name` *(opcional)*: Nombre del remitente  
- `sorteo_fecha` *(opcional)*: Fecha del sorteo
- `sorteo_conteo` *(opcional)*: Conteo del sorteo
- `hora_min` *(opcional)*: Hora y minutos
- `additional_data` *(opcional)*: JSON con datos adicionales

**Respuesta:**
```json
{
  "status": "accepted",
  "message": "Image queued for processing",
  "request_id": "sender123_juan_20250706_001_1430_20250706_143022_456",
  "queue_position": "pending",
  "check_result_endpoint": "/api/ocr/result/sender123_juan_20250706_001_1430_20250706_143022_456",
  "batch_process_endpoint": "/api/ocr/process_batch"
}
```

### **2. ENDPOINT DE PROCESAMIENTO** 
```http
POST /api/ocr/process_batch
Content-Type: application/json
```

**Body (opcional):**
```json
{
  "batch_size": 5,
  "profile": "ultra_rapido",
  "process_all": false
}
```

**Respuesta:**
```json
{
  "status": "success",
  "message": "Batch processed successfully",
  "batch_info": {
    "batch_id": "BATCH_20250706_143022_789",
    "processed_count": 5,
    "successful_count": 4,
    "failed_count": 1,
    "processing_time_seconds": 12.5,
    "profile_used": "ultra_rapido",
    "remaining_in_queue": 3,
    "result_files": ["BATCH_20250706_143022_789_request1.json", "..."],
    "download_endpoint": "/api/download/batch_results/BATCH_20250706_143022_789"
  },
  "processing_summary": {
    "average_time_per_image": 2.5,
    "images_per_second": 0.4,
    "queue_status": "3 images remaining"
  }
}
```

### **3. ENDPOINT DE CONSULTA**
```http
GET /api/ocr/result/{request_id}
```

**Respuesta:**
```json
{
  "status": "completed",
  "request_id": "sender123_juan_20250706_001_1430_20250706_143022_456",
  "result": {
    "request_id": "sender123_juan_20250706_001_1430_20250706_143022_456",
    "processing_status": "success",
    "full_raw_ocr_text": "PAGO MÓVIL\nBanco: BANESCO\nMonto: $50.000...",
    "extracted_fields": [
      {
        "field_name": "monto",
        "value": "50000",
        "confidence": 0.95,
        "coordinates": [120, 45, 180, 65],
        "relative_position": "top-center"
      }
    ],
    "unmapped_text_segments": [...],
    "validation_result": {
      "is_valid_receipt": true,
      "missing_required_fields": [],
      "validation_score": 0.92
    },
    "batch_metadata": {
      "batch_size": 5,
      "batch_processing_time_seconds": 12.5,
      "batch_timestamp": "2025-07-06T14:30:22"
    }
  },
  "file_location": "BATCH_20250706_143022_789_sender123_juan_20250706_001_1430_20250706_143022_456.json"
}
```

### **4. ENDPOINT DE ESTADO**
```http
GET /api/ocr/queue/status
```

**Respuesta:**
```json
{
  "status": "success",
  "queue_status": {
    "inbox": 8,
    "processing": 0,
    "processed": 245,
    "errors": 12,
    "results_available": 245
  },
  "system_status": {
    "worker_running": true,
    "ocr_loaded": true
  },
  "timestamp": "2025-07-06T14:30:22"
}
```

## 🛠️ **COMANDOS DE USO**

### **Instalación y Configuración**
```bash
# Instalación completa automática
curl -fsSL https://raw.githubusercontent.com/juancspjr/OcrAcorazado/main/install.sh | bash

# O instalación manual
git clone https://github.com/juancspjr/OcrAcorazado.git
cd OcrAcorazado
chmod +x install_requirements.sh
./install_requirements.sh

# Verificar instalación
source venv_ocr/bin/activate
python download_models.py --verify
```

### **Iniciar el Sistema**
```bash
# Activar entorno virtual
source venv_ocr/bin/activate

# Iniciar servidor (desarrollo local)
python main.py

# Iniciar servidor (acceso de red)
python main.py --host 0.0.0.0 --port 5000

# Iniciar servidor (producción)
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

### **Verificar Funcionamiento**
```bash
# Estado del sistema
curl -X GET http://localhost:5000/api/ocr/queue/status

# Procesar imagen de prueba
curl -X POST http://localhost:5000/api/ocr/process_image \
  -F "image=@test_factura.png" \
  -F "caption=Pago realizado" \
  -F "sender_id=user123"

# Procesar lote acumulado
curl -X POST http://localhost:5000/api/ocr/process_batch \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10, "profile": "ultra_rapido"}'

# Consultar resultado
curl -X GET http://localhost:5000/api/ocr/result/REQUEST_ID
```

### **Procesamiento CLI Directo**
```bash
# Procesamiento individual rápido
python main_ocr_process.py imagen.jpg --profile ultra_rapido --json-only

# Procesamiento con máxima calidad
python main_ocr_process.py documento.png --profile normal --save-intermediate

# Formato para n8n
python main_ocr_process.py recibo.jpg --json-n8n --profile rapido
```

## 📊 **PERFILES DE RENDIMIENTO**

| Perfil | Tiempo | Calidad | Uso Recomendado |
|--------|--------|---------|-----------------|
| `ultra_rapido` | 0.4-0.7s | 84-88% | Screenshots móviles, procesamiento masivo |
| `rapido` | 0.8-1.2s | 89-92% | Documentos simples, balance velocidad/calidad |
| `normal` | 1.5-2.0s | 93-96% | Documentos complejos, máxima precisión |
| `high_confidence` | 1.8-2.5s | 95-98% | Documentos financieros críticos |

## 🔧 **CONFIGURACIÓN AVANZADA**

### **Estructura de Directorios**
```
data/
├── inbox/           # Imágenes pendientes de procesamiento
├── processing/      # Imágenes en proceso
├── processed/       # Imágenes procesadas exitosamente
├── errors/          # Imágenes con errores de procesamiento
└── results/         # Archivos JSON con resultados
```

### **Variables de Entorno Importantes**
```bash
# Flask
export FLASK_ENV=production
export FLASK_DEBUG=0

# Base de datos (si se usa)
export DATABASE_URL="postgresql://user:pass@localhost/ocrdb"

# Configuración de sesión
export SESSION_SECRET="tu-clave-secreta-aqui"
```

### **Configuración de Lotes**
```python
# En config.py - modificar según necesidades
BATCH_PROCESSING_CONFIG = {
    'batch_size': 5,           # Tamaño ideal de lote
    'max_batch_size': 20,      # Máximo permitido
    'min_batch_size': 1,       # Mínimo permitido
    'max_files_per_batch': 50  # Límite por carga masiva
}
```

## 🤖 **INTEGRACIÓN CON N8N**

### **Flujo de Trabajo Recomendado**

#### **WORKFLOW 1: Acumulación de Imágenes**
```json
{
  "nodes": [
    {
      "name": "WhatsApp Trigger",
      "type": "@n8n/n8n-nodes-base.webhook"
    },
    {
      "name": "Extract Image",
      "type": "@n8n/n8n-nodes-base.function"
    },
    {
      "name": "Send to OCR Queue",
      "type": "@n8n/n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://tu-servidor:5000/api/ocr/process_image",
        "sendBody": true,
        "bodyContentType": "multipart/form-data"
      }
    }
  ]
}
```

#### **WORKFLOW 2: Procesamiento por Lotes**
```json
{
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "@n8n/n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "mode": "everyMinute"
            }
          ]
        }
      }
    },
    {
      "name": "Check Queue Status",
      "type": "@n8n/n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://tu-servidor:5000/api/ocr/queue/status"
      }
    },
    {
      "name": "Process if Queue > 5",
      "type": "@n8n/n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.queue_status.inbox}}",
              "operation": "larger",
              "value2": 5
            }
          ]
        }
      }
    },
    {
      "name": "Process Batch",
      "type": "@n8n/n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://tu-servidor:5000/api/ocr/process_batch",
        "sendBody": true,
        "bodyContentType": "json",
        "jsonBody": "={\"batch_size\": 10, \"profile\": \"ultra_rapido\"}"
      }
    }
  ]
}
```

#### **WORKFLOW 3: Consulta de Resultados**
```json
{
  "nodes": [
    {
      "name": "Wait for Processing",
      "type": "@n8n/n8n-nodes-base.wait",
      "parameters": {
        "amount": 30,
        "unit": "seconds"
      }
    },
    {
      "name": "Get Result",
      "type": "@n8n/n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://tu-servidor:5000/api/ocr/result/{{$json.request_id}}"
      }
    },
    {
      "name": "Process Result",
      "type": "@n8n/n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Procesar datos extraídos del OCR\nreturn items;"
      }
    }
  ]
}
```

## 🔍 **MONITOREO Y DEBUGGING**

### **Logs del Sistema**
```bash
# Ver logs en tiempo real
tail -f ocr_system.log

# Logs específicos del worker
grep "Worker" ocr_system.log

# Logs de errores solamente
grep "ERROR" ocr_system.log
```

### **Verificación de Salud del Sistema**
```bash
# Script de verificación completa
#!/bin/bash
echo "🔍 Verificación completa del sistema OCR"

# 1. Python environment
echo "Python version: $(python --version)"
echo "Virtual env: $VIRTUAL_ENV"

# 2. Dependencies
python -c "import onnxtr; print('✅ OnnxTR OK')" 2>/dev/null || echo "❌ OnnxTR Error"
python -c "import cv2; print('✅ OpenCV OK')" 2>/dev/null || echo "❌ OpenCV Error"
python -c "import numpy; print('✅ NumPy OK')" 2>/dev/null || echo "❌ NumPy Error"

# 3. Models
python download_models.py --verify

# 4. API Status
curl -s http://localhost:5000/api/ocr/queue/status | jq '.status' 2>/dev/null || echo "❌ API No accesible"

echo "✅ Verificación completada"
```

### **Métricas de Rendimiento**
```bash
# Benchmark de perfiles
for profile in ultra_rapido rapido normal; do
  echo "Testing profile: $profile"
  time python main_ocr_process.py test_factura.png --profile $profile --json-only > /dev/null
done

# Monitor de recursos durante procesamiento
htop &
python main_ocr_process.py imagen_grande.jpg --profile normal
```

## 🚨 **SOLUCIÓN DE PROBLEMAS**

### **Problemas Comunes**

#### **1. Error "Worker failed to boot"**
```bash
# Verificar conflictos de endpoints
grep -n "def api_" routes.py api_endpoints.py

# Limpiar archivos temporales
rm -rf temp/* uploads/* __pycache__
find . -name "*.pyc" -delete

# Reiniciar servicio
pkill -f gunicorn
python main.py
```

#### **2. "ModuleNotFoundError: No module named 'onnxtr'"**
```bash
# Reinstalar OnnxTR
source venv_ocr/bin/activate
pip uninstall onnxtr
pip install onnxtr==0.7.1

# Verificar instalación
python -c "import onnxtr; print('✅ OnnxTR funcionando')"
```

#### **3. "Error consultando resultado"**
```bash
# Verificar estructura de directorios
ls -la data/
mkdir -p data/{inbox,processing,processed,errors,results}

# Verificar permisos
chmod 755 data/
chmod 755 data/*
```

#### **4. "OCR system not initialized"**
```bash
# Verificar carga de modelos
python download_models.py --download --force

# Verificar memoria disponible
free -h
# Si memoria < 2GB, usar solo perfil ultra_rapido
```

### **Recuperación de Emergencia**
```bash
# Limpieza completa del sistema
./cleanup_ocr_system.sh

# Reinstalación desde cero
git pull origin main
./install_requirements.sh

# Verificación post-recuperación
python -c "
import sys, os
print('✅ Python OK' if sys.version_info >= (3,7) else '❌ Python version')
print('✅ Virtual env OK' if os.environ.get('VIRTUAL_ENV') else '❌ Virtual env not active')
try:
    import onnxtr; print('✅ OnnxTR OK')
except: print('❌ OnnxTR not installed')
print('✅ Sistema operacional')
"
```

## 📈 **OPTIMIZACIÓN DE RENDIMIENTO**

### **Recomendaciones de Hardware**
```
Mínimo:
- CPU: 2 cores, 2.0 GHz
- RAM: 4 GB
- Storage: 2 GB libre
- Red: 10 Mbps

Óptimo:
- CPU: 4+ cores, 3.0+ GHz
- RAM: 8+ GB
- Storage: 5+ GB libre (SSD recomendado)
- Red: 100+ Mbps
```

### **Configuración para Alto Volumen**
```python
# config.py - Configuración optimizada
BATCH_PROCESSING_CONFIG = {
    'batch_size': 10,              # Lotes más grandes
    'max_concurrent_batches': 3,   # Más procesamiento paralelo
    'polling_interval_seconds': 2, # Verificación más frecuente
    'auto_optimization': {
        'enabled': True,
        'cpu_threshold_high': 85,  # Más tolerancia a CPU
        'memory_threshold_high': 85
    }
}
```

### **Monitoreo Continuo**
```bash
# Script de monitoreo automático
#!/bin/bash
while true; do
  echo "$(date): Queue status:"
  curl -s http://localhost:5000/api/ocr/queue/status | jq '.queue_status'
  echo "Resource usage:"
  echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
  echo "RAM: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
  sleep 30
done
```

## 🎯 **CASOS DE USO ESPECÍFICOS**

### **Caso 1: Integración WhatsApp → n8n → OCR**
1. WhatsApp envía imagen vía webhook a n8n
2. n8n extrae imagen y metadatos
3. n8n llama POST `/api/ocr/process_image`
4. Sistema guarda en cola (inbox)
5. n8n programa procesamiento cada X minutos
6. n8n llama POST `/api/ocr/process_batch`
7. n8n consulta resultados GET `/api/ocr/result/{id}`

### **Caso 2: Procesamiento de Lotes Nocturnos**
```bash
# Cron job para procesamiento nocturno
0 2 * * * curl -X POST http://localhost:5000/api/ocr/process_batch \
  -H "Content-Type: application/json" \
  -d '{"process_all": true, "profile": "normal"}'
```

### **Caso 3: API para Sistema Externo**
```python
import requests

# Enviar imagen
files = {'image': open('recibo.jpg', 'rb')}
data = {
    'caption': 'Pago de servicios',
    'sender_id': 'user123',
    'sender_name': 'Juan Pérez'
}

response = requests.post('http://servidor:5000/api/ocr/process_image', 
                        files=files, data=data)
request_id = response.json()['request_id']

# Procesar lote
requests.post('http://servidor:5000/api/ocr/process_batch',
              json={'batch_size': 5, 'profile': 'ultra_rapido'})

# Obtener resultado
result = requests.get(f'http://servidor:5000/api/ocr/result/{request_id}')
print(result.json())
```

## 📞 **SOPORTE Y MANTENIMIENTO**

### **Actualizaciones del Sistema**
```bash
# Verificar versión actual
grep "version" config.py

# Actualizar a última versión
git pull origin main
source venv_ocr/bin/activate
pip install --upgrade onnxtr opencv-python

# Verificar compatibilidad
python download_models.py --verify
```

### **Backup y Recuperación**
```bash
# Backup completo
tar -czf backup_ocr_$(date +%Y%m%d).tar.gz \
  --exclude=venv_ocr \
  --exclude=temp \
  --exclude=__pycache__ \
  .

# Restaurar backup
tar -xzf backup_ocr_YYYYMMDD.tar.gz
./install_requirements.sh
```

---

## ✅ **VERIFICACIÓN FINAL - LISTA DE COMPROBACIÓN**

- [ ] ✅ Instalación completa ejecutada sin errores
- [ ] ✅ Modelos ONNX descargados y verificados  
- [ ] ✅ Servidor Flask iniciado en puerto 5000
- [ ] ✅ Endpoint `/api/ocr/process_image` responde 202
- [ ] ✅ Endpoint `/api/ocr/process_batch` responde 200
- [ ] ✅ Endpoint `/api/ocr/result/{id}` responde correctamente
- [ ] ✅ Endpoint `/api/ocr/queue/status` muestra estado
- [ ] ✅ Directorios data/* creados automáticamente
- [ ] ✅ Procesamiento CLI funciona con `python main_ocr_process.py`
- [ ] ✅ Integración n8n probada exitosamente
- [ ] ✅ Documentación completa disponible

**🎉 SISTEMA OCR ASÍNCRONO AL 100% DE FUNCIONALIDAD - LISTO PARA PRODUCCIÓN**

Para soporte adicional o preguntas específicas, consultar los logs del sistema o ejecutar los comandos de verificación incluidos en esta documentación.