/**
 * API DOCS MODULE - SISTEMA OCR EMPRESARIAL
 * FILOSOFÍA: INTEGRIDAD TOTAL + INTERFACE EXCELLENCE
 * 
 * Módulo encargado de la gestión de API Keys y documentación interactiva
 * para integración con servicios externos como N8N.
 */

window.OCRSystem = window.OCRSystem || {};

(function() {
    'use strict';

    class APIDocs {
        constructor(config) {
            this.config = config;
            this.apiClient = config.apiClient;
            this.currentApiKey = null;
            
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.loadCurrentApiKey();
            this.generateDocumentation();
            console.log('📚 API Docs inicializado');
        }

        /**
         * Configurar event listeners
         */
        setupEventListeners() {
            // Botón generar nueva API Key
            const generateBtn = document.getElementById('generateApiKeyBtn');
            if (generateBtn) {
                generateBtn.addEventListener('click', () => this.generateNewApiKey());
            }

            // Toggle visibilidad de API Key
            const toggleBtn = document.getElementById('toggleApiKeyVisibility');
            const toggleIcon = document.getElementById('toggleApiKeyIcon');
            const apiKeyInput = document.getElementById('currentApiKey');
            
            if (toggleBtn && toggleIcon && apiKeyInput) {
                toggleBtn.addEventListener('click', () => {
                    const isPassword = apiKeyInput.type === 'password';
                    apiKeyInput.type = isPassword ? 'text' : 'password';
                    toggleIcon.className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
                });
            }

            // Botón copiar API Key
            const copyBtn = document.getElementById('copyApiKeyBtn');
            if (copyBtn) {
                copyBtn.addEventListener('click', () => this.copyApiKey());
            }
        }

        /**
         * Cargar API Key actual
         */
        async loadCurrentApiKey() {
            try {
                // Intentar obtener desde localStorage primero
                this.currentApiKey = this.apiClient.getApiKey();
                
                if (!this.currentApiKey) {
                    // Si no existe, intentar obtener del servidor
                    const response = await this.apiClient.getCurrentApiKey();
                    this.currentApiKey = response.api_key;
                    
                    if (this.currentApiKey) {
                        this.apiClient.setApiKey(this.currentApiKey);
                    }
                }
                
                this.updateApiKeyDisplay();
                
            } catch (error) {
                console.warn('⚠️ No se pudo cargar API Key:', error);
                this.currentApiKey = null;
                this.updateApiKeyDisplay();
            }
        }

        /**
         * Actualizar visualización de API Key
         */
        updateApiKeyDisplay() {
            const apiKeyInput = document.getElementById('currentApiKey');
            if (apiKeyInput) {
                apiKeyInput.value = this.currentApiKey || 'No generada';
                
                if (!this.currentApiKey) {
                    apiKeyInput.style.fontStyle = 'italic';
                    apiKeyInput.style.color = '#6c757d';
                } else {
                    apiKeyInput.style.fontStyle = 'normal';
                    apiKeyInput.style.color = '#212529';
                }
            }
        }

        /**
         * Generar nueva API Key
         */
        async generateNewApiKey() {
            try {
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification('Generando nueva API Key...', 'info');
                }
                
                const response = await this.apiClient.generateApiKey();
                
                if (response.api_key) {
                    this.currentApiKey = response.api_key;
                    this.updateApiKeyDisplay();
                    
                    if (window.OCRSystem.Main) {
                        window.OCRSystem.Main.showNotification(
                            'Nueva API Key generada exitosamente',
                            'success'
                        );
                    }
                } else {
                    throw new Error('No se recibió API Key en la respuesta');
                }
                
            } catch (error) {
                console.error('❌ Error generando API Key:', error);
                
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        'Error generando API Key: ' + error.message,
                        'error'
                    );
                }
            }
        }

        /**
         * Copiar API Key al portapapeles
         */
        async copyApiKey() {
            if (!this.currentApiKey) {
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        'No hay API Key para copiar',
                        'warning'
                    );
                }
                return;
            }

            try {
                await navigator.clipboard.writeText(this.currentApiKey);
                
                // Efecto visual en el botón
                const copyBtn = document.getElementById('copyApiKeyBtn');
                if (copyBtn) {
                    const originalHTML = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                    copyBtn.classList.add('btn-success');
                    copyBtn.classList.remove('btn-outline-primary');
                    
                    setTimeout(() => {
                        copyBtn.innerHTML = originalHTML;
                        copyBtn.classList.remove('btn-success');
                        copyBtn.classList.add('btn-outline-primary');
                    }, 1000);
                }
                
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        'API Key copiada al portapapeles',
                        'success'
                    );
                }
                
            } catch (error) {
                console.error('❌ Error copiando API Key:', error);
                
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        'Error copiando API Key',
                        'error'
                    );
                }
            }
        }

        /**
         * Generar documentación de endpoints
         */
        generateDocumentation() {
            const docsContainer = document.getElementById('apiDocumentation');
            if (!docsContainer) return;

            const baseUrl = window.location.origin;
            
            const endpoints = [
                {
                    method: 'POST',
                    path: '/api/ocr/process_batch',
                    title: 'Procesar Lote de Imágenes',
                    description: 'Procesa un lote de imágenes con parámetros de seguimiento individuales.',
                    parameters: [
                        { name: 'files', type: 'file[]', required: true, description: 'Archivos de imagen a procesar' },
                        { name: 'profile', type: 'string', required: false, description: 'Perfil de procesamiento (ultra_rapido, balanced, high_confidence)' },
                        { name: 'codigo_sorteo_X', type: 'string', required: false, description: 'Código de sorteo para archivo X' },
                        { name: 'id_whatsapp_X', type: 'string', required: false, description: 'ID WhatsApp para archivo X' },
                        { name: 'nombre_usuario_X', type: 'string', required: false, description: 'Nombre de usuario para archivo X' },
                        { name: 'caption_X', type: 'string', required: false, description: 'Caption para archivo X' },
                        { name: 'hora_exacta_X', type: 'string', required: false, description: 'Hora exacta para archivo X' },
                        { name: 'numero_llegada_X', type: 'number', required: false, description: 'Número de llegada para archivo X' }
                    ],
                    example: this.generateCurlExample('POST', '/api/ocr/process_batch', true),
                    response: {
                        status: 200,
                        data: {
                            status: 'exitoso',
                            message: 'Lote procesado exitosamente',
                            request_id: 'BATCH_20250711_043000_abc123',
                            archivos_procesados: 2,
                            tiempo_total: 1.25
                        }
                    }
                },
                {
                    method: 'GET',
                    path: '/api/extract_results',
                    title: 'Extraer Resultados Consolidados',
                    description: 'Obtiene todos los resultados procesados en formato JSON consolidado.',
                    parameters: [],
                    example: this.generateCurlExample('GET', '/api/extract_results'),
                    response: {
                        status: 200,
                        data: {
                            metadata: {
                                fecha_extraccion: '2025-07-11T04:30:00Z',
                                total_archivos: 2,
                                version_sistema: '2.0'
                            },
                            archivos_procesados: [
                                {
                                    nombre_archivo: 'recibo_001.jpg',
                                    codigo_sorteo: 'A',
                                    id_whatsapp: '123456789@lid',
                                    nombre_usuario: 'Juan',
                                    caption: 'Pago Móvil',
                                    hora_exacta: '14-30',
                                    numero_llegada: 1,
                                    referencia: '123456789',
                                    monto: '250.00',
                                    bancoorigen: 'BANCO MERCANTIL',
                                    datosbeneficiario: {
                                        cedula: '12345678',
                                        telefono: '04121234567',
                                        banco_destino: 'BANCO DE VENEZUELA'
                                    },
                                    pago_fecha: '11/07/2025',
                                    concepto: 'Transferencia',
                                    texto_total_ocr: 'Texto completo extraído...',
                                    extraction_stats: {
                                        confidence: 0.95,
                                        total_words: 25,
                                        processing_time: 0.75
                                    }
                                }
                            ]
                        }
                    }
                },
                {
                    method: 'GET',
                    path: '/api/ocr/queue/status',
                    title: 'Estado de la Cola',
                    description: 'Verifica el estado actual de la cola de procesamiento.',
                    parameters: [],
                    example: this.generateCurlExample('GET', '/api/ocr/queue/status'),
                    response: {
                        status: 200,
                        data: {
                            queue_size: 0,
                            status: 'idle',
                            last_processed: '2025-07-11T04:30:00Z'
                        }
                    }
                },
                {
                    method: 'POST',
                    path: '/api/clean',
                    title: 'Limpiar Resultados',
                    description: 'Limpia los resultados del sistema con retención de 24 horas.',
                    parameters: [],
                    example: this.generateCurlExample('POST', '/api/clean'),
                    response: {
                        status: 200,
                        data: {
                            status: 'exitoso',
                            message: 'Sistema limpiado exitosamente',
                            results_preserved: 5,
                            results_deleted: 3
                        }
                    }
                }
            ];

            const html = endpoints.map(endpoint => this.renderEndpointDoc(endpoint)).join('');
            docsContainer.innerHTML = html;
            
            this.attachDocEventListeners();
        }

        /**
         * Renderizar documentación de endpoint
         */
        renderEndpointDoc(endpoint) {
            const parametersTable = endpoint.parameters.length > 0 ? `
                <div class="endpoint-content" id="content-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">
                    <div class="endpoint-description">
                        <p>${endpoint.description}</p>
                    </div>
                    
                    <ul class="nav nav-tabs endpoint-tabs" role="tablist">
                        <li class="nav-item">
                            <a class="nav-link active" data-bs-toggle="tab" href="#params-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">Parámetros</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#example-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">Ejemplo</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#response-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">Respuesta</a>
                        </li>
                    </ul>
                    
                    <div class="tab-content">
                        <div class="tab-pane fade show active" id="params-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">
                            <table class="param-table">
                                <thead>
                                    <tr>
                                        <th>Parámetro</th>
                                        <th>Tipo</th>
                                        <th>Requerido</th>
                                        <th>Descripción</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${endpoint.parameters.map(param => `
                                        <tr>
                                            <td><span class="param-name">${param.name}</span></td>
                                            <td><span class="param-type ${param.type}">${param.type}</span></td>
                                            <td><span class="param-${param.required ? 'required' : 'optional'}">${param.required ? 'Sí' : 'No'}</span></td>
                                            <td>${param.description}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="tab-pane fade" id="example-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">
                            <div class="code-block" data-language="bash">
                                <button class="copy-btn" onclick="copyCode(this)">Copiar</button>
                                <pre><code>${endpoint.example}</code></pre>
                            </div>
                        </div>
                        
                        <div class="tab-pane fade" id="response-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">
                            <div class="response-example">
                                <h6><span class="status-code success">${endpoint.response.status}</span>Respuesta Exitosa</h6>
                                <div class="code-block" data-language="json">
                                    <button class="copy-btn" onclick="copyCode(this)">Copiar</button>
                                    <pre><code>${JSON.stringify(endpoint.response.data, null, 2)}</code></pre>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="endpoint-content" id="content-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}">
                    <div class="endpoint-description">
                        <p>${endpoint.description}</p>
                    </div>
                    
                    <div class="code-block" data-language="bash">
                        <button class="copy-btn" onclick="copyCode(this)">Copiar</button>
                        <pre><code>${endpoint.example}</code></pre>
                    </div>
                    
                    <div class="response-example">
                        <h6><span class="status-code success">${endpoint.response.status}</span>Respuesta Exitosa</h6>
                        <div class="code-block" data-language="json">
                            <button class="copy-btn" onclick="copyCode(this)">Copiar</button>
                            <pre><code>${JSON.stringify(endpoint.response.data, null, 2)}</code></pre>
                        </div>
                    </div>
                </div>
            `;

            return `
                <div class="endpoint-section">
                    <div class="endpoint-header" onclick="toggleEndpoint('${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}')">
                        <div class="endpoint-title">
                            <span class="http-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                            <span class="endpoint-url">${endpoint.path}</span>
                        </div>
                        <div class="endpoint-title">
                            <span style="font-weight: 600;">${endpoint.title}</span>
                        </div>
                        <i class="fas fa-chevron-down expand-indicator" id="indicator-${endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}"></i>
                    </div>
                    ${parametersTable}
                </div>
            `;
        }

        /**
         * Generar ejemplo de curl
         */
        generateCurlExample(method, path, isMultipart = false) {
            const baseUrl = window.location.origin;
            const apiKeyHeader = this.currentApiKey ? ` \\
  -H "X-API-Key: ${this.currentApiKey}"` : '';

            if (method === 'GET') {
                return `curl -X GET "${baseUrl}${path}"${apiKeyHeader}`;
            }

            if (isMultipart) {
                return `curl -X POST "${baseUrl}${path}" \\
  -F "files=@recibo_001.jpg" \\
  -F "files=@recibo_002.jpg" \\
  -F "profile=ultra_rapido" \\
  -F "codigo_sorteo_0=A" \\
  -F "id_whatsapp_0=123456789@lid" \\
  -F "nombre_usuario_0=Juan" \\
  -F "caption_0=Pago Móvil" \\
  -F "hora_exacta_0=14-30" \\
  -F "numero_llegada_0=1"${apiKeyHeader}`;
            } else {
                return `curl -X POST "${baseUrl}${path}"${apiKeyHeader}`;
            }
        }

        /**
         * Adjuntar event listeners de documentación
         */
        attachDocEventListeners() {
            // Función global para toggle de endpoints
            window.toggleEndpoint = (endpointId) => {
                const content = document.getElementById(`content-${endpointId}`);
                const indicator = document.getElementById(`indicator-${endpointId}`);
                
                if (content && indicator) {
                    const isVisible = content.classList.contains('show');
                    
                    if (isVisible) {
                        content.classList.remove('show');
                        indicator.classList.remove('expanded');
                    } else {
                        content.classList.add('show');
                        indicator.classList.add('expanded');
                    }
                }
            };

            // Función global para copiar código
            window.copyCode = async (button) => {
                const codeBlock = button.nextElementSibling.textContent;
                
                try {
                    await navigator.clipboard.writeText(codeBlock);
                    
                    const originalText = button.textContent;
                    button.textContent = 'Copiado!';
                    button.classList.add('success');
                    
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.classList.remove('success');
                    }, 1000);
                    
                } catch (error) {
                    console.error('❌ Error copiando código:', error);
                }
            };
        }

        /**
         * Refrescar documentación
         */
        refresh() {
            this.loadCurrentApiKey();
            this.generateDocumentation();
        }

        /**
         * Actualizar base URL en ejemplos
         */
        updateBaseUrl() {
            const baseUrlElement = document.getElementById('baseUrl');
            if (baseUrlElement) {
                baseUrlElement.textContent = window.location.origin;
            }
            
            // Regenerar documentación con nueva URL
            this.generateDocumentation();
        }
    }

    // Exportar el API Docs
    window.OCRSystem.APIDocs = APIDocs;

    console.log('📚 API Docs module loaded');

})();