# REPORTE DE ANÁLISIS DE FLUJO DE DATOS DETALLADO (DFD) / DIAGRAMA DE SECUENCIA DE PROCESOS

**Fecha:** 15 de Julio de 2025  
**Versión:** 1.0 (Especificación Operativa Blindada)  
**Objetivo:** Definir la especificación operativa inquebrantable del flujo ideal y corregido del "Sistema OCR Asíncrono Empresarial" para implementación paso a paso  

---

## 1. PRINCIPIOS FUNDAMENTALES DEL FLUJO DE DATOS

### 1.1 Propósito Principal (Comprensión Profunda del Contexto de Dominio)

**Secuencia Operativa Central:**
> "Entre las imágenes con su JSON de entrada para que cada una esté identificada → acumular hasta esperar el mandato de procesamiento de ese lote → si solicitan el estado del lote enviarlo → si el estado procesado y solicitaron respuestas enviar los resultados finales → puede esperando que le pidan la data para liberar → pero puede procesar otro lote sin problema y acumular hasta que envíe la información y liberar el lote con envío de información de errores si los hay"

### 1.2 Filosofía de Diseño Aplicada

- **Integridad Total:** Cada paso debe ser verificable y trazable
- **Perfección Continua:** Manejo robusto de errores y reintentos
- **Zero-Fault Detection:** Detección proactiva de fallos en cada etapa
- **Persistencia de Correcciones:** Recuperación automática de fallos temporales
- **Interface Excellence:** Comunicación clara entre componentes

### 1.3 Arquitectura de Componentes Objetivo

- **CO-01:** API Gateway / Backend Service (Orquestación)
- **CO-04:** OCR Worker Service (Procesamiento Asíncrono)
- **CO-05:** Frontend Dashboard Service (Interfaz Usuario)
- **CO-06:** Servicio de Almacenamiento (Persistencia)
- **AE-01:** Usuario Final (Operador/Administrador)
- **AE-02:** Sistema n8n (Integración Externa)
- **AE-03:** Base de Datos Externa (Persistencia Final)

---

## 2. ESPECIFICACIÓN OPERATIVA DEL FLUJO DE DATOS

### 2.1 Flujo Principal: Ingestión Asíncrona de Documentos por Lote

| **Paso** | **Actor/Componente Origen** | **Evento/Acción** | **Actor/Componente Destino** | **Datos/Mensaje Enviado** | **Condiciones/Notas (Manejo de Errores, NFRs)** |
|----------|----------------------------|-------------------|------------------------------|---------------------------|--------------------------------------------------|
| **1** | Usuario Final (AE-01) | Carga de Documento Individual con Metadatos | API Gateway (CO-01) | `multipart/form-data` (archivo + JSON `metadatos_entrada`) | **HU-ING-001.** Validación estricta: Content-Type (`image/jpeg`, `image/png`, `application/pdf`), tamaño máximo 10MB. Genera `idDocumento` (UUID) y `idLote` (UUID si nuevo). **Errores:** 400 Bad Request (validación), 413 Payload Too Large (tamaño), 500 Internal Server Error (almacenamiento). **NFR-PERF-001:** Respuesta < 200ms. |
| **2** | API Gateway (CO-01) | Almacenamiento Temporal de Documento | Servicio de Almacenamiento (CO-06) | `archivo_binario`, `idDocumento`, `metadata_entrada`, `contenido_hash` | Almacenamiento en sistema de alta disponibilidad (S3/MinIO). Genera `URL_documento_almacenado` y `hash_verificacion`. **Reintentos:** 3 intentos con backoff exponencial (1s, 2s, 4s). **NFR-REND-001:** Latencia < 100ms. **Manejo de errores:** Timeout 30s, retry automático, fallback a almacenamiento local temporal. |
| **3** | API Gateway (CO-01) | Creación/Actualización de Lote EN_MEMORIA | API Gateway (CO-01) (Caché Interno) | `idLote`, `idDocumento`, `URL_documento_almacenado`, `estadoDocumento` (`RECIBIDO`), `metadata_entrada`, `timestamp_ingreso` | Mantiene `mapa_lotes_memoria` con estructura: `{idLote: {estado: 'RECIBIENDO_DOCUMENTOS', documentos: [...], total_documentos: N, timestamp_creacion: datetime}}`. **Persistencia:** Solo en memoria volátil para rendimiento. **NFR-PERF-002:** Operación < 50ms. **Lógica:** Si `idLote` existe, añade documento; si no existe, crea nuevo lote. |
| **4** | API Gateway (CO-01) | Respuesta de Confirmación de Carga | Usuario Final (AE-01) | `JSON_confirmacion_carga`: `{idDocumento, idLote, estado_documento, mensaje_confirmacion}` | **Interface Excellence:** Respuesta inmediata confirmando recepción. **Estructura:** `{idDocumento: "uuid", idLote: "uuid", estadoDocumento: "RECIBIDO", mensaje: "Documento recibido y añadido a lote"}`. **HTTP Status:** 202 Accepted. **Headers:** `Location: /api/lotes/{idLote}/status`. |
| **5** | Usuario Final (AE-01) | Solicitud de Procesamiento de Lote | API Gateway (CO-01) | `idLote`, `parametros_procesamiento` (opcional) | **HU-LOT-003.** Trigger del procesamiento asíncrono. **Validaciones:** Lote existe, estado = 'RECIBIENDO_DOCUMENTOS', mínimo 1 documento. **Respuesta:** 202 Accepted con `processing_request_id`. **Errores:** 404 Not Found (lote no existe), 409 Conflict (ya procesando), 400 Bad Request (lote vacío). **Estado:** Actualiza a 'EN_ESPERA_PROCESAMIENTO'. |
| **6** | API Gateway (CO-01) | Encolamiento de Lote para Procesamiento | Cola de Mensajes (Kafka/RabbitMQ) | `mensaje_lote`: `{idLote, lista_urls_documentos, metadata_lote_consolidada, prioridad, timestamp_encolamiento}` | **NFR-ESCA-001:** Escalabilidad horizontal. **Persistencia:** Mensaje persistente en cola con TTL 24h. **Estructura:** `{idLote: "uuid", urls_documentos: [...], metadata_lote: {...}, prioridad: 5, callback_url: "http://co-01/api/internal/ocr_results/callback"}`. **Reintentos:** DLQ (Dead Letter Queue) después de 3 fallos. **Particionado:** Por `idLote` para procesamiento ordenado. |
| **7** | OCR Worker Service (CO-04) | Consumo de Mensaje de Lote | Cola de Mensajes (Kafka/RabbitMQ) | `mensaje_lote` (consumido) | **NFR-ESCA-001:** Múltiples workers concurrentes. **Patrón:** Consumer Group para balanceo de carga. **Acknowledgment:** Manual después de procesamiento exitoso. **Timeout:** 30 minutos por lote. **Heartbeat:** Cada 5 minutos para mantener lease. **Reintentos:** 3 intentos automáticos, después envía a DLQ. |
| **8** | OCR Worker Service (CO-04) | Descarga de Documento Individual | Servicio de Almacenamiento (CO-06) | `URL_documento`, `idDocumento`, `hash_verificacion` | **Por cada documento en el lote.** **Verificación:** Comparación de hash para integridad. **Timeout:** 60s por descarga. **Reintentos:** 3 intentos con backoff. **Errores:** Log detallado, marca documento como 'ERROR_DESCARGA'. **NFR-RESI-001:** Resiliencia ante fallos de red. **Compresión:** Soporte para documentos comprimidos. |
| **9** | OCR Worker Service (CO-04) | Procesamiento OCR Individual | OCR Worker Service (CO-04) (Motor OnnxTR + Spatial Processor) | `archivo_binario`, `metadata_entrada`, `parametros_ocr` | **Por cada documento.** **Motor:** OnnxTR con modelos pre-cargados. **Procesamiento:** Extracción de texto + coordenadas, aplicación de reglas configurables, validación de resultados. **Timeout:** 30s por documento. **NFR-PERF-001:** Promedio 5s, máximo 8s (95%). **Errores:** 'EXITO', 'FALLO_OCR', 'TIMEOUT'. **Métricas:** CPU, memoria, tiempo de procesamiento. |
| **10** | OCR Worker Service (CO-04) | Almacenamiento de Resultado Individual | Servicio de Almacenamiento (CO-06) | `JSON_resultado_OCR`: `{idLote, idDocumento, estado_procesamiento, resultado_ocr, metadata_procesamiento, timestamp_procesamiento}` | **Por cada documento procesado.** **Persistencia:** Almacenamiento duradero del resultado. **Estructura:** `{texto_extraido, coordenadas_palabras, campos_extraidos, confianza_promedio, errores_detectados}`. **Atomicidad:** Transacción completa o rollback. **Backup:** Copia de seguridad automática. **TTL:** 30 días de retención. |
| **11** | OCR Worker Service (CO-04) | Notificación de Documento Procesado | API Gateway (CO-01) | `callback_resultado`: `{idLote, idDocumento, estado_procesamiento, url_resultado_ocr, resumen_errores, timestamp_finalizacion}` | **Webhook asíncrono** a `/api/internal/ocr_results/callback`. **Estructura:** `{idLote: "uuid", idDocumento: "uuid", estado: "EXITO|FALLO_OCR", url_resultado: "https://...", detalles_error: "...", tiempo_procesamiento: 5.2}`. **Reintentos:** 5 intentos con backoff exponencial. **Timeout:** 10s por callback. **NFR-RESI-001:** Manejo de fallos de callback. |
| **12** | API Gateway (CO-01) | Actualización de Estado de Lote | API Gateway (CO-01) (Caché Interno) | `idLote`, `resultado_documento`, `contadores_actualizados` | **Lógica:** Actualiza `estadoDocumento` en `mapa_lotes_memoria`. **Contadores:** Incrementa `documentos_procesados` o `documentos_fallidos`. **Verificación:** Si `(documentos_procesados + documentos_fallidos) == total_documentos`, actualiza `estadoLote` a `COMPLETADO_EXITO` o `COMPLETADO_PARCIAL_FALLO`. **Atomicidad:** Operación atómica con locks. **Logging:** Registro detallado de cambios de estado. |
| **13** | Usuario Final (AE-01) | Consulta de Estado de Lote | API Gateway (CO-01) | `idLote` | **HU-LOT-002.** Endpoint: `GET /api/lotes/{idLote}/status`. **Respuesta:** `{estadoLote, totalDocumentos, documentosProcesados, documentosConError, progresoPorcentaje, tiempoEstimadoFinalizacion, detallesDocumentos}`. **Caching:** Redis con TTL 30s. **Errores:** 404 Not Found (lote no existe). **Polling:** Recomendado cada 5s. |
| **14** | Usuario Final (AE-01) | Solicitud de Resultados de Lote | API Gateway (CO-01) | `idLote`, `formato_respuesta` (JSON/CSV/ZIP) | **HU-LOT-004.** **Condición:** Solo si `estadoLote` in ['COMPLETADO_EXITO', 'COMPLETADO_PARCIAL_FALLO']. **Errores:** 409 Conflict (no completado), 404 Not Found (lote no existe). **Formato:** JSON consolidado por defecto. **Timeout:** 60s para consolidación. **Caché:** Resultado cacheado 24h. |
| **15** | API Gateway (CO-01) | Consolidación y Entrega de Resultados | Servicio de Almacenamiento (CO-06) | `idLote`, `formato_consolidacion` | **Agregación:** Recopila todos los `JSON_resultado_OCR` del lote. **Estructura:** `{idLote, estado_final, total_documentos, documentos_exitosos, documentos_fallidos, resultados_consolidados[], errores_detallados[], metadata_consolidacion}`. **Formato:** JSON, CSV o ZIP según solicitud. **Compresión:** Automática para lotes > 100 documentos. **Integridad:** Verificación de completitud. |
| **16** | API Gateway (CO-01) | Notificación a n8n de Lote Completado | Sistema n8n (AE-02) | `webhook_n8n`: `{idLote, estado_final_lote, url_resultados_consolidados, resumen_estadisticas, timestamp_completacion}` | **HU-INT-001.** **Endpoint:** `POST /api/n8n/webhook/ocr_results`. **Condición:** Solo después de `estadoLote` completado. **Estructura:** `{idLote: "uuid", estado: "COMPLETADO_EXITO|COMPLETADO_PARCIAL_FALLO", url_resultados: "https://...", documentos_procesados: N, documentos_errores: M, tiempo_total_procesamiento: "5m30s"}`. **Reintentos:** 10 intentos con backoff exponencial. **Timeout:** 30s. **NFR-RESI-001:** Persistencia de notificación. |
| **17** | API Gateway (CO-01) | Liberación de Recursos de Lote | API Gateway (CO-01) (Caché Interno) | `idLote`, `confirmacion_liberacion` | **Condición:** Después de notificación exitosa a n8n OR solicitud exitosa de resultados por usuario. **Operación:** Elimina `idLote` del `mapa_lotes_memoria`. **Limpieza:** Archivos temporales, caché asociado. **Logging:** Registro de liberación con timestamp. **Optimización:** Permite procesamiento de nuevos lotes sin interferencia. **NFR-PERF-003:** Liberación < 100ms. |

---

## 3. ESTADOS DE LOTE Y TRANSICIONES

### 3.1 Estados Posibles de Lote

| **Estado** | **Descripción** | **Transición Desde** | **Transición Hacia** | **Condición** |
|------------|-----------------|---------------------|---------------------|---------------|
| `RECIBIENDO_DOCUMENTOS` | Lote acepta nuevos documentos | `INICIAL` | `EN_ESPERA_PROCESAMIENTO` | Usuario solicita procesamiento |
| `EN_ESPERA_PROCESAMIENTO` | Lote encolado para procesamiento | `RECIBIENDO_DOCUMENTOS` | `EN_PROCESAMIENTO` | Worker consume mensaje |
| `EN_PROCESAMIENTO` | Documentos siendo procesados | `EN_ESPERA_PROCESAMIENTO` | `COMPLETADO_EXITO` / `COMPLETADO_PARCIAL_FALLO` | Todos los documentos procesados |
| `COMPLETADO_EXITO` | Todos los documentos procesados exitosamente | `EN_PROCESAMIENTO` | `LIBERADO` | Notificación a n8n exitosa |
| `COMPLETADO_PARCIAL_FALLO` | Algunos documentos fallaron | `EN_PROCESAMIENTO` | `LIBERADO` | Notificación a n8n exitosa |
| `LIBERADO` | Recursos liberados | `COMPLETADO_EXITO` / `COMPLETADO_PARCIAL_FALLO` | N/A | Estado final |

### 3.2 Estados Posibles de Documento

| **Estado** | **Descripción** | **Transición Desde** | **Transición Hacia** | **Condición** |
|------------|-----------------|---------------------|---------------------|---------------|
| `RECIBIDO` | Documento cargado y almacenado | `INICIAL` | `EN_PROCESAMIENTO` | Worker inicia procesamiento |
| `EN_PROCESAMIENTO` | Documento siendo procesado por OCR | `RECIBIDO` | `PROCESADO_EXITO` / `PROCESADO_FALLO` | OCR completa |
| `PROCESADO_EXITO` | OCR exitoso | `EN_PROCESAMIENTO` | N/A | Estado final exitoso |
| `PROCESADO_FALLO` | OCR falló | `EN_PROCESAMIENTO` | N/A | Estado final con error |
| `ERROR_DESCARGA` | Fallo en descarga | `RECIBIDO` | N/A | Estado final con error |
| `ERROR_TIMEOUT` | Timeout en procesamiento | `EN_PROCESAMIENTO` | N/A | Estado final con error |

---

## 4. ESTRUCTURA DE DATOS OPERACIONAL

### 4.1 Estructura del Lote en Memoria (CO-01)

```json
{
  "idLote": "uuid-v4",
  "estadoLote": "RECIBIENDO_DOCUMENTOS|EN_ESPERA_PROCESAMIENTO|EN_PROCESAMIENTO|COMPLETADO_EXITO|COMPLETADO_PARCIAL_FALLO",
  "timestamp_creacion": "2025-07-15T10:00:00Z",
  "timestamp_ultimo_documento": "2025-07-15T10:05:00Z",
  "total_documentos": 5,
  "documentos_procesados": 3,
  "documentos_fallidos": 1,
  "progreso_porcentaje": 80,
  "tiempo_estimado_finalizacion": "2025-07-15T10:15:00Z",
  "documentos": [
    {
      "idDocumento": "uuid-v4",
      "nombre_archivo": "recibo_001.jpg",
      "url_almacenamiento": "https://storage.co-06/documents/uuid",
      "estadoDocumento": "PROCESADO_EXITO",
      "metadata_entrada": {...},
      "timestamp_ingreso": "2025-07-15T10:01:00Z",
      "timestamp_procesamiento": "2025-07-15T10:03:00Z",
      "tiempo_procesamiento_segundos": 4.2,
      "url_resultado": "https://storage.co-06/results/uuid.json",
      "errores": []
    }
  ],
  "metadata_lote": {
    "usuario_origen": "operador_001",
    "parametros_procesamiento": {...},
    "prioridad": 5,
    "callback_url": "https://co-01/api/internal/ocr_results/callback"
  }
}
```

### 4.2 Estructura del Resultado OCR (CO-04)

```json
{
  "idDocumento": "uuid-v4",
  "idLote": "uuid-v4",
  "estado_procesamiento": "EXITO|FALLO_OCR|ERROR_DESCARGA|ERROR_TIMEOUT",
  "timestamp_procesamiento": "2025-07-15T10:03:00Z",
  "tiempo_procesamiento_segundos": 4.2,
  "resultado_ocr": {
    "texto_completo": "Texto extraído completo...",
    "confianza_promedio": 0.95,
    "palabras_detectadas": [
      {
        "texto": "BANCO",
        "coordenadas": {
          "x": 100,
          "y": 50,
          "width": 80,
          "height": 20
        },
        "confianza": 0.98
      }
    ],
    "campos_extraidos": {
      "monto": "1250.00",
      "banco_origen": "BANCO MERCANTIL",
      "referencia": "123456789",
      "fecha_operacion": "2025-07-15",
      "telefono": "04121234567",
      "cedula": "V12345678"
    }
  },
  "metadata_procesamiento": {
    "motor_ocr": "OnnxTR",
    "version_modelo": "v2.1",
    "servidor_procesamiento": "worker-node-01",
    "parametros_utilizados": {...},
    "metricas_rendimiento": {
      "tiempo_descarga_ms": 250,
      "tiempo_ocr_ms": 3800,
      "tiempo_validacion_ms": 150,
      "memoria_utilizada_mb": 512,
      "cpu_utilizada_porcentaje": 45
    }
  },
  "errores": [
    {
      "codigo": "WARN_BAJA_CONFIANZA",
      "mensaje": "Confianza baja en campo 'referencia': 0.75",
      "campo_afectado": "referencia",
      "severidad": "WARNING"
    }
  ]
}
```

### 4.3 Estructura del Mensaje de Cola (Kafka/RabbitMQ)

```json
{
  "message_id": "uuid-v4",
  "timestamp": "2025-07-15T10:05:00Z",
  "topic": "ocr_lotes_pendientes",
  "partition_key": "lote_uuid",
  "headers": {
    "version": "1.0",
    "content_type": "application/json",
    "priority": "5",
    "ttl": "86400"
  },
  "payload": {
    "idLote": "uuid-v4",
    "total_documentos": 5,
    "urls_documentos": [
      "https://storage.co-06/documents/doc1_uuid",
      "https://storage.co-06/documents/doc2_uuid"
    ],
    "metadata_lote": {
      "usuario_origen": "operador_001",
      "parametros_procesamiento": {
        "perfil_rendimiento": "balanced",
        "reglas_extraccion": "recibos_venezolanos",
        "validacion_estricta": true
      },
      "prioridad": 5,
      "callback_url": "https://co-01/api/internal/ocr_results/callback"
    },
    "documentos": [
      {
        "idDocumento": "uuid-v4",
        "nombre_archivo": "recibo_001.jpg",
        "url_almacenamiento": "https://storage.co-06/documents/uuid",
        "hash_verificacion": "sha256_hash",
        "metadata_entrada": {
          "numerosorteo": "20250715",
          "fechasorteo": "2025-07-15",
          "idWhatsapp": "@lid_operador_10-00",
          "nombre": "Operador",
          "caption": "Recibo de pago móvil"
        }
      }
    ]
  }
}
```

---

## 5. MANEJO DE ERRORES Y RESILIENCIA

### 5.1 Categorías de Errores

#### 5.1.1 Errores de Validación (400 Bad Request)
- **Archivo inválido:** Formato no soportado, tamaño excesivo, archivo corrupto
- **Metadatos incompletos:** Campos requeridos faltantes, formato incorrecto
- **Lote inválido:** Lote no existe, estado incompatible con operación

#### 5.1.2 Errores de Procesamiento (500 Internal Server Error)
- **Fallo de almacenamiento:** CO-06 no disponible, espacio insuficiente
- **Fallo de OCR:** Modelo no disponible, imagen ilegible, timeout
- **Fallo de cola:** Kafka/RabbitMQ no disponible, mensaje corrupto

#### 5.1.3 Errores de Integración (502 Bad Gateway)
- **Webhook n8n fallo:** Endpoint no disponible, timeout, respuesta inválida
- **Callback fallo:** CO-01 no disponible, respuesta inválida

### 5.2 Estrategias de Recuperación

#### 5.2.1 Reintentos con Backoff Exponencial
```
Intento 1: Inmediato
Intento 2: 1 segundo
Intento 3: 2 segundos
Intento 4: 4 segundos
Intento 5: 8 segundos
Después: Dead Letter Queue
```

#### 5.2.2 Degradación Elegante
- **CO-06 indisponible:** Almacenamiento temporal local
- **OCR fallo:** Marcado como error, continúa con otros documentos
- **n8n indisponible:** Almacenamiento de notificaciones para reintento posterior

#### 5.2.3 Monitoreo y Alertas
- **Métricas:** Latencia, throughput, tasa de errores
- **Alertas:** Fallos consecutivos, tiempos de respuesta excesivos
- **Logs:** Trazabilidad completa con correlation IDs

---

## 6. REQUISITOS NO FUNCIONALES APLICADOS

### 6.1 Rendimiento (Performance)

#### 6.1.1 Latencia
- **API Gateway (CO-01):** < 200ms para ingestión (NFR-PERF-001)
- **OCR Worker (CO-04):** 5s promedio, 8s máximo 95% (NFR-PERF-002)
- **Callbacks:** < 50ms latencia de red (NFR-PERF-003)
- **Notificación n8n:** < 1s desde completación (NFR-PERF-004)

#### 6.1.2 Throughput
- **Ingestión:** 50 solicitudes/segundo concurrentes
- **Procesamiento:** 20 documentos/minuto por worker
- **Consolidación:** 1000 documentos/minuto

### 6.2 Escalabilidad

#### 6.2.1 Escalabilidad Horizontal
- **CO-01:** Escalabilidad 50% sin degradación (NFR-ESCAL-002)
- **CO-04:** Escalabilidad 100% en 2 horas (NFR-ESCAL-001)
- **Cola:** Particionado por lote para balanceo

#### 6.2.2 Recursos
- **Memoria:** 512MB por worker OCR
- **CPU:** 2 cores por worker recomendado
- **Almacenamiento:** 100GB por 10,000 documentos

### 6.3 Disponibilidad

#### 6.3.1 Uptime
- **CO-01 y CO-06:** 99.95% (NFR-DISP-001)
- **CO-04:** 99.5% (NFR-DISP-002)
- **Cola:** 99.9% con clustering

#### 6.3.2 Recuperación
- **RTO:** 5 minutos (Recovery Time Objective)
- **RPO:** 1 minuto (Recovery Point Objective)
- **Backup:** Automático cada 4 horas

---

## 7. VALIDACIÓN CONTRA PRINCIPIOS FUNDAMENTALES

### 7.1 Esqueleto Base vs Maquillajes

#### 7.1.1 Esqueleto Base (Crítico)
- **Pasos 1-17:** Flujo completo de ingestión → procesamiento → entrega
- **Componentes Core:** CO-01, CO-04, CO-06, cola de mensajes
- **Funcionalidad Esencial:** Procesamiento asíncrono, gestión de estado, notificaciones

#### 7.1.2 Maquillajes (Opcionales)
- **Paso 13:** Consulta de estado (habilita UI dashboard)
- **Métricas avanzadas:** Graficación de 20 procesos concurrentes
- **Visualización:** Frontend elaborado con WebSockets

### 7.2 Comprensión Profunda del Contexto de Dominio

#### 7.2.1 Dominio Específico
- **Recibos de pagos móviles venezolanos:** Campos específicos (banco, monto, referencia)
- **Metadatos WhatsApp:** Estructura específica (numerosorteo, idWhatsapp)
- **Validaciones:** Prefijos telefónicos venezolanos, formato de cédulas

#### 7.2.2 Flujo de Negocio
- **Acumulación:** Documentos se acumulan en lotes
- **Procesamiento por mandato:** Solo procesa cuando usuario lo solicita
- **Liberación condicional:** Libera recursos solo después de entrega exitosa
- **Procesamiento paralelo:** Múltiples lotes pueden coexistir

---

## 8. CASOS DE USO CRÍTICOS

### 8.1 Caso de Uso: Procesamiento Normal

**Escenario:** Usuario carga 5 documentos, solicita procesamiento, consulta estado, obtiene resultados

**Flujo:**
1. Usuario carga 5 documentos → CO-01 crea lote → almacena en CO-06
2. Usuario solicita procesamiento → CO-01 encola lote → CO-04 consume
3. CO-04 procesa 5 documentos → almacena resultados → notifica CO-01
4. CO-01 actualiza estado → notifica n8n → libera recursos
5. Usuario consulta estado → recibe "COMPLETADO_EXITO"
6. Usuario solicita resultados → recibe JSON consolidado

### 8.2 Caso de Uso: Procesamiento con Errores

**Escenario:** Usuario carga 5 documentos, 2 fallan en OCR, solicita resultados

**Flujo:**
1. Usuario carga 5 documentos → CO-01 crea lote
2. Usuario solicita procesamiento → CO-04 procesa
3. CO-04 procesa: 3 exitosos, 2 fallan → notifica CO-01
4. CO-01 actualiza estado → "COMPLETADO_PARCIAL_FALLO"
5. CO-01 notifica n8n con detalles de errores
6. Usuario consulta estado → recibe detalles de errores
7. Usuario solicita resultados → recibe JSON con errores incluidos

### 8.3 Caso de Uso: Procesamiento Concurrente

**Escenario:** 2 usuarios procesando lotes simultáneamente

**Flujo:**
1. Usuario A carga lote A → Usuario B carga lote B
2. Usuario A solicita procesamiento → Usuario B solicita procesamiento
3. Cola distribuye: Worker 1 procesa lote A, Worker 2 procesa lote B
4. Ambos lotes procesan independientemente
5. Resultados se consolidan independientemente
6. Notificaciones a n8n independientes
7. Liberación de recursos independiente

---

## 9. MÉTRICAS Y MONITOREO

### 9.1 Métricas Clave

#### 9.1.1 Métricas de Rendimiento
- **Latencia promedio de ingestión:** < 200ms
- **Throughput de procesamiento:** documentos/minuto
- **Tiempo de procesamiento por documento:** segundos
- **Tasa de éxito de procesamiento:** porcentaje

#### 9.1.2 Métricas de Calidad
- **Confianza promedio de OCR:** > 0.90
- **Tasa de errores de validación:** < 5%
- **Tasa de callbacks exitosos:** > 99%
- **Tasa de notificaciones n8n exitosas:** > 95%

#### 9.1.3 Métricas de Recursos
- **Utilización de CPU por worker:** < 80%
- **Utilización de memoria por worker:** < 70%
- **Utilización de almacenamiento:** < 80%
- **Tamaño promedio de cola:** < 100 mensajes

### 9.2 Alertas Críticas

#### 9.2.1 Alertas de Rendimiento
- **Latencia > 500ms:** Alerta inmediata
- **Throughput < 50% normal:** Alerta en 5 minutos
- **Cola > 1000 mensajes:** Alerta inmediata

#### 9.2.2 Alertas de Fallos
- **Tasa de errores > 10%:** Alerta inmediata
- **Worker down:** Alerta en 30 segundos
- **Almacenamiento > 90%:** Alerta inmediata

---

## 10. PLAN DE IMPLEMENTACIÓN PASO A PASO

### 10.1 Fase 1: Infraestructura Base (Semanas 1-2)
- **Semana 1:** Configuración de cola (Kafka/RabbitMQ), CO-06 básico
- **Semana 2:** Separación CO-01 y CO-04, comunicación básica

### 10.2 Fase 2: Flujo Principal (Semanas 3-4)
- **Semana 3:** Implementación pasos 1-8 (ingestión + encolamiento)
- **Semana 4:** Implementación pasos 9-12 (procesamiento + callbacks)

### 10.3 Fase 3: Integración y Consolidación (Semanas 5-6)
- **Semana 5:** Implementación pasos 13-15 (consultas + consolidación)
- **Semana 6:** Implementación pasos 16-17 (n8n + liberación)

### 10.4 Fase 4: Optimización y Monitoreo (Semanas 7-8)
- **Semana 7:** Implementación de métricas y alertas
- **Semana 8:** Optimización de rendimiento y pruebas de carga

---

## 11. CONCLUSIONES

### 11.1 Especificación Operativa Completa
Este DFD proporciona la especificación operativa inquebrantable para el sistema OCR asíncrono empresarial, definiendo cada paso, transición de estado, estructura de datos y manejo de errores necesarios para la implementación.

### 11.2 Alineación con Principios Fundamentales
- **Integridad Total:** Cada paso es verificable y trazable
- **Perfección Continua:** Manejo robusto de errores y recuperación
- **Zero-Fault Detection:** Detección proactiva en cada etapa
- **Interface Excellence:** Comunicación clara entre componentes

### 11.3 Preparación para Implementación
La especificación está lista para guiar la implementación paso a paso, asegurando que el sistema cumpla con todos los requisitos funcionales y no funcionales definidos en la documentación unificada.

### 11.4 Flexibilidad y Escalabilidad
El flujo diseñado permite procesamiento concurrente de múltiples lotes, escalabilidad horizontal independiente de componentes, y recuperación automática de fallos, cumpliendo con los principios de arquitectura empresarial.

---

**Fin del Reporte**  
**Preparado por:** Agente Replit siguiendo metodología Zero-Fault Detection  
**Fecha:** 15 de Julio de 2025  
**Clasificación:** ESPECIFICACIÓN OPERATIVA BLINDADA - READY FOR IMPLEMENTATION