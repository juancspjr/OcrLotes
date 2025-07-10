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
                    metadata: {}
                });
                validFiles++;
            } else {
                this.showFileError(file.name, validation.error);
                invalidFiles++;
            }
        });

        // Actualizar UI
        this.updateFileListDisplay();
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

        return `
            <div class="file-item border rounded mb-2 p-3" data-file-id="${fileData.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="file-info flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
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
                    </div>
                    <div class="file-actions ms-3">
                        ${this.renderFileActions(fileData)}
                    </div>
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
            stats[file.status] = (stats[file.status] || 0) + 1;
        });

        return stats;
    }
}

// Instancia global del file manager
window.fileManager = new FileManager();