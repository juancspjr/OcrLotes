# Sistema OCR Asíncrono Empresarial

## Descripción del Proyecto
Sistema OCR asíncrono de alto rendimiento para procesamiento de recibos de pago y documentos, con extracción de coordenadas precisas y compatibilidad con n8n.

## Funcionalidades Principales
- **OCR Asíncrono**: Procesamiento por lotes con cola inteligente
- **Extracción de Coordenadas**: Posición exacta de cada palabra detectada
- **Respuestas en Español**: Interfaz completamente en español
- **Integración n8n**: Compatible con workflows de automatización
- **Perfiles de Rendimiento**: Desde ultra_rapido hasta high_confidence

## Arquitectura Técnica
- **Backend**: Flask con workers asíncronos
- **OCR Engine**: OnnxTR optimizado
- **Base de Datos**: PostgreSQL integrado
- **Frontend**: Dashboard web con Bootstrap

## Cambios Recientes
- ✅ Migración completada de Replit Agent a Replit
- ✅ Interface Excellence implementation completada
- ✅ Enhanced filename visibility implementada
- ✅ Professional external environment styling aplicado
- ✅ Comprehensive component validation añadida
- ✅ Real-time visual change tracking implementado
- ✅ Enhanced file metadata display con WhatsApp data
- ✅ Metadatos de WhatsApp completamente funcionales (numerosorteo, idWhatsapp, nombre, horamin, caption)
- ✅ Sistema de subida múltiple de archivos corregido
- ✅ Cola de archivos visible con metadatos WhatsApp completos
- ✅ Corrección de errores de upload y manejo robusto de archivos
- ✅ Testing integral implementado con philosophy compliance

## Correcciones Críticas Implementadas - Zero-Fault Detection (Julio 2025)
- ✅ **ERROR CRÍTICO 1**: Unificación de nombres de campos FormData ('images' → 'files')
- ✅ **ERROR CRÍTICO 2**: Implementación de envío de metadatos WhatsApp desde formulario
- ✅ **ERROR CRÍTICO 3**: Corrección de parsing de metadatos WhatsApp con validación robusta
- ✅ **ERROR CRÍTICO 4**: Preview reactivo automático con listeners en tiempo real
- ✅ **ERROR CRÍTICO 5**: Función copyFilenamePreview completamente funcional
- ✅ **VALIDACIÓN ENTERPRISE**: Sistema de validación de metadatos WhatsApp (A-Z, YYYYMMDD, @lid, HH-MM)
- ✅ **MANEJO DE ERRORES**: Error handlers estandarizados 400/404/413/500 con logging
- ✅ **INTERFACE EXCELLENCE**: Binding reactivo y validación de componentes

## Preferencias del Usuario
- Interfaz completamente en español
- Workflow por etapas: Subir → Lista no procesados → Procesar lote → Extraer resultados → Limpiar
- Botón "Subir" solo para cargar y renombrar archivos
- Botón separado "Procesar Todo el Lote" para ejecutar OCR
- Botón "Extraer Resultados JSON" para descargar resultados
- Botón "Limpiar Sistema" al final
- Mostrar listas separadas de archivos pendientes y procesados
- Prioridad en coordenadas correctas y archivos JSON visibles

## APIs Principales
- `POST /api/ocr/process_image`: Encolar imagen
- `POST /api/ocr/process_batch`: Procesar lote
- `GET /api/ocr/result/{id}`: Obtener resultados
- `GET /api/ocr/processed_files`: Listar archivos procesados

## Estado del Proyecto
🟢 **COMPLETADO** - Sistema funcional y listo para producción