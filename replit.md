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
- ✅ Corrección de extracción de coordenadas
- ✅ Respuestas en español implementadas
- ✅ Algoritmo de detección JSON corregido
- ✅ Interfaz mejorada con dashboard empresarial de pestañas
- ✅ Sistema de gestión de API Keys implementado
- ✅ Documentación completa de APIs externas
- ✅ Ejemplos de uso con cURL, JavaScript y Python
- ✅ Autenticación Bearer Token para APIs externas
- ✅ Formulario de subida de archivos visible y funcional

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