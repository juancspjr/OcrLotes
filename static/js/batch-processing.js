/**
 * Sistema de Procesamiento por Lotes con Monitoreo de Recursos
 * Interfaz JavaScript para carga masiva de recibos OCR
 */

class BatchProcessor {
    constructor() {
        this.selectedFiles = [];
        this.currentBatch = null;
        this.pollingInterval = null;
        this.resourceMonitorInterval = null;
        this.currentJsonData = null;
        this.maxBatchSize = 20;
        this.currentBatchSize = 5;
        this.autoOptimize = true;
        
        this.initializeEventListeners();
        this.startResourceMonitoring();
        this.loadConfiguration();
    }

    initializeEventListeners() {
        // Drag and drop functionality
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('imageFiles');
        const form = document.getElementById('batchForm');
        const batchSizeSlider = document.getElementById('batchSize');
        const autoOptimizeCheckbox = document.getElementById('autoOptimize');

        // Drop zone events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.handleFileSelect(e.dataTransfer.files);
        });

        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitBatch();
        });

        // Batch size configuration
        batchSizeSlider.addEventListener('input', (e) => {
            this.currentBatchSize = parseInt(e.target.value);
            document.getElementById('batchSizeValue').textContent = this.currentBatchSize;
            this.saveConfiguration();
        });

        // Auto-optimize toggle
        autoOptimizeCheckbox.addEventListener('change', (e) => {
            this.autoOptimize = e.target.checked;
            this.saveConfiguration();
        });

        // JSON validation for additional data
        document.getElementById('additionalData').addEventListener('input', (e) => {
            this.validateJson(e.target.value);
        });
    }

    handleFileSelect(files) {
        this.selectedFiles = Array.from(files).filter(file => {
            return file.type.startsWith('image/');
        });

        this.updateFileList();
        this.optimizeBatchSize();
    }

    updateFileList() {
        const container = document.getElementById('selectedFiles');
        
        if (this.selectedFiles.length === 0) {
            container.innerHTML = '';
            return;
        }

        const html = `
            <div class="alert alert-info">
                <i class="fas fa-images me-2"></i>
                <strong>${this.selectedFiles.length}</strong> archivos seleccionados
                <div class="mt-2">
                    ${this.selectedFiles.map(file => `
                        <span class="badge bg-secondary me-1">${file.name}</span>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    validateJson(jsonString) {
        const additionalDataInput = document.getElementById('additionalData');
        
        if (!jsonString.trim()) {
            additionalDataInput.classList.remove('is-invalid', 'is-valid');
            return true;
        }

        try {
            JSON.parse(jsonString);
            additionalDataInput.classList.remove('is-invalid');
            additionalDataInput.classList.add('is-valid');
            return true;
        } catch (e) {
            additionalDataInput.classList.remove('is-valid');
            additionalDataInput.classList.add('is-invalid');
            return false;
        }
    }

    async submitBatch() {
        if (this.selectedFiles.length === 0) {
            this.showAlert('warning', 'Por favor selecciona al menos un archivo');
            return;
        }

        // Validate JSON if provided
        const additionalData = document.getElementById('additionalData').value;
        if (additionalData && !this.validateJson(additionalData)) {
            this.showAlert('danger', 'El formato JSON de datos adicionales no es válido');
            return;
        }

        const formData = new FormData();
        
        // Add files
        this.selectedFiles.forEach(file => {
            formData.append('images', file);
        });

        // Add metadata
        formData.append('caption_global', document.getElementById('captionGlobal').value);
        formData.append('additional_data_batch', additionalData);
        formData.append('batch_size', this.currentBatchSize);

        try {
            this.updateSubmitButton(true);
            this.showProgress(0, 'Enviando archivos...');

            const response = await fetch('/api/upload_batch', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.currentBatch = result.enqueued_ids;
                this.showAlert('success', `Lote enviado exitosamente. ${result.enqueued_ids.length} archivos en cola de procesamiento`);
                this.startPolling();
                this.clearForm();
            } else {
                this.showAlert('danger', result.message || 'Error procesando el lote');
            }
        } catch (error) {
            this.showAlert('danger', `Error de conexión: ${error.message}`);
        } finally {
            this.updateSubmitButton(false);
        }
    }

    updateSubmitButton(loading) {
        const button = document.getElementById('submitBtn');
        
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
        } else {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-rocket me-2"></i>Procesar Lote';
        }
    }

    showProgress(percentage, text) {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        progressContainer.style.display = 'block';
        progressBar.style.width = percentage + '%';
        progressText.textContent = text;
    }

    hideProgress() {
        const progressContainer = document.getElementById('progressContainer');
        progressContainer.style.display = 'none';
    }

    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.pollingInterval = setInterval(() => {
            this.checkBatchStatus();
        }, 3000); // Check every 3 seconds

        // Initial check
        this.checkBatchStatus();
    }

    async checkBatchStatus() {
        if (!this.currentBatch || this.currentBatch.length === 0) {
            return;
        }

        try {
            const results = await Promise.all(
                this.currentBatch.map(async (requestId) => {
                    const cleanId = requestId.replace(/\.(png|jpg|jpeg)$/i, '');
                    const response = await fetch(`/api/ocr/result/${cleanId}`);
                    return response.json();
                })
            );

            this.updateBatchResults(results);
            
            // Check if all are completed
            const allCompleted = results.every(result => 
                result.status === 'completed' || result.status === 'error'
            );

            if (allCompleted) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
                this.hideProgress();
                this.showAlert('success', 'Procesamiento de lote completado');
            } else {
                const completed = results.filter(r => r.status === 'completed' || r.status === 'error').length;
                const percentage = (completed / results.length) * 100;
                this.showProgress(percentage, `Procesando... ${completed} de ${results.length} completados`);
            }
        } catch (error) {
            console.error('Error checking batch status:', error);
        }
    }

    updateBatchResults(results) {
        const container = document.getElementById('resultsList');
        
        if (results.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No hay resultados disponibles</p>';
            return;
        }

        const html = results.map(result => {
            const statusClass = this.getStatusClass(result.status);
            const statusIcon = this.getStatusIcon(result.status);
            
            return `
                <div class="result-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">
                                <i class="fas fa-file-image me-2"></i>
                                ${result.request_id || 'Desconocido'}
                            </h6>
                            <div class="mb-2">
                                <span class="status-badge ${statusClass}">
                                    ${statusIcon} ${result.status}
                                </span>
                            </div>
                            ${result.status === 'error' && result.message ? 
                                `<div class="text-danger small">
                                    <i class="fas fa-exclamation-triangle me-1"></i>
                                    ${result.message}
                                </div>` : ''
                            }
                            ${result.status === 'completed' && result.result ? 
                                `<div class="text-success small">
                                    <i class="fas fa-check me-1"></i>
                                    Texto extraído: ${result.result.full_raw_ocr_text ? result.result.full_raw_ocr_text.length : 0} caracteres
                                </div>` : ''
                            }
                        </div>
                        <div class="text-end">
                            ${result.status === 'completed' ? 
                                `<button class="btn btn-sm btn-outline-primary me-2" onclick="batchProcessor.showJsonModal('${result.request_id}', ${JSON.stringify(result.result).replace(/"/g, '&quot;')})">
                                    <i class="fas fa-eye me-1"></i>Ver JSON
                                </button>
                                <button class="btn btn-sm btn-outline-success" onclick="batchProcessor.downloadResult('${result.request_id}', ${JSON.stringify(result.result).replace(/"/g, '&quot;')})">
                                    <i class="fas fa-download me-1"></i>Descargar
                                </button>` : ''
                            }
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    }

    getStatusClass(status) {
        switch (status) {
            case 'completed': return 'status-success';
            case 'error': return 'status-error';
            case 'processing': return 'status-processing';
            default: return 'status-processing';
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'completed': return '✅';
            case 'error': return '❌';
            case 'processing': return '⏳';
            default: return '⏳';
        }
    }

    showJsonModal(requestId, jsonData) {
        this.currentJsonData = { requestId, data: jsonData };
        
        const modal = new bootstrap.Modal(document.getElementById('jsonModal'));
        const content = document.getElementById('jsonContent');
        
        content.innerHTML = `<pre>${JSON.stringify(jsonData, null, 2)}</pre>`;
        modal.show();
    }

    copyJsonToClipboard() {
        if (!this.currentJsonData) return;
        
        const text = JSON.stringify(this.currentJsonData.data, null, 2);
        navigator.clipboard.writeText(text).then(() => {
            this.showAlert('success', 'JSON copiado al portapapeles');
        }).catch(err => {
            this.showAlert('danger', 'Error copiando al portapapeles');
        });
    }

    downloadJson() {
        if (!this.currentJsonData) return;
        
        const text = JSON.stringify(this.currentJsonData.data, null, 2);
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentJsonData.requestId}_result.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }

    downloadResult(requestId, jsonData) {
        const text = JSON.stringify(jsonData, null, 2);
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${requestId}_result.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }

    clearForm() {
        document.getElementById('batchForm').reset();
        this.selectedFiles = [];
        this.updateFileList();
        document.getElementById('additionalData').classList.remove('is-valid', 'is-invalid');
    }

    showAlert(type, message) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'warning' ? 'exclamation-triangle' : 'exclamation-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.getElementById('batchStatus');
        container.innerHTML = alertHtml;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    startResourceMonitoring() {
        this.resourceMonitorInterval = setInterval(() => {
            this.updateResourceMonitor();
        }, 2000);
        
        // Initial update
        this.updateResourceMonitor();
    }

    async updateResourceMonitor() {
        try {
            const response = await fetch('/api/ocr/resources');
            const data = await response.json();
            
            if (response.ok) {
                this.updateResourceBars(data);
                this.adaptBatchSize(data);
            }
        } catch (error) {
            console.error('Error updating resource monitor:', error);
        }
    }

    updateResourceBars(data) {
        // Update CPU
        const cpuUsage = data.cpu_percent || 0;
        document.getElementById('cpuUsage').textContent = `${cpuUsage.toFixed(1)}%`;
        document.getElementById('cpuBar').style.width = `${cpuUsage}%`;

        // Update Memory
        const memoryUsage = data.memory_percent || 0;
        document.getElementById('memoryUsage').textContent = `${memoryUsage.toFixed(1)}%`;
        document.getElementById('memoryBar').style.width = `${memoryUsage}%`;

        // Update Queue
        const queueTotal = (data.queue_status?.inbox || 0) + (data.queue_status?.processing || 0);
        const queuePercent = Math.min((queueTotal / 50) * 100, 100); // Assume max 50 items in queue
        document.getElementById('queueSize').textContent = `${queueTotal}`;
        document.getElementById('queueBar').style.width = `${queuePercent}%`;
    }

    adaptBatchSize(resourceData) {
        if (!this.autoOptimize) return;
        
        const cpuUsage = resourceData.cpu_percent || 0;
        const memoryUsage = resourceData.memory_percent || 0;
        const queueSize = (resourceData.queue_status?.inbox || 0) + (resourceData.queue_status?.processing || 0);
        
        let recommendedBatchSize = this.currentBatchSize;
        
        // Adapt based on system resources
        if (cpuUsage > 80 || memoryUsage > 80) {
            recommendedBatchSize = Math.max(1, Math.floor(this.currentBatchSize * 0.7));
        } else if (cpuUsage < 50 && memoryUsage < 50 && queueSize < 5) {
            recommendedBatchSize = Math.min(this.maxBatchSize, Math.floor(this.currentBatchSize * 1.2));
        }
        
        if (recommendedBatchSize !== this.currentBatchSize) {
            this.currentBatchSize = recommendedBatchSize;
            document.getElementById('batchSize').value = this.currentBatchSize;
            document.getElementById('batchSizeValue').textContent = this.currentBatchSize;
            
            this.showOptimizationMessage(resourceData);
        }
    }

    showOptimizationMessage(resourceData) {
        const statusDiv = document.getElementById('optimizationStatus');
        const cpuUsage = resourceData.cpu_percent || 0;
        const memoryUsage = resourceData.memory_percent || 0;
        
        let message = `Tamaño de lote ajustado automáticamente a ${this.currentBatchSize} `;
        
        if (cpuUsage > 80 || memoryUsage > 80) {
            message += `(reducido por alta carga del sistema: CPU ${cpuUsage.toFixed(1)}%, RAM ${memoryUsage.toFixed(1)}%)`;
            statusDiv.className = 'alert alert-warning';
        } else {
            message += `(aumentado por recursos disponibles)`;
            statusDiv.className = 'alert alert-success';
        }
        
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }

    optimizeBatchSize() {
        if (!this.autoOptimize) return;
        
        const fileCount = this.selectedFiles.length;
        
        if (fileCount > 0) {
            // Estimate based on file count
            const estimatedOptimal = Math.min(Math.max(1, Math.floor(fileCount / 4)), this.maxBatchSize);
            
            if (estimatedOptimal !== this.currentBatchSize) {
                this.currentBatchSize = estimatedOptimal;
                document.getElementById('batchSize').value = this.currentBatchSize;
                document.getElementById('batchSizeValue').textContent = this.currentBatchSize;
            }
        }
    }

    saveConfiguration() {
        const config = {
            batchSize: this.currentBatchSize,
            autoOptimize: this.autoOptimize
        };
        
        localStorage.setItem('batchProcessorConfig', JSON.stringify(config));
    }

    loadConfiguration() {
        const stored = localStorage.getItem('batchProcessorConfig');
        
        if (stored) {
            try {
                const config = JSON.parse(stored);
                this.currentBatchSize = config.batchSize || 5;
                this.autoOptimize = config.autoOptimize !== false;
                
                document.getElementById('batchSize').value = this.currentBatchSize;
                document.getElementById('batchSizeValue').textContent = this.currentBatchSize;
                document.getElementById('autoOptimize').checked = this.autoOptimize;
            } catch (error) {
                console.error('Error loading configuration:', error);
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.batchProcessor = new BatchProcessor();
});

// Clear form function for global access
function clearForm() {
    window.batchProcessor.clearForm();
}