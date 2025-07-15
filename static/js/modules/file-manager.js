/**
 * FILE MANAGER MODULE - SISTEMA OCR EMPRESARIAL
 * FILOSOFÍA: INTEGRIDAD TOTAL + INTERFACE EXCELLENCE
 * 
 * Módulo encargado de gestionar la subida, configuración y procesamiento
 * de archivos con parámetros individuales según el mandato especificado.
 */

window.OCRSystem = window.OCRSystem || {};

(function() {
    'use strict';

    class FileManager {
        constructor(config) {
            this.config = config;
            this.apiClient = config.apiClient;
            this.files = new Map();
            this.fileCounter = 0;
            this.isProcessingFiles = false;
            
            // Referencias DOM
            this.dropArea = document.getElementById(config.dropAreaId);
            this.fileInput = document.getElementById(config.fileInputId);
            this.fileList = document.getElementById(config.fileListId);
            
            this.init();
        }

        init() {
            this.setupDropArea();
            this.setupFileInput();
            this.updateDisplay();
            console.log('📁 File Manager inicializado');
        }

        /**
         * Configurar área de drop
         */
        setupDropArea() {
            if (!this.dropArea) return;

            // Prevenir comportamiento por defecto
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                this.dropArea.addEventListener(eventName, this.preventDefaults.bind(this), false);
            });

            // Efectos visuales para drag & drop
            ['dragenter', 'dragover'].forEach(eventName => {
                this.dropArea.addEventListener(eventName, this.highlight.bind(this), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                this.dropArea.addEventListener(eventName, this.unhighlight.bind(this), false);
            });

            // Manejar drop
            this.dropArea.addEventListener('drop', this.handleDrop.bind(this), false);
            
            // Click en área de drop
            this.dropArea.addEventListener('click', () => {
                if (this.fileInput) {
                    this.fileInput.click();
                }
            });
        }

        /**
         * Configurar input de archivos
         */
        setupFileInput() {
            if (!this.fileInput) return;

            // Crear función handler para poder removerla después
            this.fileInputHandler = (e) => {
                // Prevenir múltiples ejecuciones
                if (this.isProcessingFiles) {
                    console.log('⚠️ Ya se está procesando archivo, ignorando...');
                    return;
                }
                
                this.isProcessingFiles = true;
                
                try {
                    this.handleFiles(Array.from(e.target.files));
                } finally {
                    // Limpiar input para permitir seleccionar el mismo archivo
                    e.target.value = '';
                    
                    // Permitir nuevas selecciones después de un breve delay
                    setTimeout(() => {
                        this.isProcessingFiles = false;
                    }, 500);
                }
            };
            
            this.fileInput.addEventListener('change', this.fileInputHandler);
        }

        /**
         * Prevenir comportamiento por defecto
         */
        preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        /**
         * Resaltar área de drop
         */
        highlight() {
            this.dropArea.classList.add('drag-over');
        }

        /**
         * Quitar resaltado del área de drop
         */
        unhighlight() {
            this.dropArea.classList.remove('drag-over');
        }

        /**
         * Manejar drop de archivos
         */
        handleDrop(e) {
            const dt = e.dataTransfer;
            const files = Array.from(dt.files);
            this.handleFiles(files);
        }

        /**
         * Manejar archivos seleccionados
         */
        handleFiles(files) {
            console.log(`📁 Procesando ${files.length} archivo(s)...`);
            
            const validFiles = this.validateFiles(files);
            if (validFiles.length === 0) {
                this.showError('No se encontraron archivos válidos para procesar');
                return;
            }

            validFiles.forEach(file => this.addFile(file));
            this.updateDisplay();
            this.updateCounters();
            
            // Mostrar notificación
            if (window.OCRSystem.Main) {
                window.OCRSystem.Main.showNotification(
                    `${validFiles.length} archivo(s) agregado(s) exitosamente`,
                    'success'
                );
            }
        }

        /**
         * Validar archivos
         */
        validateFiles(files) {
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            
            return files.filter(file => {
                // Validar tipo
                if (!allowedTypes.includes(file.type)) {
                    console.warn(`⚠️ Archivo rechazado (tipo no válido): ${file.name}`);
                    return false;
                }
                
                // Validar tamaño
                if (file.size > maxSize) {
                    console.warn(`⚠️ Archivo rechazado (muy grande): ${file.name}`);
                    return false;
                }
                
                // Validar que no esté duplicado
                const existingFile = Array.from(this.files.values()).find(f => 
                    f.file.name === file.name && f.file.size === file.size
                );
                
                if (existingFile) {
                    console.warn(`⚠️ Archivo duplicado: ${file.name}`);
                    return false;
                }
                
                return true;
            });
        }

        /**
         * Agregar archivo al sistema
         */
        addFile(file) {
            const fileId = `file_${++this.fileCounter}_${Date.now()}`;
            const numeroLlegada = this.files.size + 1;
            
            const fileData = {
                id: fileId,
                file: file,
                status: 'ready',
                expanded: false,
                parameters: {
                    codigo_sorteo: '',
                    id_whatsapp: '',
                    nombre_usuario: '',
                    caption: '',
                    hora_exacta: '',
                    numero_llegada: numeroLlegada
                },
                metadata: {
                    size: file.size,
                    type: file.type,
                    lastModified: file.lastModified,
                    addedAt: Date.now()
                }
            };

            this.files.set(fileId, fileData);
            console.log(`📁 Archivo agregado: ${file.name} (ID: ${fileId})`);
        }

        /**
         * Remover archivo
         */
        removeFile(fileId) {
            if (this.files.has(fileId)) {
                const fileData = this.files.get(fileId);
                this.files.delete(fileId);
                console.log(`🗑️ Archivo removido: ${fileData.file.name}`);
                
                // Reordenar números de llegada
                this.reorderFiles();
                this.updateDisplay();
                this.updateCounters();
                
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        `Archivo "${fileData.file.name}" removido`,
                        'info'
                    );
                }
            }
        }

        /**
         * Reordenar números de llegada después de remover archivo
         */
        reorderFiles() {
            let counter = 1;
            this.files.forEach(fileData => {
                fileData.parameters.numero_llegada = counter++;
            });
        }

        /**
         * Expandir parámetros de archivo
         */
        expandFile(fileId) {
            if (this.files.has(fileId)) {
                const fileData = this.files.get(fileId);
                fileData.expanded = !fileData.expanded;
                this.updateDisplay();
            }
        }

        /**
         * Expandir todos los archivos
         */
        expandAll() {
            this.files.forEach(fileData => {
                fileData.expanded = true;
            });
            this.updateDisplay();
        }

        /**
         * Colapsar todos los archivos
         */
        collapseAll() {
            this.files.forEach(fileData => {
                fileData.expanded = false;
            });
            this.updateDisplay();
        }

        /**
         * Actualizar parámetros de archivo
         */
        updateFileParameter(fileId, paramName, value) {
            if (this.files.has(fileId)) {
                const fileData = this.files.get(fileId);
                fileData.parameters[paramName] = value;
                
                // Marcar como configurado si tiene parámetros
                const hasParams = Object.values(fileData.parameters).some(v => v && v !== '');
                fileData.status = hasParams ? 'configured' : 'ready';
                
                console.log(`📝 Parámetro actualizado: ${fileId}.${paramName} = ${value}`);
            }
        }

        /**
         * Aplicar parámetros a todo el lote
         */
        applyBatchParameters(batchParams) {
            const codigoLetras = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
            let codigoIndex = 0;
            
            this.files.forEach((fileData, index) => {
                // Aplicar código de sorteo (secuencial si no se especifica)
                if (batchParams.codigo_sorteo) {
                    fileData.parameters.codigo_sorteo = batchParams.codigo_sorteo;
                } else {
                    fileData.parameters.codigo_sorteo = codigoLetras[codigoIndex % codigoLetras.length];
                    codigoIndex++;
                }
                
                // Aplicar otros parámetros
                fileData.parameters.id_whatsapp = batchParams.id_whatsapp || this.generateWhatsAppId();
                fileData.parameters.nombre_usuario = batchParams.nombre_usuario || this.generateRandomName();
                fileData.parameters.caption = batchParams.caption || 'Pago Móvil';
                fileData.parameters.hora_exacta = batchParams.hora_exacta || this.generateRandomTime();
                
                // Marcar como configurado
                fileData.status = 'configured';
            });
            
            this.updateDisplay();
            console.log('📋 Parámetros de lote aplicados a todos los archivos');
        }

        /**
         * Generar ID de WhatsApp aleatorio
         */
        generateWhatsAppId() {
            const randomNum = Math.floor(Math.random() * 900000000) + 100000000;
            return `${randomNum}@lid`;
        }

        /**
         * Generar nombre aleatorio
         */
        generateRandomName() {
            const nombres = ['Ana', 'Carlos', 'María', 'Juan', 'Sofía', 'Pedro', 'Laura', 'Miguel', 'Carmen', 'José'];
            return nombres[Math.floor(Math.random() * nombres.length)];
        }

        /**
         * Generar hora aleatoria
         */
        generateRandomTime() {
            const hours = Math.floor(Math.random() * 24).toString().padStart(2, '0');
            const minutes = Math.floor(Math.random() * 60).toString().padStart(2, '0');
            return `${hours}-${minutes}`;
        }

        /**
         * Procesar lote de archivos
         */
        async processBatch(profile = 'ultra_rapido') {
            if (this.files.size === 0) {
                throw new Error('No hay archivos para procesar');
            }

            // Prevenir doble procesamiento
            if (this.isProcessing) {
                console.warn('⚠️ Ya hay un procesamiento en curso, ignorando duplicado');
                return;
            }
            
            this.isProcessing = true;
            
            // Preparar archivos para procesamiento
            const filesToProcess = Array.from(this.files.values());
            
            try {
                console.log(`🚀 Iniciando procesamiento de ${filesToProcess.length} archivos...`);
                
                // Generar ID único para el lote
                const batchId = this.generateBatchId();
                console.log(`📋 ID del lote: ${batchId}`);
                
                // Marcar archivos como procesando
                filesToProcess.forEach(fileData => {
                    fileData.status = 'processing';
                    fileData.batchId = batchId;
                });
                this.updateDisplay();
                
                // Procesar a través del API Client
                const result = await this.apiClient.processBatch(filesToProcess, profile);
                
                // Actualizar estado según resultado
                if (result && (result.status === 'exitoso' || result.status === 'success')) {
                    filesToProcess.forEach(fileData => {
                        fileData.status = 'processed';
                    });
                    
                    console.log(`✅ Lote ${batchId} procesado exitosamente`);
                    
                    // Limpiar archivos después del procesamiento exitoso
                    setTimeout(() => {
                        this.files.clear();
                        this.updateDisplay();
                        this.updateCounters();
                    }, 2000);
                } else {
                    // Marcar como error
                    filesToProcess.forEach(fileData => {
                        fileData.status = 'error';
                    });
                    this.updateDisplay();
                }
                
                return result;
                
            } catch (error) {
                // Marcar archivos como error
                filesToProcess.forEach(fileData => {
                    fileData.status = 'error';
                });
                this.updateDisplay();
                
                console.error('❌ Error procesando lote:', error);
                throw error;
            } finally {
                this.isProcessing = false;
            }
        }

        /**
         * Generar ID único para el lote
         */
        generateBatchId() {
            const now = new Date();
            const timestamp = now.toISOString().replace(/[^\d]/g, '').slice(0, 14); // YYYYMMDDHHMMSS
            const random = Math.random().toString(36).substr(2, 8);
            return `BATCH_${timestamp}_${random}`;
        }

        /**
         * Actualizar visualización de la lista de archivos
         */
        updateDisplay() {
            if (!this.fileList) return;

            if (this.files.size === 0) {
                this.fileList.innerHTML = `
                    <tr id="emptyFileListMessage">
                        <td colspan="4" class="text-center text-muted py-5">
                            <i class="fas fa-inbox fa-2x mb-2"></i><br>
                            No hay archivos en cola
                        </td>
                    </tr>
                `;
                return;
            }

            const filesArray = Array.from(this.files.values());
            let html = '';

            filesArray.forEach(fileData => {
                html += this.renderFileRow(fileData);
                if (fileData.expanded) {
                    html += this.renderParametersRow(fileData);
                }
            });

            this.fileList.innerHTML = html;
            this.attachEventListeners();
        }

        /**
         * Renderizar fila de archivo
         */
        renderFileRow(fileData) {
            const statusClass = this.getStatusClass(fileData.status);
            const statusIcon = this.getStatusIcon(fileData.status);
            const expandIcon = fileData.expanded ? 'fa-chevron-down' : 'fa-chevron-right';

            return `
                <tr class="file-item ${fileData.expanded ? 'expanded' : ''}" data-file-id="${fileData.id}">
                    <td>
                        <div class="numero-llegada">${fileData.parameters.numero_llegada}</div>
                    </td>
                    <td>
                        <div class="d-flex align-items-center">
                            <i class="fas ${expandIcon} expand-indicator me-2 ${fileData.expanded ? 'expanded' : ''}" 
                               data-file-id="${fileData.id}" style="cursor: pointer;"></i>
                            <div>
                                <div class="fw-medium">${this.truncateFilename(fileData.file.name)}</div>
                                <small class="text-muted">${this.formatFileSize(fileData.file.size)}</small>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="file-status ${statusClass}">
                            <i class="fas ${statusIcon}"></i>
                            ${this.getStatusText(fileData.status)}
                        </span>
                    </td>
                    <td>
                        <button type="button" class="btn btn-sm btn-outline-danger remove-file-btn" 
                                data-file-id="${fileData.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }

        /**
         * Renderizar fila de parámetros
         */
        renderParametersRow(fileData) {
            return `
                <tr class="file-params-row show" data-file-id="${fileData.id}">
                    <td colspan="4">
                        <div class="file-params-content">
                            <div class="mb-2">
                                <strong><i class="fas fa-file me-1"></i>Archivo:</strong> 
                                <span class="text-muted">${fileData.file.name}</span>
                            </div>
                            <form class="params-form">
                                <div class="param-group">
                                    <label for="codigo_sorteo_${fileData.id}">Código de Sorteo</label>
                                    <select class="form-select param-input" 
                                            id="codigo_sorteo_${fileData.id}"
                                            data-file-id="${fileData.id}"
                                            data-param="codigo_sorteo">
                                        <option value="">Seleccionar...</option>
                                        ${['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'].map(letra => 
                                            `<option value="${letra}" ${fileData.parameters.codigo_sorteo === letra ? 'selected' : ''}>${letra}</option>`
                                        ).join('')}
                                    </select>
                                </div>
                                <div class="param-group">
                                    <label for="id_whatsapp_${fileData.id}">ID de WhatsApp</label>
                                    <input type="text" class="form-control param-input" 
                                           id="id_whatsapp_${fileData.id}"
                                           data-file-id="${fileData.id}"
                                           data-param="id_whatsapp"
                                           placeholder="123456789@lid"
                                           value="${fileData.parameters.id_whatsapp}">
                                </div>
                                <div class="param-group">
                                    <label for="nombre_usuario_${fileData.id}">Nombre de Usuario</label>
                                    <input type="text" class="form-control param-input" 
                                           id="nombre_usuario_${fileData.id}"
                                           data-file-id="${fileData.id}"
                                           data-param="nombre_usuario"
                                           placeholder="Juan"
                                           value="${fileData.parameters.nombre_usuario}">
                                </div>
                                <div class="param-group">
                                    <label for="caption_${fileData.id}">Caption</label>
                                    <input type="text" class="form-control param-input" 
                                           id="caption_${fileData.id}"
                                           data-file-id="${fileData.id}"
                                           data-param="caption"
                                           placeholder="Pago Móvil"
                                           value="${fileData.parameters.caption}">
                                </div>
                                <div class="param-group">
                                    <label for="hora_exacta_${fileData.id}">Hora Exacta</label>
                                    <input type="text" class="form-control param-input" 
                                           id="hora_exacta_${fileData.id}"
                                           data-file-id="${fileData.id}"
                                           data-param="hora_exacta"
                                           placeholder="14-30"
                                           pattern="[0-9]{2}-[0-9]{2}"
                                           value="${fileData.parameters.hora_exacta}">
                                </div>
                                <div class="param-group">
                                    <label>Número de Llegada</label>
                                    <input type="text" class="form-control" 
                                           value="${fileData.parameters.numero_llegada}"
                                           readonly>
                                    <small class="text-muted">Auto-generado según orden de subida</small>
                                </div>
                            </form>
                            <div class="param-actions">
                                <div class="btn-group">
                                    <button type="button" class="btn btn-sm btn-outline-primary auto-generate-btn" 
                                            data-file-id="${fileData.id}">
                                        <i class="fas fa-magic me-1"></i>Auto-generar
                                    </button>
                                    <button type="button" class="btn btn-sm btn-outline-secondary clear-params-btn" 
                                            data-file-id="${fileData.id}">
                                        <i class="fas fa-eraser me-1"></i>Limpiar
                                    </button>
                                </div>
                                <button type="button" class="btn btn-sm btn-outline-success copy-filename-btn" 
                                        data-file-id="${fileData.id}">
                                    <i class="fas fa-copy me-1"></i>Copiar Nombre
                                </button>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }

        /**
         * Adjuntar event listeners después de renderizar
         */
        attachEventListeners() {
            // Expandir/colapsar archivos
            document.querySelectorAll('.expand-indicator').forEach(el => {
                el.addEventListener('click', (e) => {
                    const fileId = e.target.getAttribute('data-file-id');
                    this.expandFile(fileId);
                });
            });

            // Remover archivos
            document.querySelectorAll('.remove-file-btn').forEach(el => {
                el.addEventListener('click', (e) => {
                    const fileId = e.target.closest('.remove-file-btn').getAttribute('data-file-id');
                    this.removeFile(fileId);
                });
            });

            // Actualizar parámetros
            document.querySelectorAll('.param-input').forEach(el => {
                el.addEventListener('input', (e) => {
                    const fileId = e.target.getAttribute('data-file-id');
                    const paramName = e.target.getAttribute('data-param');
                    const value = e.target.value;
                    this.updateFileParameter(fileId, paramName, value);
                });
            });

            // Auto-generar parámetros
            document.querySelectorAll('.auto-generate-btn').forEach(el => {
                el.addEventListener('click', (e) => {
                    const fileId = e.target.closest('.auto-generate-btn').getAttribute('data-file-id');
                    this.autoGenerateParameters(fileId);
                });
            });

            // Limpiar parámetros
            document.querySelectorAll('.clear-params-btn').forEach(el => {
                el.addEventListener('click', (e) => {
                    const fileId = e.target.closest('.clear-params-btn').getAttribute('data-file-id');
                    this.clearParameters(fileId);
                });
            });

            // Copiar nombre de archivo
            document.querySelectorAll('.copy-filename-btn').forEach(el => {
                el.addEventListener('click', (e) => {
                    const fileId = e.target.closest('.copy-filename-btn').getAttribute('data-file-id');
                    this.copyFilename(fileId);
                });
            });
        }

        /**
         * Auto-generar parámetros para un archivo
         */
        autoGenerateParameters(fileId) {
            if (this.files.has(fileId)) {
                const fileData = this.files.get(fileId);
                
                fileData.parameters.codigo_sorteo = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'][Math.floor(Math.random() * 10)];
                fileData.parameters.id_whatsapp = this.generateWhatsAppId();
                fileData.parameters.nombre_usuario = this.generateRandomName();
                fileData.parameters.caption = 'Pago Móvil';
                fileData.parameters.hora_exacta = this.generateRandomTime();
                
                fileData.status = 'configured';
                this.updateDisplay();
                
                console.log(`🎲 Parámetros auto-generados para: ${fileData.file.name}`);
            }
        }

        /**
         * Limpiar parámetros de un archivo
         */
        clearParameters(fileId) {
            if (this.files.has(fileId)) {
                const fileData = this.files.get(fileId);
                
                Object.keys(fileData.parameters).forEach(key => {
                    if (key !== 'numero_llegada') {
                        fileData.parameters[key] = '';
                    }
                });
                
                fileData.status = 'ready';
                this.updateDisplay();
                
                console.log(`🧹 Parámetros limpiados para: ${fileData.file.name}`);
            }
        }

        /**
         * Copiar nombre de archivo al clipboard
         */
        async copyFilename(fileId) {
            if (this.files.has(fileId)) {
                const fileData = this.files.get(fileId);
                
                try {
                    await navigator.clipboard.writeText(fileData.file.name);
                    
                    if (window.OCRSystem.Main) {
                        window.OCRSystem.Main.showNotification(
                            'Nombre de archivo copiado al portapapeles',
                            'success'
                        );
                    }
                } catch (error) {
                    console.error('❌ Error copiando nombre:', error);
                }
            }
        }

        /**
         * Obtener clase CSS para estado
         */
        getStatusClass(status) {
            const classes = {
                ready: 'ready',
                configured: 'configured',
                processing: 'processing',
                processed: 'success',
                error: 'error'
            };
            return classes[status] || 'ready';
        }

        /**
         * Obtener icono para estado
         */
        getStatusIcon(status) {
            const icons = {
                ready: 'fa-clock',
                configured: 'fa-check-circle',
                processing: 'fa-spinner fa-spin',
                processed: 'fa-check',
                error: 'fa-exclamation-triangle'
            };
            return icons[status] || 'fa-clock';
        }

        /**
         * Obtener texto para estado
         */
        getStatusText(status) {
            const texts = {
                ready: 'Listo',
                configured: 'Configurado',
                processing: 'Procesando',
                processed: 'Procesado',
                error: 'Error'
            };
            return texts[status] || 'Listo';
        }

        /**
         * Truncar nombre de archivo
         */
        truncateFilename(filename, maxLength = 40) {
            if (filename.length <= maxLength) return filename;
            
            const extension = filename.split('.').pop();
            const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
            const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 4) + '...';
            
            return `${truncatedName}.${extension}`;
        }

        /**
         * Formatear tamaño de archivo
         */
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        /**
         * Mostrar error
         */
        showError(message) {
            if (window.OCRSystem.Main) {
                window.OCRSystem.Main.showNotification(message, 'error');
            } else {
                console.error('❌', message);
            }
        }

        /**
         * Actualizar contadores
         */
        updateCounters() {
            if (window.OCRSystem.Main) {
                window.OCRSystem.Main.updateCounters();
            }
        }

        /**
         * Obtener número de archivos
         */
        getFileCount() {
            return this.files.size;
        }

        /**
         * Obtener archivos
         */
        getFiles() {
            return Array.from(this.files.values());
        }

        /**
         * Limpiar todos los archivos
         */
        clearAll() {
            this.files.clear();
            this.fileCounter = 0;
            this.updateDisplay();
            this.updateCounters();
        }
    }

    // Exportar el File Manager
    window.OCRSystem.FileManager = FileManager;

    console.log('📁 File Manager module loaded');

})();