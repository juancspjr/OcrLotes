/**
 * API CLIENT - SISTEMA OCR EMPRESARIAL
 * Módulo para manejo de todas las interacciones con el backend
 * FILOSOFÍA: INTEGRIDAD TOTAL + TRANSPARENCIA TOTAL
 */

class APIClient {
    constructor() {
        this.baseURL = '';
        this.timeout = 30000;
        this.requests = new Map(); // Tracking de requests activos
    }

    /**
     * CONTRATO: POST /api/ocr/process_image
     * Upload de archivos múltiples con metadatos WhatsApp
     */
    async uploadFiles(files, metadata = {}) {
        const formData = new FormData();
        
        // Agregar archivos con nombre correcto según contrato backend
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        
        // Agregar metadatos WhatsApp según especificación
        const defaultMetadata = {
            numerosorteo: '',
            fechasorteo: '',
            idWhatsapp: '',
            nombre: '',
            horamin: '',
            caption: '',
            otro_valor: ''
        };
        
        const finalMetadata = { ...defaultMetadata, ...metadata };
        Object.entries(finalMetadata).forEach(([key, value]) => {
            if (value) formData.append(key, value);
        });

        return this._makeRequest('POST', '/api/ocr/process_image', formData);
    }

    /**
     * CONTRATO: POST /api/ocr/process_batch
     * Procesamiento por lotes con request_id tracking y parámetros esenciales
     */
    async processBatch(options = {}) {
        const payload = {
            profile: options.profile || 'ultra_rapido',
            batch_size: options.batch_size || 5
        };

        // Agregar parámetros esenciales al payload
        if (options.codigo_sorteo) payload.codigo_sorteo = options.codigo_sorteo;
        if (options.id_whatsapp) payload.id_whatsapp = options.id_whatsapp;
        if (options.nombre_usuario) payload.nombre_usuario = options.nombre_usuario;
        if (options.caption) payload.caption = options.caption;
        if (options.hora_exacta) payload.hora_exacta = options.hora_exacta;

        // Preparar headers con API Key si está disponible
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (options.api_key) {
            headers['Authorization'] = `Bearer ${options.api_key}`;
        }

        return this._makeRequest('POST', '/api/ocr/process_batch', JSON.stringify(payload), headers);
    }

    /**
     * CONTRATO: GET /api/ocr/queue/status
     * Estado actual de cola y sistema
     */
    async getQueueStatus() {
        return this._makeRequest('GET', '/api/ocr/queue/status');
    }

    /**
     * CONTRATO: GET /api/ocr/processed_files
     * Lista de archivos procesados con metadatos
     */
    async getProcessedFiles() {
        return this._makeRequest('GET', '/api/ocr/processed_files');
    }

    /**
     * CONTRATO: GET /api/ocr/result_data/<filename>
     * Datos estructurados para visualizador
     */
    async getResultData(filename) {
        // Sanitizar filename para URL
        const cleanFilename = encodeURIComponent(filename);
        return this._makeRequest('GET', `/api/ocr/result_data/${cleanFilename}`);
    }

    /**
     * CONTRATO: GET /api/extract_results
     * JSON consolidado empresarial con request_id para agrupación
     */
    async extractResults() {
        return this._makeRequest('GET', '/api/extract_results');
    }

    /**
     * CONTRATO: POST /api/clean
     * Limpieza completa del sistema con retención 24h
     */
    async cleanSystem() {
        return this._makeRequest('POST', '/api/clean', '{}', {
            'Content-Type': 'application/json'
        });
    }

    /**
     * CONTRATO: POST /api/clean_queue
     * Limpieza solo de cola (inbox)
     */
    async cleanQueue() {
        return this._makeRequest('POST', '/api/clean_queue', '{}', {
            'Content-Type': 'application/json'
        });
    }

    /**
     * MÉTRICAS DE MONITOREO (EXTENSIÓN REQUERIDA)
     * Endpoint para métricas por lote según Mandato 14
     */
    async getBatchMetrics(batchId = null) {
        const url = batchId ? `/api/metrics/batch/${batchId}` : '/api/metrics/batch';
        return this._makeRequest('GET', url);
    }

    /**
     * MÉTODO INTERNO: Manejo unificado de requests
     * Implementa manejo de errores según especificación backend
     */
    async _makeRequest(method, url, body = null, headers = {}) {
        const requestId = this._generateRequestId();
        const fullURL = this.baseURL + url;
        
        const requestConfig = {
            method: method,
            headers: {
                ...headers
            },
            timeout: this.timeout
        };

        if (body && !(body instanceof FormData)) {
            requestConfig.body = body;
        } else if (body instanceof FormData) {
            requestConfig.body = body;
            // No agregar Content-Type para FormData - el navegador lo maneja
        }

        try {
            this.requests.set(requestId, { url: fullURL, method, timestamp: Date.now() });
            
            const response = await fetch(fullURL, requestConfig);
            const data = await response.json();

            // Manejo de errores según especificación backend
            if (!response.ok || data.status === 'error') {
                throw new APIError(
                    data.mensaje || data.message || 'Error desconocido',
                    response.status,
                    data.error_code || 'UNKNOWN_ERROR',
                    data
                );
            }

            this.requests.delete(requestId);
            return data;

        } catch (error) {
            this.requests.delete(requestId);
            
            if (error instanceof APIError) {
                throw error;
            }
            
            // Error de red o timeout
            throw new APIError(
                'Error de conexión con el servidor',
                0,
                'NETWORK_ERROR',
                { originalError: error.message }
            );
        }
    }

    /**
     * Generar ID único para tracking de requests
     */
    _generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Obtener requests activos (para debugging)
     */
    getActiveRequests() {
        return Array.from(this.requests.entries());
    }

    /**
     * Cancelar todos los requests activos
     */
    cancelAllRequests() {
        this.requests.clear();
    }
}

/**
 * CLASE DE ERROR PERSONALIZADA
 * Manejo estructurado de errores según especificación backend
 */
class APIError extends Error {
    constructor(message, status, code, details = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.code = code;
        this.details = details;
        this.timestamp = new Date().toISOString();
    }

    /**
     * Obtener mensaje de error para mostrar al usuario
     */
    getUserMessage() {
        switch (this.code) {
            case 'FILE_TOO_LARGE_413':
                return 'El archivo es demasiado grande (máximo 16MB)';
            case 'BAD_REQUEST_400':
                return 'Solicitud incorrecta. Verifique los datos enviados';
            case 'NOT_FOUND_404':
                return 'Recurso no encontrado';
            case 'BATCH_PROCESSING_ERROR':
                return `Error en procesamiento: ${this.message}`;
            case 'NETWORK_ERROR':
                return 'Error de conexión. Verifique su internet';
            default:
                return this.message || 'Error desconocido del servidor';
        }
    }

    /**
     * Obtener clase CSS para el tipo de error
     */
    getErrorClass() {
        if (this.status >= 500) return 'error-server';
        if (this.status >= 400) return 'error-client';
        if (this.code === 'NETWORK_ERROR') return 'error-network';
        return 'error-unknown';
    }
}

// Instancia global del cliente API
window.apiClient = new APIClient();
window.APIError = APIError;