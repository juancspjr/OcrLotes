/**
 * FILE MANAGER - SISTEMA OCR EMPRESARIAL
 * Módulo para gestión de archivos, drag&drop y cola de procesamiento
 * FILOSOFÍA: PERFECCIÓN CONTINUA + INTEGRIDAD TOTAL
 */

class FileManager {
    constructor() {
        this.files = new Map(); // Mapa de archivos con estado
        this.dragCounter = 0;
        this.maxFileSize = 16 * 1024 * 1024; // 16MB según especificación
        this.allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
        this.currentUploadRequestId = null;
        
        this.initializeElements();
        this.bindEvents();
    }

    /**
     * INICIALIZACIÓN DE ELEMENTOS DOM
     */
    initializeElements() {
        // Elementos principales según especificación Mandato 14
        this.elements = {
            dropZone: document.getElementById('dropZone'),
            fileInput: document.getElementById('fileInput'),
            selectButton: document.getElementById('selectFilesBtn'),
            fileListDisplay: document.getElementById('fileListDisplay'),
            processBatchBtn: document.getElementById('processBatchBtn'),
            uploadProgress: document.getElementById('uploadProgress'),
            batchProgress: document.getElementById('batchProgress')
        };

        // Verificar que todos los elementos críticos existen
        const missingElements = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);

        if (missingElements.length > 0) {
            console.warn('⚠️ Elementos faltantes en DOM:', missingElements);
        }
    }

    /**
     * BIND DE EVENTOS
     */
    bindEvents() {
        // Drag & Drop events
        if (this.elements.dropZone) {
            this.elements.dropZone.addEventListener('dragenter', this.handleDragEnter.bind(this));
            this.elements.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
            this.elements.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
            this.elements.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        }

        // File input
        if (this.elements.fileInput) {
            this.elements.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        // Select button
        if (this.elements.selectButton) {
            this.elements.selectButton.addEventListener('click', this.openFileDialog.bind(this));
        }

        // Process batch button
        if (this.elements.processBatchBtn) {
            this.elements.processBatchBtn.addEventListener('click', this.processBatch.bind(this));
        }

        // MANDATO 15: Nuevos eventos para parámetros individuales
        const generateBatchParamsBtn = document.getElementById('generateBatchParamsBtn');
        if (generateBatchParamsBtn) {
            generateBatchParamsBtn.addEventListener('click', this.generateBatchParameters.bind(this));
        }

        const expandAllBtn = document.getElementById('expandAllBtn');
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', this.expandAllItems.bind(this));
        }

        const collapseAllBtn = document.getElementById('collapseAllBtn');
        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', this.collapseAllItems.bind(this));
        }
    }

    /**
     * DRAG & DROP HANDLERS
     */
    handleDragEnter(e) {
        e.preventDefault();
        this.dragCounter++;
        this.elements.dropZone.classList.add('drag-over');
    }

    handleDragOver(e) {
        e.preventDefault();
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.dragCounter--;
        if (this.dragCounter === 0) {
            this.elements.dropZone.classList.remove('drag-over');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        this.dragCounter = 0;
        this.elements.dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.addFiles(files);
    }

    /**
     * FILE SELECTION HANDLERS
     */
    openFileDialog() {
        if (this.elements.fileInput) {
            this.elements.fileInput.click();
        }
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
        
        // Limpiar input para permitir seleccionar los mismos archivos nuevamente
        e.target.value = '';
    }

    /**
     * AGREGAR ARCHIVOS A LA COLA
     */
    addFiles(files) {
        let validFiles = 0;
        let invalidFiles = 0;

        files.forEach(file => {
            const validation = this.validateFile(file);
            const fileId = this.generateFileId(file);

            if (validation.isValid) {
                this.files.set(fileId, {
                    id: fileId,
                    file: file,
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    status: 'pending', // pending, uploading, uploaded, processing, completed, error
                    progress: 0,
                    addedAt: new Date(),
                    metadata: {},
                    // MANDATO 15: Parámetros individuales por imagen
                    parameters: {
                        numerosorteo: '',
                        idWhatsapp: '',
                        nombre: '',
                        horamin: '',
                        caption: '',
                        fechasorteo: '',
                        profile: 'ultra_rapido',
                        apiKey: '',
                        otro_valor: ''
                    },
                    expanded: false // Para UI colapsable/expandible
                });
                validFiles++;
            } else {
                this.showFileError(file.name, validation.error);
                invalidFiles++;
            }
        });

        // Actualizar UI
        this.updateFileListDisplay();

        // Mostrar notificación de archivos agregados
        if (validFiles > 0) {
            this.showSuccess(`${validFiles} archivo(s) agregado(s) exitosamente`);
        }
        if (invalidFiles > 0) {
            this.showError(`${invalidFiles} archivo(s) no válido(s) rechazado(s)`);
        }
        this.updateProcessButtonState();

        // Mostrar resumen
        if (validFiles > 0) {
            this.showNotification(`✅ ${validFiles} archivo(s) agregado(s) a la cola`, 'success');
        }
        if (invalidFiles > 0) {
            this.showNotification(`⚠️ ${invalidFiles} archivo(s) rechazado(s)`, 'warning');
        }
    }

    /**
     * VALIDACIÓN DE ARCHIVOS
     */
    validateFile(file) {
        // Verificar tipo de archivo
        if (!this.allowedTypes.includes(file.type)) {
            return {
                isValid: false,
                error: `Tipo de archivo no soportado. Use: ${this.allowedTypes.map(t => t.split('/')[1].toUpperCase()).join(', ')}`
            };
        }

        // Verificar tamaño
        if (file.size > this.maxFileSize) {
            const sizeMB = (this.maxFileSize / (1024 * 1024)).toFixed(0);
            return {
                isValid: false,
                error: `Archivo demasiado grande. Máximo: ${sizeMB}MB`
            };
        }

        // Verificar si ya existe
        const existing = Array.from(this.files.values()).find(f => 
            f.name === file.name && f.size === file.size
        );
        if (existing) {
            return {
                isValid: false,
                error: 'Archivo ya agregado a la cola'
            };
        }

        return { isValid: true };
    }

    /**
     * UPLOAD DE ARCHIVOS
     */
    async uploadFiles(metadata = {}) {
        const pendingFiles = Array.from(this.files.values()).filter(f => f.status === 'pending');
        
        if (pendingFiles.length === 0) {
            this.showNotification('⚠️ No hay archivos para subir', 'warning');
            return;
        }

        try {
            // Cambiar estado a uploading
            pendingFiles.forEach(fileData => {
                fileData.status = 'uploading';
                fileData.progress = 0;
            });
            this.updateFileListDisplay();

            // Preparar archivos para upload
            const filesToUpload = pendingFiles.map(f => f.file);
            
            // Simular progreso (el backend no reporta progreso real)
            const progressInterval = setInterval(() => {
                pendingFiles.forEach(fileData => {
                    if (fileData.status === 'uploading' && fileData.progress < 90) {
                        fileData.progress += Math.random() * 15;
                        if (fileData.progress > 90) fileData.progress = 90;
                    }
                });
                this.updateFileListDisplay();
            }, 200);

            // Llamar al backend
            const result = await window.apiClient.uploadFiles(filesToUpload, metadata);

            clearInterval(progressInterval);

            // Procesar respuesta
            if (result.status === 'success') {
                // Actualizar estado de archivos según respuesta
                if (result.results && Array.isArray(result.results)) {
                    result.results.forEach(fileResult => {
                        const fileData = pendingFiles.find(f => 
                            f.name === fileResult.filename_original
                        );
                        if (fileData) {
                            fileData.status = 'uploaded';
                            fileData.progress = 100;
                            fileData.finalFilename = fileResult.filename_final;
                            fileData.metadata = fileResult.metadata || {};
                        }
                    });
                } else {
                    // Fallback: marcar todos como uploaded
                    pendingFiles.forEach(fileData => {
                        fileData.status = 'uploaded';
                        fileData.progress = 100;
                    });
                }

                this.updateFileListDisplay();
                this.updateProcessButtonState();
                this.showNotification(`✅ ${result.uploaded_count} archivo(s) subido(s) exitosamente`, 'success');
                
                return result;
            }

        } catch (error) {
            clearInterval(progressInterval);
            
            // Marcar archivos como error
            pendingFiles.forEach(fileData => {
                fileData.status = 'error';
                fileData.progress = 0;
                fileData.error = error.getUserMessage();
            });
            
            this.updateFileListDisplay();
            this.showNotification(`❌ Error al subir archivos: ${error.getUserMessage()}`, 'error');
            throw error;
        }
    }

    /**
     * PROCESAMIENTO DE LOTE CON PARÁMETROS ESENCIALES
     */
    async processBatch(options = {}) {
        const uploadedFiles = Array.from(this.files.values()).filter(f => f.status === 'uploaded');
        
        if (uploadedFiles.length === 0) {
            this.showNotification('⚠️ No hay archivos subidos para procesar', 'warning');
            return;
        }

        try {
            // Cambiar estado del botón
            this.setProcessButtonLoading(true);

            // Cambiar estado de archivos
            uploadedFiles.forEach(fileData => {
                fileData.status = 'processing';
                fileData.progress = 0;
            });
            this.updateFileListDisplay();

            // Simular progreso de procesamiento
            const progressInterval = setInterval(() => {
                uploadedFiles.forEach(fileData => {
                    if (fileData.status === 'processing' && fileData.progress < 95) {
                        fileData.progress += Math.random() * 10;
                        if (fileData.progress > 95) fileData.progress = 95;
                    }
                });
                this.updateFileListDisplay();
            }, 500);

            // Obtener parámetros esenciales del formulario
            const essentialParams = this.getEssentialParameters();

            // Llamar al backend con parámetros esenciales
            const result = await window.apiClient.processBatch({
                profile: options.profile || 'ultra_rapido',
                batch_size: options.batch_size || uploadedFiles.length,
                ...essentialParams
            });

            clearInterval(progressInterval);

            if (result.status === 'success') {
                // Actualizar estado final
                uploadedFiles.forEach(fileData => {
                    fileData.status = 'completed';
                    fileData.progress = 100;
                    fileData.requestId = result.request_id;
                    fileData.batchId = result.batch_id;
                });

                this.updateFileListDisplay();
                this.setProcessButtonLoading(false);
                this.showNotification(`✅ Lote procesado exitosamente (${result.batch_info.processed_count} archivos)`, 'success');

                // Disparar evento para actualizar dashboard
                this.dispatchBatchCompleted(result);

                return result;
            }

        } catch (error) {
            clearInterval(progressInterval);
            
            // Marcar archivos como error
            uploadedFiles.forEach(fileData => {
                fileData.status = 'error';
                fileData.error = error.getUserMessage();
            });
            
            this.updateFileListDisplay();
            this.setProcessButtonLoading(false);
            this.showNotification(`❌ Error en procesamiento: ${error.getUserMessage()}`, 'error');
            throw error;
        }
    }

    /**
     * REMOVER ARCHIVO DE LA COLA
     */
    removeFile(fileId) {
        const fileData = this.files.get(fileId);
        if (fileData && ['pending', 'error'].includes(fileData.status)) {
            this.files.delete(fileId);
            this.updateFileListDisplay();
            this.updateProcessButtonState();
            this.showNotification(`🗑️ Archivo "${fileData.name}" removido de la cola`, 'info');
        }
    }

    /**
     * LIMPIAR COLA COMPLETA
     */
    clearQueue() {
        const removableFiles = Array.from(this.files.values()).filter(f => 
            ['pending', 'error', 'completed'].includes(f.status)
        );
        
        removableFiles.forEach(fileData => {
            this.files.delete(fileData.id);
        });
        
        this.updateFileListDisplay();
        this.updateProcessButtonState();
        this.showNotification(`🧹 Cola limpiada (${removableFiles.length} archivos removidos)`, 'info');
    }

    /**
     * ACTUALIZAR VISUALIZACIÓN DE LISTA DE ARCHIVOS
     */
    updateFileListDisplay() {
        if (!this.elements.fileListDisplay) return;

        const filesArray = Array.from(this.files.values()).sort((a, b) => b.addedAt - a.addedAt);
        
        if (filesArray.length === 0) {
            this.elements.fileListDisplay.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-upload fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay archivos en la cola</p>
                    <p class="small text-muted">Arrastra archivos aquí o usa el botón "Seleccionar Archivos"</p>
                </div>
            `;
            return;
        }

        const html = `
            <div class="file-list-header d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">Archivos en Cola (${filesArray.length})</h6>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="fileManager.clearQueue()">
                    <i class="fas fa-trash me-1"></i>Limpiar Cola
                </button>
            </div>
            <div class="file-list">
                ${filesArray.map(fileData => this.renderFileItem(fileData)).join('')}
            </div>
        `;

        this.elements.fileListDisplay.innerHTML = html;
    }

    /**
     * RENDER DE UN ITEM DE ARCHIVO
     */
    renderFileItem(fileData) {
        const statusConfig = this.getStatusConfig(fileData.status);
        const sizeFormatted = this.formatFileSize(fileData.size);
        const progressBar = fileData.progress > 0 ? `
            <div class="progress mb-2" style="height: 4px;">
                <div class="progress-bar ${statusConfig.progressClass}" 
                     style="width: ${fileData.progress}%"></div>
            </div>
        ` : '';

        // MANDATO 15: Interfaz de parámetros individuales expandible
        const parametersSection = fileData.expanded ? this.renderParametersSection(fileData) : '';

        return `
            <div class="file-item border rounded mb-2 p-3" data-file-id="${fileData.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="file-info flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <button type="button" class="btn btn-sm btn-outline-secondary me-2" 
                                    onclick="fileManager.toggleFileExpansion('${fileData.id}')" 
                                    title="${fileData.expanded ? 'Colapsar' : 'Expandir'} parámetros">
                                <i class="fas fa-${fileData.expanded ? 'chevron-down' : 'chevron-right'}"></i>
                            </button>
                            <i class="fas fa-file-image text-primary me-2"></i>
                            <span class="file-name fw-medium">${this.escapeHtml(fileData.name)}</span>
                            <span class="badge ${statusConfig.badgeClass} ms-2">${statusConfig.label}</span>
                        </div>
                        <div class="file-meta small text-muted">
                            <span>${sizeFormatted}</span>
                            ${fileData.finalFilename ? `• <span class="text-success">Renombrado</span>` : ''}
                            ${fileData.requestId ? `• <span class="text-info">Lote: ${fileData.requestId.split('_')[2]}</span>` : ''}
                        </div>
                        ${progressBar}
                        ${fileData.error ? `<div class="alert alert-danger alert-sm mt-2 mb-0 py-1 px-2">${this.escapeHtml(fileData.error)}</div>` : ''}
                        ${parametersSection}
                    </div>
                    <div class="file-actions ms-3">
                        ${this.renderFileActions(fileData)}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * MANDATO 15: RENDER DE SECCIÓN DE PARÁMETROS INDIVIDUALES
     */
    renderParametersSection(fileData) {
        const params = fileData.parameters || {};
        
        return `
            <div class="parameters-section mt-3 border-top pt-3">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-cogs me-2"></i>Parámetros Individuales
                </h6>
                <div class="row g-2">
                    <div class="col-md-4">
                        <label class="form-label small">Número Sorteo</label>
                        <input type="text" class="form-control form-control-sm" 
                               value="${params.numerosorteo || ''}" 
                               onchange="fileManager.updateFileParameters('${fileData.id}', {numerosorteo: this.value})"
                               placeholder="Ej: SORT001">
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small">ID WhatsApp</label>
                        <input type="text" class="form-control form-control-sm" 
                               value="${params.idWhatsapp || ''}" 
                               onchange="fileManager.updateFileParameters('${fileData.id}', {idWhatsapp: this.value})"
                               placeholder="Ej: 123@lid">
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small">Nombre Usuario</label>
                        <input type="text" class="form-control form-control-sm" 
                               value="${params.nombre || ''}" 
                               onchange="fileManager.updateFileParameters('${fileData.id}', {nombre: this.value})"
                               placeholder="Ej: Juan Pérez">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Hora y Minuto</label>
                        <input type="text" class="form-control form-control-sm" 
                               value="${params.horamin || ''}" 
                               onchange="fileManager.updateFileParameters('${fileData.id}', {horamin: this.value})"
                               placeholder="Ej: 14:30">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Fecha Sorteo</label>
                        <input type="date" class="form-control form-control-sm" 
                               value="${params.fechasorteo || ''}" 
                               onchange="fileManager.updateFileParameters('${fileData.id}', {fechasorteo: this.value})">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Perfil OCR</label>
                        <select class="form-select form-select-sm" 
                                onchange="fileManager.updateFileParameters('${fileData.id}', {profile: this.value})">
                            <option value="ultra_rapido" ${params.profile === 'ultra_rapido' ? 'selected' : ''}>Ultra Rápido</option>
                            <option value="rapido" ${params.profile === 'rapido' ? 'selected' : ''}>Rápido</option>
                            <option value="balanced" ${params.profile === 'balanced' ? 'selected' : ''}>Balanceado</option>
                            <option value="high_confidence" ${params.profile === 'high_confidence' ? 'selected' : ''}>Alta Confianza</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">API Key</label>
                        <input type="password" class="form-control form-control-sm" 
                               value="${params.apiKey || ''}" 
                               onchange="fileManager.updateFileParameters('${fileData.id}', {apiKey: this.value})"
                               placeholder="Opcional">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small">Caption/Descripción</label>
                        <textarea class="form-control form-control-sm" rows="2" 
                                  onchange="fileManager.updateFileParameters('${fileData.id}', {caption: this.value})"
                                  placeholder="Descripción del archivo...">${params.caption || ''}</textarea>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small">Otro Valor</label>
                        <textarea class="form-control form-control-sm" rows="2" 
                                  onchange="fileManager.updateFileParameters('${fileData.id}', {otro_valor: this.value})"
                                  placeholder="Información adicional...">${params.otro_valor || ''}</textarea>
                    </div>
                </div>
                <div class="mt-3">
                    <button type="button" class="btn btn-sm btn-primary" 
                            onclick="fileManager.autoGenerateFileParameters('${fileData.id}')">
                        <i class="fas fa-magic me-1"></i>Auto-Generar
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary ms-2" 
                            onclick="fileManager.copyParametersFromGlobal('${fileData.id}')">
                        <i class="fas fa-copy me-1"></i>Copiar Globales
                    </button>
                    <button type="button" class="btn btn-sm btn-warning ms-2" 
                            onclick="fileManager.clearFileParameters('${fileData.id}')">
                        <i class="fas fa-eraser me-1"></i>Limpiar
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * RENDER DE ACCIONES DE ARCHIVO
     */
    renderFileActions(fileData) {
        switch (fileData.status) {
            case 'pending':
            case 'error':
                return `<button type="button" class="btn btn-sm btn-outline-danger" 
                               onclick="fileManager.removeFile('${fileData.id}')" title="Remover archivo">
                            <i class="fas fa-times"></i>
                        </button>`;
            case 'completed':
                return `<button type="button" class="btn btn-sm btn-outline-primary" 
                               onclick="resultsViewer.viewFileDetails('${fileData.finalFilename || fileData.name}')" 
                               title="Ver detalles">
                            <i class="fas fa-eye"></i>
                        </button>`;
            default:
                return '<span class="text-muted">—</span>';
        }
    }

    /**
     * CONFIGURACIÓN DE ESTADOS
     */
    getStatusConfig(status) {
        const configs = {
            pending: { label: 'Pendiente', badgeClass: 'bg-secondary', progressClass: 'bg-secondary' },
            uploading: { label: 'Subiendo...', badgeClass: 'bg-primary', progressClass: 'bg-primary' },
            uploaded: { label: 'Subido', badgeClass: 'bg-info', progressClass: 'bg-info' },
            processing: { label: 'Procesando...', badgeClass: 'bg-warning', progressClass: 'bg-warning' },
            completed: { label: 'Completado', badgeClass: 'bg-success', progressClass: 'bg-success' },
            error: { label: 'Error', badgeClass: 'bg-danger', progressClass: 'bg-danger' }
        };
        return configs[status] || configs.pending;
    }

    /**
     * ACTUALIZAR ESTADO DEL BOTÓN DE PROCESAMIENTO
     */
    updateProcessButtonState() {
        if (!this.elements.processBatchBtn) return;

        const uploadedFiles = Array.from(this.files.values()).filter(f => f.status === 'uploaded');
        const isDisabled = uploadedFiles.length === 0;

        this.elements.processBatchBtn.disabled = isDisabled;
        
        if (isDisabled) {
            this.elements.processBatchBtn.innerHTML = '<i class="fas fa-cog me-2"></i>Procesar Lote';
            this.elements.processBatchBtn.className = 'btn btn-primary';
        } else {
            this.elements.processBatchBtn.innerHTML = `<i class="fas fa-cog me-2"></i>Procesar Lote (${uploadedFiles.length})`;
            this.elements.processBatchBtn.className = 'btn btn-success';
        }
    }

    /**
     * ESTADO DE CARGA DEL BOTÓN DE PROCESAMIENTO
     */
    setProcessButtonLoading(loading) {
        if (!this.elements.processBatchBtn) return;

        if (loading) {
            this.elements.processBatchBtn.disabled = true;
            this.elements.processBatchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
        } else {
            this.updateProcessButtonState();
        }
    }

    /**
     * UTILIDADES
     */
    generateFileId(file) {
        return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * NOTIFICACIONES
     */
    showNotification(message, type = 'info', duration = 5000) {
        // Dispatch evento para que el main.js maneje las notificaciones
        window.dispatchEvent(new CustomEvent('showNotification', {
            detail: { message, type, duration }
        }));
    }

    showFileError(filename, error) {
        this.showNotification(`❌ ${filename}: ${error}`, 'error');
    }

    /**
     * EVENTOS PERSONALIZADOS
     */
    dispatchBatchCompleted(result) {
        window.dispatchEvent(new CustomEvent('batchCompleted', {
            detail: result
        }));
    }

    /**
     * OBTENER PARÁMETROS ESENCIALES DEL FORMULARIO
     */
    getEssentialParameters() {
        const params = {};
        
        // Obtener valores de los campos
        const codigoSorteo = document.getElementById('codigoSorteo')?.value.trim();
        const idWhatsapp = document.getElementById('idWhatsapp')?.value.trim();
        const nombreUsuario = document.getElementById('nombreUsuario')?.value.trim();
        const captionTexto = document.getElementById('captionTexto')?.value.trim();
        const horaExacta = document.getElementById('horaExacta')?.value.trim();
        const apiKey = document.getElementById('apiKey')?.value.trim();
        
        // Incluir solo parámetros no vacíos
        if (codigoSorteo) params.codigo_sorteo = codigoSorteo;
        if (idWhatsapp) params.id_whatsapp = idWhatsapp;
        if (nombreUsuario) params.nombre_usuario = nombreUsuario;
        if (captionTexto) params.caption = captionTexto;
        if (horaExacta) params.hora_exacta = horaExacta;
        if (apiKey) params.api_key = apiKey;
        
        return params;
    }

    /**
     * OBTENER ESTADÍSTICAS
     */
    getStats() {
        const filesArray = Array.from(this.files.values());
        const stats = {
            total: filesArray.length,
            pending: 0,
            uploading: 0,
            uploaded: 0,
            processing: 0,
            completed: 0,
            error: 0
        };
        
        filesArray.forEach(file => {
            if (stats.hasOwnProperty(file.status)) {
                stats[file.status]++;
            }
        });
        
        return stats;
    }

    /**
     * MANDATO 15: MÉTODOS PARA PARÁMETROS INDIVIDUALES POR IMAGEN
     */
    
    /**
     * GENERAR PARÁMETROS AUTOMÁTICAMENTE PARA LOTE
     */
    generateBatchParameters() {
        const files = Array.from(this.files.values());
        const baseParams = this.getEssentialParameters();
        
        let counter = 1;
        files.forEach(fileData => {
            // Generar parámetros únicos para cada archivo
            fileData.parameters = {
                numerosorteo: baseParams.codigo_sorteo || `SORT${counter.toString().padStart(3, '0')}`,
                idWhatsapp: baseParams.id_whatsapp || `${counter}@lid`,
                nombre: baseParams.nombre_usuario || `Usuario${counter}`,
                horamin: baseParams.hora_exacta || this.getCurrentTime(),
                caption: baseParams.caption || `Imagen procesada ${counter}`,
                fechasorteo: this.getCurrentDate(),
                profile: 'ultra_rapido',
                apiKey: baseParams.api_key || '',
                otro_valor: `Valor${counter}`
            };
            counter++;
        });
        
        this.updateFileListDisplay();
        this.showNotification(`✅ Parámetros generados automáticamente para ${files.length} archivo(s)`, 'success');
    }

    /**
     * EXPANDIR TODOS LOS ELEMENTOS DE ARCHIVO
     */
    expandAllItems() {
        const files = Array.from(this.files.values());
        files.forEach(fileData => {
            fileData.expanded = true;
        });
        this.updateFileListDisplay();
        this.showNotification(`📂 Todos los archivos expandidos`, 'info');
    }

    /**
     * COLAPSAR TODOS LOS ELEMENTOS DE ARCHIVO
     */
    collapseAllItems() {
        const files = Array.from(this.files.values());
        files.forEach(fileData => {
            fileData.expanded = false;
        });
        this.updateFileListDisplay();
        this.showNotification(`📁 Todos los archivos colapsados`, 'info');
    }

    /**
     * ALTERNAR EXPANSIÓN DE UN ARCHIVO ESPECÍFICO
     */
    toggleFileExpansion(fileId) {
        const fileData = this.files.get(fileId);
        if (fileData) {
            fileData.expanded = !fileData.expanded;
            this.updateFileListDisplay();
        }
    }

    /**
     * ACTUALIZAR PARÁMETROS DE UN ARCHIVO ESPECÍFICO
     */
    updateFileParameters(fileId, parameters) {
        const fileData = this.files.get(fileId);
        if (fileData) {
            fileData.parameters = { ...fileData.parameters, ...parameters };
            this.showNotification(`✅ Parámetros actualizados para ${fileData.name}`, 'success');
        }
    }

    /**
     * OBTENER PARÁMETROS CONSOLIDADOS PARA PROCESAMIENTO
     */
    getConsolidatedParameters() {
        const files = Array.from(this.files.values()).filter(f => f.status === 'uploaded');
        const consolidatedParams = {};
        
        files.forEach(fileData => {
            if (fileData.finalFilename) {
                consolidatedParams[fileData.finalFilename] = fileData.parameters;
            }
        });
        
        return consolidatedParams;
    }

    /**
     * UTILIDADES DE FECHA Y HORA
     */
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    }

    getCurrentDate() {
        const now = new Date();
        return now.toLocaleDateString('es-ES', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit' 
        });
    }

    /**
     * PROCESAMIENTO DE LOTE CON PARÁMETROS INDIVIDUALES
     */
    async processBatchWithIndividualParameters(options = {}) {
        const uploadedFiles = Array.from(this.files.values()).filter(f => f.status === 'uploaded');
        
        if (uploadedFiles.length === 0) {
            this.showNotification('⚠️ No hay archivos subidos para procesar', 'warning');
            return;
        }

        try {
            // Obtener parámetros consolidados
            const consolidatedParams = this.getConsolidatedParameters();
            
            // Cambiar estado del botón
            this.setProcessButtonLoading(true);

            // Cambiar estado de archivos
            uploadedFiles.forEach(fileData => {
                fileData.status = 'processing';
                fileData.progress = 0;
            });
            this.updateFileListDisplay();

            // Simular progreso de procesamiento
            const progressInterval = setInterval(() => {
                uploadedFiles.forEach(fileData => {
                    if (fileData.status === 'processing' && fileData.progress < 95) {
                        fileData.progress += Math.random() * 10;
                        if (fileData.progress > 95) fileData.progress = 95;
                    }
                });
                this.updateFileListDisplay();
            }, 500);

            // Llamar al backend con parámetros individuales
            const result = await window.apiClient.processBatchWithParameters({
                profile: options.profile || 'ultra_rapido',
                batch_size: options.batch_size || uploadedFiles.length,
                individual_parameters: consolidatedParams,
                ...this.getEssentialParameters()
            });

            clearInterval(progressInterval);

            if (result.status === 'success') {
                // Actualizar estado final
                uploadedFiles.forEach(fileData => {
                    fileData.status = 'completed';
                    fileData.progress = 100;
                    fileData.requestId = result.request_id;
                    fileData.batchId = result.batch_id;
                });

                this.updateFileListDisplay();
                this.setProcessButtonLoading(false);
                this.showNotification(`✅ Lote procesado exitosamente con parámetros individuales (${result.batch_info.processed_count} archivos)`, 'success');

                // Disparar evento para actualizar dashboard
                this.dispatchBatchCompleted(result);

                return result;
            }

        } catch (error) {
            clearInterval(progressInterval);
            
            // Marcar archivos como error
            uploadedFiles.forEach(fileData => {
                fileData.status = 'error';
                fileData.error = error.getUserMessage();
            });
            
            this.updateFileListDisplay();
            this.setProcessButtonLoading(false);
            this.showNotification(`❌ Error en procesamiento: ${error.getUserMessage()}`, 'error');
            throw error;
        }
    }

    /**
     * MANDATO 15: MÉTODOS AUXILIARES PARA PARÁMETROS INDIVIDUALES
     */
    
    /**
     * AUTO-GENERAR PARÁMETROS PARA UN ARCHIVO ESPECÍFICO
     */
    autoGenerateFileParameters(fileId) {
        const fileData = this.files.get(fileId);
        if (!fileData) return;

        const now = new Date();
        const timestamp = now.getTime();
        const baseParams = this.getEssentialParameters();
        
        // Generar parámetros únicos basados en el archivo
        const autoParams = {
            numerosorteo: baseParams.codigo_sorteo || `SORT${timestamp.toString().slice(-4)}`,
            idWhatsapp: baseParams.id_whatsapp || `${timestamp.toString().slice(-6)}@lid`,
            nombre: baseParams.nombre_usuario || `Usuario_${fileData.name.split('.')[0]}`,
            horamin: this.getCurrentTime(),
            caption: `Procesamiento automático de ${fileData.name}`,
            fechasorteo: this.getCurrentDate(),
            profile: 'ultra_rapido',
            apiKey: baseParams.api_key || '',
            otro_valor: `Auto-generado: ${now.toISOString()}`
        };

        this.updateFileParameters(fileId, autoParams);
        this.showNotification(`✨ Parámetros auto-generados para ${fileData.name}`, 'success');
    }

    /**
     * COPIAR PARÁMETROS GLOBALES A UN ARCHIVO ESPECÍFICO
     */
    copyParametersFromGlobal(fileId) {
        const fileData = this.files.get(fileId);
        if (!fileData) return;

        const globalParams = this.getEssentialParameters();
        const mappedParams = {
            numerosorteo: globalParams.codigo_sorteo || '',
            idWhatsapp: globalParams.id_whatsapp || '',
            nombre: globalParams.nombre_usuario || '',
            horamin: globalParams.hora_exacta || '',
            caption: globalParams.caption || '',
            fechasorteo: this.getCurrentDate(),
            profile: 'ultra_rapido',
            apiKey: globalParams.api_key || '',
            otro_valor: ''
        };

        this.updateFileParameters(fileId, mappedParams);
        this.showNotification(`📋 Parámetros globales copiados a ${fileData.name}`, 'success');
    }

    /**
     * LIMPIAR PARÁMETROS DE UN ARCHIVO ESPECÍFICO
     */
    clearFileParameters(fileId) {
        const fileData = this.files.get(fileId);
        if (!fileData) return;

        const clearedParams = {
            numerosorteo: '',
            idWhatsapp: '',
            nombre: '',
            horamin: '',
            caption: '',
            fechasorteo: '',
            profile: 'ultra_rapido',
            apiKey: '',
            otro_valor: ''
        };

        this.updateFileParameters(fileId, clearedParams);
        this.showNotification(`🧹 Parámetros limpiados para ${fileData.name}`, 'info');
    }

    /**
     * EXPORTAR CONFIGURACIÓN DE PARÁMETROS
     */
    exportParametersConfiguration() {
        const files = Array.from(this.files.values());
        const config = {
            timestamp: new Date().toISOString(),
            global_parameters: this.getEssentialParameters(),
            file_parameters: {}
        };

        files.forEach(fileData => {
            if (fileData.parameters) {
                config.file_parameters[fileData.name] = fileData.parameters;
            }
        });

        // Crear y descargar archivo JSON
        const dataStr = JSON.stringify(config, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `parametros_ocr_${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        this.showNotification(`📥 Configuración exportada: ${exportFileDefaultName}`, 'success');
    }

    /**
     * IMPORTAR CONFIGURACIÓN DE PARÁMETROS
     */
    importParametersConfiguration(fileContent) {
        try {
            const config = JSON.parse(fileContent);
            
            if (config.file_parameters) {
                // Aplicar parámetros a archivos existentes
                const files = Array.from(this.files.values());
                let appliedCount = 0;
                
                files.forEach(fileData => {
                    if (config.file_parameters[fileData.name]) {
                        fileData.parameters = { ...fileData.parameters, ...config.file_parameters[fileData.name] };
                        appliedCount++;
                    }
                });
                
                this.updateFileListDisplay();
                this.showNotification(`📤 Configuración importada: ${appliedCount} archivo(s) actualizados`, 'success');
            }
        } catch (error) {
            this.showNotification(`❌ Error al importar configuración: ${error.message}`, 'error');
        }
    }

    /**
     * VALIDAR PARÁMETROS ANTES DE PROCESAMIENTO
     */
    validateAllParameters() {
        const files = Array.from(this.files.values()).filter(f => f.status === 'uploaded');
        const validationResults = [];
        
        files.forEach(fileData => {
            const params = fileData.parameters || {};
            const validation = {
                filename: fileData.name,
                valid: true,
                errors: []
            };
            
            // Validaciones básicas
            if (!params.numerosorteo) validation.errors.push('Número de sorteo requerido');
            if (!params.idWhatsapp) validation.errors.push('ID WhatsApp requerido');
            if (!params.nombre) validation.errors.push('Nombre de usuario requerido');
            
            // Validaciones de formato
            if (params.idWhatsapp && !params.idWhatsapp.includes('@')) {
                validation.errors.push('ID WhatsApp debe contener @');
            }
            
            if (params.horamin && !/^\d{2}:\d{2}$/.test(params.horamin)) {
                validation.errors.push('Hora debe tener formato HH:MM');
            }
            
            validation.valid = validation.errors.length === 0;
            validationResults.push(validation);
        });
        
        return validationResults;
    }

    /**
     * MOSTRAR RESUMEN DE VALIDACIÓN
     */
    showValidationSummary() {
        const validationResults = this.validateAllParameters();
        const validFiles = validationResults.filter(r => r.valid);
        const invalidFiles = validationResults.filter(r => !r.valid);
        
        if (invalidFiles.length === 0) {
            this.showNotification(`✅ Todos los archivos (${validFiles.length}) tienen parámetros válidos`, 'success');
        } else {
            const errorDetails = invalidFiles.map(r => `${r.filename}: ${r.errors.join(', ')}`).join('\n');
            this.showNotification(`⚠️ ${invalidFiles.length} archivo(s) con errores:\n${errorDetails}`, 'warning');
        }
        
        return validationResults;
    }

    /**
     * APLICAR PARÁMETROS EN LOTE
     */
    applyBatchParameters(template) {
        const files = Array.from(this.files.values());
        let counter = 1;
        
        files.forEach(fileData => {
            const batchParams = { ...template };
            
            // Personalizar parámetros con numeración
            if (batchParams.numerosorteo) {
                batchParams.numerosorteo = `${batchParams.numerosorteo}_${counter.toString().padStart(3, '0')}`;
            }
            if (batchParams.idWhatsapp && !batchParams.idWhatsapp.includes('@')) {
                batchParams.idWhatsapp = `${counter}${batchParams.idWhatsapp}@lid`;
            }
            if (batchParams.nombre) {
                batchParams.nombre = `${batchParams.nombre}_${counter}`;
            }
            
            fileData.parameters = { ...fileData.parameters, ...batchParams };
            counter++;
        });
        
        this.updateFileListDisplay();
        this.showNotification(`📋 Parámetros aplicados en lote a ${files.length} archivo(s)`, 'success');
    }
}

// Instancia global del file manager
window.fileManager = new FileManager();