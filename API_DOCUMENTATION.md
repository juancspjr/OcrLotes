# API Documentation - Sistema OCR Empresarial

## Filosofía de Desarrollo
Este sistema sigue los principios de **Integridad Total** y **Perfección Continua**, garantizando que cada dato preserve su integridad desde la entrada hasta la salida final.

## Autenticación y Seguridad

### API Key
**Estado actual**: No requerida para endpoints públicos en desarrollo local
**Producción**: Se recomienda implementar autenticación para entornos productivos

```bash
# Ejemplo de uso futuro (no requerido actualmente)
curl -X POST "https://tu-dominio.com/api/ocr/upload" \
  -H "X-API-Key: tu-api-key-aqui"
```

## Flujo de Procesamiento Completo

### Resumen del Flujo
1. **Subida** → Cargar archivos con metadatos
2. **Procesamiento** → Ejecutar OCR del lote
3. **Monitoreo** → Verificar estado de procesamiento
4. **Descarga** → Obtener resultados estructurados

---

## 1. Subida de Archivos y Puesta en Cola

### `POST /api/ocr/upload`

**Descripción**: Sube archivos de imagen para procesamiento OCR, preservando metadatos y orden de subida.

**Content-Type**: `multipart/form-data`

**Parámetros**:
- `files`: Archivos de imagen (JPG, PNG, JPEG)
- `metadata`: JSON string con metadatos por archivo

**Estructura del metadata JSON**:
```json
{
  "nombre_archivo": "recibo_001.jpg",
  "id_whatsapp": "123456789",
  "idsorteo": "SORT001",
  "nombre_usuario": "Juan Pérez",
  "hora_minuto_subida": "14:30",
  "caption": "Pago Móvil BDV",
  "indice_de_subida": 1
}
```

**Ejemplo de request con curl**:
```bash
curl -X POST "http://localhost:5000/api/ocr/upload" \
  -F "files=@recibo_001.jpg" \
  -F "files=@recibo_002.jpg" \
  -F 'metadata=[
    {
      "nombre_archivo": "recibo_001.jpg",
      "id_whatsapp": "123456789",
      "nombre_usuario": "Juan Pérez",
      "hora_minuto_subida": "14:30",
      "caption": "Pago Móvil BDV",
      "indice_de_subida": 1
    },
    {
      "nombre_archivo": "recibo_002.jpg",
      "id_whatsapp": "987654321",
      "nombre_usuario": "María García",
      "hora_minuto_subida": "14:35",
      "caption": "Transferencia Bancaria",
      "indice_de_subida": 2
    }
  ]'
```

**Respuesta exitosa**:
```json
{
  "status": "success",
  "message": "Archivos subidos exitosamente",
  "batch_id": "BATCH_20250117_143000_abc123",
  "files_uploaded": 2,
  "timestamp": "2025-01-17T14:30:00Z"
}
```

**Respuesta de error**:
```json
{
  "status": "error",
  "message": "No se pudieron procesar los archivos",
  "error_code": "UPLOAD_FAILED",
  "details": "Formato de archivo no soportado"
}
```

---

## 2. Ejecución del Lote Acumulado

### `POST /api/ocr/process_batch`

**Descripción**: Ejecuta el procesamiento OCR de todos los archivos en cola del lote actual.

**Content-Type**: `application/json`

**Request Body**:
```json
{}
```

**Ejemplo de request**:
```bash
curl -X POST "http://localhost:5000/api/ocr/process_batch" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Respuesta exitosa**:
```json
{
  "status": "success",
  "message": "Procesamiento del lote iniciado",
  "batch_id": "BATCH_20250117_143000_abc123",
  "processing_status": "processing",
  "files_in_batch": 2,
  "estimated_time": "30-45 segundos"
}
```

**Respuesta de error**:
```json
{
  "status": "error",
  "message": "No hay archivos para procesar",
  "error_code": "NO_FILES_IN_QUEUE",
  "batch_id": null
}
```

---

## 3. Consulta de Estado del Lote

### `GET /api/ocr/batch_status/{batch_id}`

**Descripción**: Consulta el estado actual del procesamiento de un lote específico.

**Parámetros de URL**:
- `batch_id`: ID del lote a consultar

**Ejemplo de request**:
```bash
curl -X GET "http://localhost:5000/api/ocr/batch_status/BATCH_20250117_143000_abc123"
```

**Estados posibles**:
- `pending`: Lote creado, esperando procesamiento
- `processing`: OCR en ejecución
- `completed`: Procesamiento terminado exitosamente
- `failed`: Error durante el procesamiento
- `partial`: Algunos archivos procesados, otros fallaron

**Respuesta - Estado en procesamiento**:
```json
{
  "status": "processing",
  "batch_id": "BATCH_20250117_143000_abc123",
  "progress": {
    "processed": 1,
    "total": 2,
    "percentage": 50
  },
  "results_available": false,
  "estimated_remaining": "15-20 segundos"
}
```

**Respuesta - Estado completado**:
```json
{
  "status": "completed",
  "batch_id": "BATCH_20250117_143000_abc123",
  "progress": {
    "processed": 2,
    "total": 2,
    "percentage": 100
  },
  "results_available": true,
  "completion_time": "2025-01-17T14:31:45Z",
  "processing_stats": {
    "success_count": 2,
    "error_count": 0,
    "total_processing_time": "42.5s"
  }
}
```

---

## 4. Obtención de Resultados del Lote

### `GET /api/extract_results`

**Descripción**: Obtiene el JSON consolidado con todos los resultados del último lote procesado.

**Ejemplo de request**:
```bash
curl -X GET "http://localhost:5000/api/extract_results"
```

**Estructura de respuesta completa**:
```json
{
  "metadata": {
    "fecha_extraccion": "2025-01-17T14:31:45Z",
    "total_archivos": 2,
    "version_sistema": "1.0",
    "tipo_extraccion": "consolidado_empresarial"
  },
  "archivos_procesados": [
    {
      "nombre_archivo": "recibo_001.jpg",
      "id_whatsapp": "123456789",
      "nombre_usuario": "Juan Pérez",
      "caption": "Pago Móvil BDV",
      "hora_exacta": "14:30",
      "indice_de_subida": 1,
      "otro": "",
      "referencia": "002501174438",
      "bancoorigen": "BANCO DE VENEZUELA",
      "monto": "200.00",
      "datosbeneficiario": {
        "cedula": "26714848",
        "telefono": "04125318244",
        "banco_destino": "BANCO MERCANTIL"
      },
      "pago_fecha": "01/04/2025",
      "concepto": "Pago Móvil BDV",
      "texto_total_ocr": "Personas 200,00 Bs Fecha : 01/04/ 2025 Operacion : 002501174438...",
      "lote_id": "BATCH_20250117_143000_abc123",
      "lote_fecha": "2025-01-17 14:30:00",
      "extraction_stats": {
        "confidence": 0.938,
        "total_words": 20,
        "processing_time": 0.116
      }
    },
    {
      "nombre_archivo": "recibo_002.jpg",
      "id_whatsapp": "987654321",
      "nombre_usuario": "María García",
      "caption": "Transferencia Bancaria",
      "hora_exacta": "14:35",
      "indice_de_subida": 2,
      "otro": "",
      "referencia": "003162521173",
      "bancoorigen": "BANCO MERCANTIL",
      "monto": "150.50",
      "datosbeneficiario": {
        "cedula": "24609941",
        "telefono": "",
        "banco_destino": "BANCO DE VENEZUELA"
      },
      "pago_fecha": "02/04/2025",
      "concepto": "Transferencia interbancaria",
      "texto_total_ocr": "Transferencia 150,50 Bs Fecha : 02/04/ 2025 Operacion : 003162521173...",
      "lote_id": "BATCH_20250117_143000_abc123",
      "lote_fecha": "2025-01-17 14:30:00",
      "extraction_stats": {
        "confidence": 0.892,
        "total_words": 18,
        "processing_time": 0.134
      }
    }
  ]
}
```

---

## 5. Descarga de Resultados por Lote Específico

### `GET /api/batches/download/{batch_id}`

**Descripción**: Descarga resultados de un lote específico por su ID.

**Parámetros de URL**:
- `batch_id`: ID del lote específico

**Ejemplo de request**:
```bash
curl -X GET "http://localhost:5000/api/batches/download/BATCH_20250117_143000_abc123"
```

**Respuesta**: Estructura idéntica a `/api/extract_results` pero filtrada por el lote específico.

---

## Integración con n8n

### Flujo Recomendado para n8n

1. **Nodo HTTP Request** - Subir archivos
   - Método: POST
   - URL: `/api/ocr/upload`
   - Content-Type: multipart/form-data

2. **Nodo HTTP Request** - Iniciar procesamiento
   - Método: POST
   - URL: `/api/ocr/process_batch`
   - Content-Type: application/json

3. **Nodo Wait** - Esperar procesamiento (30-60 segundos)

4. **Nodo HTTP Request** - Verificar estado
   - Método: GET
   - URL: `/api/ocr/batch_status/{{batch_id}}`

5. **Nodo IF** - Verificar si `results_available: true`

6. **Nodo HTTP Request** - Obtener resultados
   - Método: GET
   - URL: `/api/extract_results`

### Ejemplo de Workflow n8n
```json
{
  "nodes": [
    {
      "name": "Upload Files",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:5000/api/ocr/upload",
        "sendBody": true,
        "contentType": "multipart-form-data"
      }
    },
    {
      "name": "Process Batch",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:5000/api/ocr/process_batch",
        "sendBody": true,
        "contentType": "json"
      }
    },
    {
      "name": "Wait for Processing",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "amount": 45,
        "unit": "seconds"
      }
    },
    {
      "name": "Get Results",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://localhost:5000/api/extract_results"
      }
    }
  ]
}
```

---

## Códigos de Error Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| `UPLOAD_FAILED` | Error al subir archivos | Verificar formato y tamaño |
| `NO_FILES_IN_QUEUE` | No hay archivos para procesar | Subir archivos primero |
| `BATCH_NOT_FOUND` | Lote no encontrado | Verificar batch_id |
| `PROCESSING_ERROR` | Error durante OCR | Revisar logs del servidor |
| `INVALID_METADATA` | Metadatos incorrectos | Verificar estructura JSON |

---

## Campos de Datos Extraídos

### Campos Principales
- **referencia**: Número de referencia/operación
- **bancoorigen**: Banco emisor del pago
- **monto**: Cantidad monetaria (normalizada a formato decimal)
- **datosbeneficiario**: Información del beneficiario
  - `cedula`: Número de identificación
  - `telefono`: Número de teléfono (formato venezolano)
  - `banco_destino`: Banco receptor
- **pago_fecha**: Fecha de la operación
- **concepto**: Motivo/concepto del pago

### Metadatos Preservados
- **caption**: Texto original del usuario
- **indice_de_subida**: Orden de subida original
- **id_whatsapp**: Identificador WhatsApp
- **nombre_usuario**: Usuario que subió el archivo

---

## Notas Técnicas

### Rendimiento
- **Tiempo promedio**: 15-30 segundos por lote de 2-5 archivos
- **Concurrencia**: Un lote a la vez por sistema
- **Formatos soportados**: JPG, PNG, JPEG

### Precisión OCR
- **Confianza promedio**: 90-95%
- **Campos especializados**: Optimizado para recibos bancarios venezolanos
- **Validación automática**: Teléfonos, cédulas, montos

Esta documentación garantiza la integración clara y funcional con n8n, preservando la integridad de los datos desde la entrada hasta la salida según los principios de la filosofía central del proyecto.