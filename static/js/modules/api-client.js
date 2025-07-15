/**
 * API CLIENT MODULE - SISTEMA OCR EMPRESARIAL
 * FILOSOFÍA: INTEGRIDAD TOTAL + INTERFACE EXCELLENCE
 * 
 * Módulo encargado de gestionar todas las comunicaciones con el backend
 * siguiendo el patrón de cliente API robusto con manejo de errores.
 */

window.OCRSystem = window.OCRSystem || {};

(function() {
    'use strict';

    class APIClient {
        constructor(baseUrl) {
            this.baseUrl = baseUrl;
            this.defaultHeaders = {
                'Content-Type': 'application/json'
            };
            this.timeout = 30000; // 30 segundos
        }

        /**
         * Realizar petición HTTP genérica
         */
        async request(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            const config = {
                method: 'GET',
                headers: { ...this.defaultHeaders },
                ...options
            };

            // Agregar API key si está disponible
            const apiKey = this.getApiKey();
            if (apiKey) {
                config.headers['X-API-Key'] = apiKey;
            }

            try {
                console.log(`🌐 API Request: ${config.method} ${endpoint}`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    console.log(`✅ API Response: ${config.method} ${endpoint}`, data);
                    return data;
                } else {
                    return response;
                }

            } catch (error) {
                console.error(`❌ API Error: ${config.method} ${endpoint}`, error);
                
                if (error.name === 'AbortError') {
                    throw new Error('La petición ha excedido el tiempo límite');
                }
                
                throw error;
            }
        }

        /**
         * Subir archivos con parámetros
         */
        async uploadFiles(files, parameters = {}) {
            const formData = new FormData();
            
            // Agregar archivos
            files.forEach((file, index) => {
                formData.append('files', file.file);
                
                // Agregar parámetros específicos del archivo
                const fileParams = file.parameters || {};
                Object.keys(fileParams).forEach(key => {
                    formData.append(`${key}_${index}`, fileParams[key]);
                });
            });

            // Agregar parámetros globales
            Object.keys(parameters).forEach(key => {
                formData.append(key, parameters[key]);
            });

            try {
                const response = await fetch(`${this.baseUrl}/api/upload`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        // No establecer Content-Type para FormData
                        ...(this.getApiKey() ? { 'X-API-Key': this.getApiKey() } : {})
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Error desconocido' }));
                    throw new Error(errorData.error || `HTTP ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                console.error('❌ Error subiendo archivos:', error);
                throw error;
            }
        }

        /**
         * Procesar lote de archivos
         */
        async processBatch(files, profile = 'ultra_rapido') {
            const formData = new FormData();
            
            // Agregar perfil de procesamiento
            formData.append('profile', profile);
            
            // Agregar archivos con sus parámetros
            files.forEach((fileData, index) => {
                formData.append('files', fileData.file);
                
                // Agregar parámetros de seguimiento
                const params = fileData.parameters || {};
                formData.append(`codigo_sorteo_${index}`, params.codigo_sorteo || '');
                formData.append(`id_whatsapp_${index}`, params.id_whatsapp || '');
                formData.append(`nombre_usuario_${index}`, params.nombre_usuario || '');
                formData.append(`caption_${index}`, params.caption || '');
                formData.append(`hora_exacta_${index}`, params.hora_exacta || '');
                formData.append(`numero_llegada_${index}`, params.numero_llegada || index + 1);
            });

            try {
                const response = await fetch(`${this.baseUrl}/api/ocr/process_batch`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        ...(this.getApiKey() ? { 'X-API-Key': this.getApiKey() } : {})
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Error desconocido' }));
                    throw new Error(errorData.error || `HTTP ${response.status}`);
                }

                const result = await response.json();
                console.log('✅ Lote procesado exitosamente:', result);
                return result;
                
            } catch (error) {
                console.error('❌ Error procesando lote:', error);
                throw error;
            }
        }

        /**
         * Obtener archivos procesados
         */
        async getProcessedFiles() {
            return this.request('/api/ocr/processed_files');
        }

        /**
         * Obtener resultados consolidados
         */
        async extractResults() {
            return this.request('/api/extract_results');
        }

        /**
         * Limpiar resultados del sistema
         */
        async cleanResults() {
            return this.request('/api/clean', { method: 'POST' });
        }

        /**
         * Obtener estado de la cola
         */
        async getQueueStatus() {
            return this.request('/api/ocr/queue/status');
        }

        /**
         * Obtener resultado específico por ID
         */
        async getResult(resultId) {
            return this.request(`/api/ocr/result/${resultId}`);
        }

        /**
         * Obtener datos de resultado por filename
         */
        async getResultData(filename) {
            return this.request(`/api/ocr/result_data/${encodeURIComponent(filename)}`);
        }

        /**
         * Obtener métricas del sistema
         */
        async getSystemMetrics() {
            try {
                // Combinar varias fuentes de métricas
                const [processedFiles, queueStatus] = await Promise.all([
                    this.getProcessedFiles(),
                    this.getQueueStatus().catch(() => ({ queue_size: 0, status: 'unknown' }))
                ]);

                // Calcular métricas
                const totalProcessed = processedFiles.length || 0;
                const totalSuccess = processedFiles.filter(f => f.has_ocr_data).length || 0;
                const totalErrors = totalProcessed - totalSuccess;
                const successRate = totalProcessed > 0 ? (totalSuccess / totalProcessed * 100).toFixed(1) : 0;

                return {
                    totalProcessed,
                    totalSuccess,
                    totalErrors,
                    successRate: `${successRate}%`,
                    queueSize: queueStatus.queue_size || 0,
                    systemStatus: queueStatus.status || 'unknown'
                };
            } catch (error) {
                console.error('❌ Error obteniendo métricas:', error);
                return {
                    totalProcessed: 0,
                    totalSuccess: 0,
                    totalErrors: 0,
                    successRate: '0%',
                    queueSize: 0,
                    systemStatus: 'error'
                };
            }
        }

        /**
         * Obtener historial de lotes
         */
        async getBatchHistory() {
            try {
                const processedFiles = await this.getProcessedFiles();
                
                // Validar que processedFiles sea un array
                if (!Array.isArray(processedFiles)) {
                    console.warn('⚠️ processedFiles no es un array válido');
                    return [];
                }
                
                // Agrupar por request_id/lote
                const batchMap = new Map();
                
                processedFiles.forEach(file => {
                    // Validar que file sea un objeto válido
                    if (!file || typeof file !== 'object' || !file.filename) {
                        console.warn('⚠️ Archivo inválido omitido:', file);
                        return;
                    }
                    
                    // Extraer ID de lote del nombre del archivo
                    const batchMatch = file.filename.match(/^BATCH_(\d{8}_\d{6}_[a-f0-9]+)/);
                    const batchId = batchMatch ? batchMatch[1] : 'unknown';
                    
                    if (!batchMap.has(batchId)) {
                        batchMap.set(batchId, {
                            id: batchId,
                            date: this.extractDateFromBatchId(batchId),
                            files: [],
                            totalFiles: 0,
                            successCount: 0,
                            errorCount: 0,
                            avgProcessingTime: 0
                        });
                    }
                    
                    const batch = batchMap.get(batchId);
                    batch.files.push(file);
                    batch.totalFiles++;
                    
                    if (file.has_ocr_data) {
                        batch.successCount++;
                    } else {
                        batch.errorCount++;
                    }
                });

                // Convertir a array y ordenar por fecha
                const batches = Array.from(batchMap.values()).sort((a, b) => {
                    try {
                        return new Date(b.date) - new Date(a.date);
                    } catch (error) {
                        console.warn('⚠️ Error ordenando lotes por fecha:', error);
                        return 0;
                    }
                });

                return batches;
            } catch (error) {
                console.error('❌ Error obteniendo historial de lotes:', error);
                // Retornar estructura vacía pero válida
                return [];
            }
        }

        /**
         * Generar nueva API Key
         */
        async generateApiKey() {
            try {
                const response = await this.request('/api/generate_api_key', { method: 'POST' });
                if (response.api_key) {
                    this.setApiKey(response.api_key);
                }
                return response;
            } catch (error) {
                console.error('❌ Error generando API Key:', error);
                throw error;
            }
        }

        /**
         * Obtener API Key actual
         */
        async getCurrentApiKey() {
            try {
                return await this.request('/api/current_api_key');
            } catch (error) {
                console.error('❌ Error obteniendo API Key actual:', error);
                throw error;
            }
        }

        /**
         * Extraer fecha del ID de lote
         */
        extractDateFromBatchId(batchId) {
            try {
                // Validar que batchId sea válido
                if (!batchId || typeof batchId !== 'string') {
                    return new Date();
                }
                
                const match = batchId.match(/^(\d{8})_(\d{6})/);
                if (match) {
                    const [, dateStr, timeStr] = match;
                    
                    // Validar longitudes
                    if (dateStr.length !== 8 || timeStr.length !== 6) {
                        return new Date();
                    }
                    
                    const year = dateStr.substring(0, 4);
                    const month = dateStr.substring(4, 6);
                    const day = dateStr.substring(6, 8);
                    const hour = timeStr.substring(0, 2);
                    const minute = timeStr.substring(2, 4);
                    const second = timeStr.substring(4, 6);
                    
                    // Validar rangos válidos
                    if (parseInt(month) < 1 || parseInt(month) > 12 ||
                        parseInt(day) < 1 || parseInt(day) > 31 ||
                        parseInt(hour) > 23 || parseInt(minute) > 59 || parseInt(second) > 59) {
                        return new Date();
                    }
                    
                    const dateStr_ISO = `${year}-${month}-${day}T${hour}:${minute}:${second}`;
                    const parsedDate = new Date(dateStr_ISO);
                    
                    // Validar que la fecha sea válida
                    if (isNaN(parsedDate.getTime())) {
                        return new Date();
                    }
                    
                    return parsedDate;
                }
            } catch (error) {
                console.warn('⚠️ Error parseando fecha de lote:', error);
            }
            return new Date();
        }

        /**
         * Gestión de API Key local
         */
        getApiKey() {
            return localStorage.getItem('ocr_api_key');
        }

        setApiKey(apiKey) {
            if (apiKey) {
                localStorage.setItem('ocr_api_key', apiKey);
            } else {
                localStorage.removeItem('ocr_api_key');
            }
        }

        /**
         * Ping al servidor para verificar conectividad
         */
        async ping() {
            try {
                const start = Date.now();
                await this.request('/api/ocr/processed_files');
                const duration = Date.now() - start;
                return { status: 'ok', latency: duration };
            } catch (error) {
                return { status: 'error', error: error.message };
            }
        }

        /**
         * Obtener información del sistema
         */
        async getSystemInfo() {
            try {
                // Información básica del sistema
                const ping = await this.ping();
                const metrics = await this.getSystemMetrics();
                
                return {
                    version: '2.0',
                    backend_status: ping.status,
                    latency: ping.latency || null,
                    ...metrics
                };
            } catch (error) {
                console.error('❌ Error obteniendo información del sistema:', error);
                return {
                    version: '2.0',
                    backend_status: 'error',
                    latency: null,
                    totalProcessed: 0,
                    totalSuccess: 0,
                    totalErrors: 0,
                    successRate: '0%'
                };
            }
        }
    }

    // Exportar el cliente API
    window.OCRSystem.APIClient = APIClient;

    console.log('🌐 API Client module loaded');

})();