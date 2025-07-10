/**
 * RESULTS VIEWER - SISTEMA OCR EMPRESARIAL
 * Módulo para visualización de resultados y agrupación por lotes
 * FILOSOFÍA: TRANSPARENCIA TOTAL + PERFECCIÓN CONTINUA
 */

class ResultsViewer {
    constructor() {
        this.currentFiles = [];
        this.groupedByBatch = new Map();
        this.currentView = 'list'; // list, batch, details
        this.selectedBatch = null;
        this.sortConfig = { field: 'modified_date', order: 'desc' };
        this.filterConfig = { confidence: 'all', status: 'all' };
        
        this.initializeElements();
        this.bindEvents();
    }

    /**
     * INICIALIZACIÓN DE ELEMENTOS DOM
     */
    initializeElements() {
        this.elements = {
            resultsTable: document.getElementById('resultsTable'),
            resultsContainer: document.getElementById('resultsContainer'),
            viewToggle: document.getElementById('viewToggle'),
            sortControls: document.getElementById('sortControls'),
            filterControls: document.getElementById('filterControls'),
            batchSelector: document.getElementById('batchSelector'),
            refreshBtn: document.getElementById('refreshResultsBtn'),
            extractBtn: document.getElementById('extractResultsBtn'),
            fileDetailsModal: document.getElementById('fileDetailsModal'),
            confidenceFilter: document.getElementById('confidenceFilter'),
            searchInput: document.getElementById('resultsSearch')
        };
    }

    /**
     * BIND DE EVENTOS
     */
    bindEvents() {
        // Refresh button
        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => this.loadResults());
        }

        // Extract results button
        if (this.elements.extractBtn) {
            this.elements.extractBtn.addEventListener('click', () => this.extractResults());
        }

        // View toggle
        if (this.elements.viewToggle) {
            this.elements.viewToggle.addEventListener('change', (e) => {
                this.currentView = e.target.value;
                this.renderResults();
            });
        }

        // Sort controls
        if (this.elements.sortControls) {
            this.elements.sortControls.addEventListener('change', (e) => {
                if (e.target.name === 'sortField') {
                    this.sortConfig.field = e.target.value;
                    this.renderResults();
                }
                if (e.target.name === 'sortOrder') {
                    this.sortConfig.order = e.target.value;
                    this.renderResults();
                }
            });
        }

        // Filter controls
        if (this.elements.confidenceFilter) {
            this.elements.confidenceFilter.addEventListener('change', (e) => {
                this.filterConfig.confidence = e.target.value;
                this.renderResults();
            });
        }

        // Search input
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', this.debounce((e) => {
                this.filterConfig.search = e.target.value;
                this.renderResults();
            }, 300));
        }

        // Batch selector
        if (this.elements.batchSelector) {
            this.elements.batchSelector.addEventListener('change', (e) => {
                this.selectedBatch = e.target.value || null;
                this.renderResults();
            });
        }

        // Listen for batch completed events
        window.addEventListener('batchCompleted', (e) => {
            this.handleBatchCompleted(e.detail);
        });
    }

    /**
     * CARGAR RESULTADOS DESDE BACKEND
     */
    async loadResults(showLoading = true) {
        try {
            if (showLoading) {
                this.showLoadingState();
            }

            const data = await window.apiClient.getProcessedFiles();
            
            if (data.status === 'exitoso' && data.files) {
                this.currentFiles = data.files;
                this.processFilesForBatchView();
                this.renderResults();
                this.updateBatchSelector();
                
                this.showNotification(`✅ ${data.files.length} archivo(s) cargado(s)`, 'success');
            } else {
                this.currentFiles = [];
                this.renderResults();
                this.showNotification('⚠️ No se encontraron archivos procesados', 'warning');
            }

        } catch (error) {
            console.error('Error cargando resultados:', error);
            this.showErrorState(error.getUserMessage());
            this.showNotification(`❌ Error cargando resultados: ${error.getUserMessage()}`, 'error');
        }
    }

    /**
     * PROCESAR ARCHIVOS PARA VISTA POR LOTES
     * Extraer request_id/batch_id de nombres de archivo y agrupar
     */
    processFilesForBatchView() {
        this.groupedByBatch.clear();
        
        this.currentFiles.forEach(file => {
            // Extraer batch ID del filename (formato: BATCH_YYYYMMDD_HHMMSS_xxx_filename.ext.json)
            const batchMatch = file.filename.match(/^BATCH_(\d{8}_\d{6}_[a-zA-Z0-9]+)/);
            const batchId = batchMatch ? batchMatch[1] : 'unknown';
            
            if (!this.groupedByBatch.has(batchId)) {
                this.groupedByBatch.set(batchId, {
                    id: batchId,
                    files: [],
                    totalFiles: 0,
                    avgConfidence: 0,
                    completedAt: null,
                    totalSize: 0
                });
            }
            
            const batch = this.groupedByBatch.get(batchId);
            batch.files.push(file);
            batch.totalFiles++;
            batch.totalSize += file.size_bytes || 0;
            
            // Actualizar fecha más reciente
            const fileDate = new Date(file.modified_date);
            if (!batch.completedAt || fileDate > batch.completedAt) {
                batch.completedAt = fileDate;
            }
        });

        // Calcular confianza promedio por lote
        this.groupedByBatch.forEach(batch => {
            const confidences = batch.files
                .filter(f => f.confidence && f.confidence > 0)
                .map(f => f.confidence);
            
            batch.avgConfidence = confidences.length > 0 
                ? confidences.reduce((a, b) => a + b, 0) / confidences.length 
                : 0;
        });
    }

    /**
     * RENDERIZAR RESULTADOS
     */
    renderResults() {
        if (!this.elements.resultsContainer) return;

        const filteredFiles = this.getFilteredFiles();
        const sortedFiles = this.getSortedFiles(filteredFiles);

        switch (this.currentView) {
            case 'batch':
                this.renderBatchView();
                break;
            case 'details':
                this.renderDetailsView(sortedFiles);
                break;
            default:
                this.renderListView(sortedFiles);
        }

        this.updateResultsStats(sortedFiles);
    }

    /**
     * VISTA LISTA (DEFAULT)
     */
    renderListView(files) {
        if (files.length === 0) {
            this.elements.resultsContainer.innerHTML = this.getEmptyState();
            return;
        }

        const html = `
            <div class="results-header d-flex justify-content-between align-items-center mb-4">
                <h5 class="mb-0">Archivos Procesados (${files.length})</h5>
                <div class="d-flex gap-2">
                    ${this.renderViewControls()}
                </div>
            </div>
            
            ${this.renderFiltersAndSort()}
            
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Archivo</th>
                            <th>Confianza</th>
                            <th>Palabras</th>
                            <th>Tamaño</th>
                            <th>Procesado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${files.map(file => this.renderFileRow(file)).join('')}
                    </tbody>
                </table>
            </div>
        `;

        this.elements.resultsContainer.innerHTML = html;
    }

    /**
     * VISTA POR LOTES
     */
    renderBatchView() {
        const batches = Array.from(this.groupedByBatch.values())
            .sort((a, b) => new Date(b.completedAt) - new Date(a.completedAt));

        if (batches.length === 0) {
            this.elements.resultsContainer.innerHTML = this.getEmptyState();
            return;
        }

        const html = `
            <div class="results-header d-flex justify-content-between align-items-center mb-4">
                <h5 class="mb-0">Resultados por Lote (${batches.length})</h5>
                <div class="d-flex gap-2">
                    ${this.renderViewControls()}
                </div>
            </div>

            <div class="batch-grid">
                ${batches.map(batch => this.renderBatchCard(batch)).join('')}
            </div>
        `;

        this.elements.resultsContainer.innerHTML = html;
    }

    /**
     * VISTA DE DETALLES
     */
    renderDetailsView(files) {
        const html = `
            <div class="results-header d-flex justify-content-between align-items-center mb-4">
                <h5 class="mb-0">Vista Detallada (${files.length})</h5>
                <div class="d-flex gap-2">
                    ${this.renderViewControls()}
                </div>
            </div>

            ${this.renderFiltersAndSort()}

            <div class="details-grid">
                ${files.map(file => this.renderFileCard(file)).join('')}
            </div>
        `;

        this.elements.resultsContainer.innerHTML = html;
    }

    /**
     * RENDERIZAR CONTROLES DE VISTA
     */
    renderViewControls() {
        return `
            <div class="btn-group" role="group">
                <input type="radio" class="btn-check" name="viewType" id="viewList" value="list" ${this.currentView === 'list' ? 'checked' : ''}>
                <label class="btn btn-outline-primary" for="viewList">
                    <i class="fas fa-list me-1"></i>Lista
                </label>
                
                <input type="radio" class="btn-check" name="viewType" id="viewBatch" value="batch" ${this.currentView === 'batch' ? 'checked' : ''}>
                <label class="btn btn-outline-primary" for="viewBatch">
                    <i class="fas fa-layer-group me-1"></i>Lotes
                </label>
                
                <input type="radio" class="btn-check" name="viewType" id="viewDetails" value="details" ${this.currentView === 'details' ? 'checked' : ''}>
                <label class="btn btn-outline-primary" for="viewDetails">
                    <i class="fas fa-th-large me-1"></i>Detalles
                </label>
            </div>
        `;
    }

    /**
     * RENDERIZAR FILTROS Y ORDENAMIENTO
     */
    renderFiltersAndSort() {
        return `
            <div class="filters-sort-container bg-light rounded p-3 mb-4">
                <div class="row g-3">
                    <div class="col-md-4">
                        <label class="form-label small">Buscar</label>
                        <input type="text" class="form-control" id="searchInput" 
                               placeholder="Buscar por nombre..." 
                               value="${this.filterConfig.search || ''}">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">Confianza</label>
                        <select class="form-select" id="confidenceFilterSelect">
                            <option value="all" ${this.filterConfig.confidence === 'all' ? 'selected' : ''}>Todas</option>
                            <option value="high" ${this.filterConfig.confidence === 'high' ? 'selected' : ''}>Alta (>90%)</option>
                            <option value="medium" ${this.filterConfig.confidence === 'medium' ? 'selected' : ''}>Media (70-90%)</option>
                            <option value="low" ${this.filterConfig.confidence === 'low' ? 'selected' : ''}>Baja (<70%)</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small">Ordenar por</label>
                        <select class="form-select" id="sortFieldSelect">
                            <option value="modified_date" ${this.sortConfig.field === 'modified_date' ? 'selected' : ''}>Fecha</option>
                            <option value="filename" ${this.sortConfig.field === 'filename' ? 'selected' : ''}>Nombre</option>
                            <option value="confidence" ${this.sortConfig.field === 'confidence' ? 'selected' : ''}>Confianza</option>
                            <option value="size_bytes" ${this.sortConfig.field === 'size_bytes' ? 'selected' : ''}>Tamaño</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">Orden</label>
                        <select class="form-select" id="sortOrderSelect">
                            <option value="desc" ${this.sortConfig.order === 'desc' ? 'selected' : ''}>Desc</option>
                            <option value="asc" ${this.sortConfig.order === 'asc' ? 'selected' : ''}>Asc</option>
                        </select>
                    </div>
                    <div class="col-md-1 d-flex align-items-end">
                        <button type="button" class="btn btn-outline-secondary" onclick="resultsViewer.clearFilters()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * RENDERIZAR FILA DE ARCHIVO
     */
    renderFileRow(file) {
        const confidenceBadge = this.getConfidenceBadge(file.confidence);
        const sizeFormatted = this.formatFileSize(file.size_bytes);
        const dateFormatted = this.formatDate(file.modified_date);

        return `
            <tr data-filename="${file.filename}">
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-file-alt text-primary me-2"></i>
                        <div>
                            <div class="fw-medium">${this.escapeHtml(this.getDisplayFilename(file.filename))}</div>
                            ${file.texto_preview ? `<small class="text-muted">${this.escapeHtml(file.texto_preview.substring(0, 50))}...</small>` : ''}
                        </div>
                    </div>
                </td>
                <td>${confidenceBadge}</td>
                <td>
                    <span class="badge bg-info">${file.word_count || 0}</span>
                    ${file.has_coordinates ? '<i class="fas fa-map-marker-alt text-success ms-1" title="Con coordenadas"></i>' : ''}
                </td>
                <td>${sizeFormatted}</td>
                <td>
                    <small class="text-muted">${dateFormatted}</small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary" 
                                onclick="resultsViewer.viewFileDetails('${file.filename}')" 
                                title="Ver detalles">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" class="btn btn-outline-secondary" 
                                onclick="resultsViewer.downloadFile('${file.filename}')" 
                                title="Descargar JSON">
                            <i class="fas fa-download"></i>
                        </button>
                        <button type="button" class="btn btn-outline-info" 
                                onclick="resultsViewer.copyFilename('${file.filename}')" 
                                title="Copiar nombre">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * RENDERIZAR TARJETA DE LOTE
     */
    renderBatchCard(batch) {
        const confidenceBadge = this.getConfidenceBadge(batch.avgConfidence);
        const dateFormatted = this.formatDate(batch.completedAt);
        const sizeFormatted = this.formatFileSize(batch.totalSize);

        return `
            <div class="batch-card card mb-3" data-batch-id="${batch.id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-layer-group text-primary me-2"></i>
                        Lote ${batch.id.split('_')[1] || batch.id}
                    </h6>
                    ${confidenceBadge}
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-3">
                            <div class="stat-item">
                                <div class="stat-value">${batch.totalFiles}</div>
                                <div class="stat-label small text-muted">Archivos</div>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="stat-item">
                                <div class="stat-value">${sizeFormatted}</div>
                                <div class="stat-label small text-muted">Tamaño</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="stat-item">
                                <div class="stat-value small">${dateFormatted}</div>
                                <div class="stat-label small text-muted">Completado</div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-3">
                        <button type="button" class="btn btn-primary btn-sm me-2" 
                                onclick="resultsViewer.viewBatchFiles('${batch.id}')">
                            <i class="fas fa-eye me-1"></i>Ver Archivos
                        </button>
                        <button type="button" class="btn btn-outline-secondary btn-sm" 
                                onclick="resultsViewer.extractBatchResults('${batch.id}')">
                            <i class="fas fa-download me-1"></i>Extraer
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * RENDERIZAR TARJETA DE ARCHIVO
     */
    renderFileCard(file) {
        const confidenceBadge = this.getConfidenceBadge(file.confidence);
        const sizeFormatted = this.formatFileSize(file.size_bytes);
        const dateFormatted = this.formatDate(file.modified_date);

        return `
            <div class="file-card card mb-3" data-filename="${file.filename}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0 text-truncate">${this.escapeHtml(this.getDisplayFilename(file.filename))}</h6>
                    ${confidenceBadge}
                </div>
                <div class="card-body">
                    ${file.texto_preview ? `
                        <div class="preview-text mb-3">
                            <small class="text-muted">${this.escapeHtml(file.texto_preview)}</small>
                        </div>
                    ` : ''}
                    
                    <div class="row text-center mb-3">
                        <div class="col-4">
                            <div class="stat-item">
                                <div class="stat-value">${file.word_count || 0}</div>
                                <div class="stat-label small text-muted">Palabras</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item">
                                <div class="stat-value">${sizeFormatted}</div>
                                <div class="stat-label small text-muted">Tamaño</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item">
                                <div class="stat-value small">${dateFormatted}</div>
                                <div class="stat-label small text-muted">Procesado</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="button" class="btn btn-primary btn-sm" 
                                onclick="resultsViewer.viewFileDetails('${file.filename}')">
                            <i class="fas fa-eye me-1"></i>Ver Detalles
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * VER DETALLES DE ARCHIVO
     */
    async viewFileDetails(filename) {
        try {
            this.showNotification('Cargando detalles...', 'info', 2000);
            
            const cleanFilename = filename.replace('.json', '');
            const data = await window.apiClient.getResultData(cleanFilename);
            
            this.showFileDetailsModal(data);
            
        } catch (error) {
            console.error('Error cargando detalles:', error);
            this.showNotification(`❌ Error cargando detalles: ${error.getUserMessage()}`, 'error');
        }
    }

    /**
     * MOSTRAR MODAL DE DETALLES
     */
    showFileDetailsModal(data) {
        const modalHtml = `
            <div class="modal fade" id="fileDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-file-alt me-2"></i>
                                ${this.escapeHtml(data.filename || 'Detalles del Archivo')}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${this.renderFileDetailsContent(data)}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            <button type="button" class="btn btn-primary" onclick="resultsViewer.copyFileData('${data.filename}')">
                                <i class="fas fa-copy me-1"></i>Copiar Datos
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const existingModal = document.getElementById('fileDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Agregar nuevo modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('fileDetailsModal'));
        modal.show();
    }

    /**
     * RENDERIZAR CONTENIDO DEL MODAL DE DETALLES
     */
    renderFileDetailsContent(data) {
        const stats = data.estadisticas || {};
        const confidenceBadge = this.getConfidenceBadge(stats.confidence_avg);

        return `
            <div class="row">
                <!-- Información del archivo -->
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h6 class="mb-0"><i class="fas fa-info-circle me-1"></i>Información</h6>
                        </div>
                        <div class="card-body">
                            ${data.archivo_info ? `
                                <p><strong>Original:</strong> ${this.escapeHtml(data.archivo_info.nombre_original || '')}</p>
                                <p><strong>Formato:</strong> ${data.archivo_info.formato || ''}</p>
                                <p><strong>Tamaño:</strong> ${data.archivo_info.tamaño || ''}</p>
                                <p><strong>Procesado:</strong> ${this.formatDate(data.archivo_info.fecha_procesamiento)}</p>
                            ` : ''}
                            
                            <div class="mt-3">
                                <h6>Estadísticas OCR</h6>
                                <p><strong>Confianza:</strong> ${confidenceBadge}</p>
                                <p><strong>Palabras:</strong> ${stats.total_palabras || stats.total || 0}</p>
                                <p><strong>Tiempo:</strong> ${stats.tiempo_procesamiento || 0}ms</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Texto extraído -->
                <div class="col-md-8">
                    <div class="card h-100">
                        <div class="card-header">
                            <h6 class="mb-0"><i class="fas fa-text-width me-1"></i>Texto Extraído</h6>
                        </div>
                        <div class="card-body">
                            <div class="text-container bg-light p-3 rounded" style="max-height: 200px; overflow-y: auto;">
                                <pre class="mb-0">${this.escapeHtml(data.texto_extraido || 'No disponible')}</pre>
                            </div>
                            
                            ${data.datos_financieros ? `
                                <div class="mt-3">
                                    <h6>Datos Financieros</h6>
                                    <div class="row">
                                        <div class="col-6">
                                            <small><strong>Monto:</strong> ${data.datos_financieros.monto_encontrado || 'N/A'}</small>
                                        </div>
                                        <div class="col-6">
                                            <small><strong>Referencia:</strong> ${data.datos_financieros.referencia || 'N/A'}</small>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>

            ${data.coordenadas && data.coordenadas.length > 0 ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="fas fa-map-marker-alt me-1"></i>Coordenadas (${data.coordenadas.length})</h6>
                            </div>
                            <div class="card-body">
                                <div style="max-height: 300px; overflow-y: auto;">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Texto</th>
                                                <th>Confianza</th>
                                                <th>Posición</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${data.coordenadas.slice(0, 50).map(coord => `
                                                <tr>
                                                    <td><code>${this.escapeHtml(coord.texto || '')}</code></td>
                                                    <td>${this.getConfidenceBadge(coord.confianza)}</td>
                                                    <td><small>${coord.x1},${coord.y1} → ${coord.x2},${coord.y2}</small></td>
                                                </tr>
                                            `).join('')}
                                            ${data.coordenadas.length > 50 ? `
                                                <tr>
                                                    <td colspan="3" class="text-center text-muted">
                                                        ... y ${data.coordenadas.length - 50} más
                                                    </td>
                                                </tr>
                                            ` : ''}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
    }

    /**
     * EXTRAER RESULTADOS
     */
    async extractResults() {
        try {
            this.showNotification('Extrayendo resultados...', 'info');
            
            const data = await window.apiClient.extractResults();
            
            // Crear y descargar JSON consolidado
            const jsonBlob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(jsonBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `resultados_consolidados_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('✅ Resultados extraídos exitosamente', 'success');
            
        } catch (error) {
            console.error('Error extrayendo resultados:', error);
            this.showNotification(`❌ Error extrayendo resultados: ${error.getUserMessage()}`, 'error');
        }
    }

    /**
     * UTILIDADES
     */
    getFilteredFiles() {
        let filtered = [...this.currentFiles];
        
        // Filtrar por búsqueda
        if (this.filterConfig.search) {
            const search = this.filterConfig.search.toLowerCase();
            filtered = filtered.filter(file => 
                file.filename.toLowerCase().includes(search) ||
                (file.texto_preview && file.texto_preview.toLowerCase().includes(search))
            );
        }
        
        // Filtrar por confianza
        if (this.filterConfig.confidence !== 'all') {
            filtered = filtered.filter(file => {
                const confidence = file.confidence || 0;
                switch (this.filterConfig.confidence) {
                    case 'high': return confidence > 0.9;
                    case 'medium': return confidence >= 0.7 && confidence <= 0.9;
                    case 'low': return confidence < 0.7;
                    default: return true;
                }
            });
        }
        
        return filtered;
    }

    getSortedFiles(files) {
        return files.sort((a, b) => {
            let aVal = a[this.sortConfig.field];
            let bVal = b[this.sortConfig.field];
            
            // Manejo especial para fechas
            if (this.sortConfig.field === 'modified_date') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }
            
            if (this.sortConfig.order === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    getConfidenceBadge(confidence) {
        if (!confidence || confidence === 0) {
            return '<span class="badge bg-secondary">N/A</span>';
        }
        
        const percent = (confidence * 100).toFixed(1);
        let badgeClass = 'bg-secondary';
        
        if (confidence > 0.9) badgeClass = 'bg-success';
        else if (confidence > 0.7) badgeClass = 'bg-warning';
        else badgeClass = 'bg-danger';
        
        return `<span class="badge ${badgeClass}">${percent}%</span>`;
    }

    getDisplayFilename(filename) {
        // Remover extensión .json y prefijo BATCH_ para mostrar
        return filename.replace(/\.json$/, '').replace(/^BATCH_\d{8}_\d{6}_[a-zA-Z0-9]+_/, '');
    }

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * ESTADOS DE UI
     */
    showLoadingState() {
        if (this.elements.resultsContainer) {
            this.elements.resultsContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-spinner fa-spin fa-2x text-primary mb-3"></i>
                    <p class="text-muted">Cargando resultados...</p>
                </div>
            `;
        }
    }

    showErrorState(message) {
        if (this.elements.resultsContainer) {
            this.elements.resultsContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-2x text-danger mb-3"></i>
                    <h5>Error cargando resultados</h5>
                    <p class="text-muted">${this.escapeHtml(message)}</p>
                    <button type="button" class="btn btn-primary" onclick="resultsViewer.loadResults()">
                        <i class="fas fa-refresh me-1"></i>Reintentar
                    </button>
                </div>
            `;
        }
    }

    getEmptyState() {
        return `
            <div class="text-center py-5">
                <i class="fas fa-file-alt fa-3x text-muted mb-3"></i>
                <h5>No hay resultados</h5>
                <p class="text-muted">No se encontraron archivos procesados</p>
                <button type="button" class="btn btn-primary" onclick="resultsViewer.loadResults()">
                    <i class="fas fa-refresh me-1"></i>Actualizar
                </button>
            </div>
        `;
    }

    /**
     * ACCIONES ADICIONALES
     */
    copyFilename(filename) {
        navigator.clipboard.writeText(filename).then(() => {
            this.showNotification('📋 Nombre copiado al portapapeles', 'success', 2000);
        });
    }

    downloadFile(filename) {
        window.open(`/api/ocr/download_json/${encodeURIComponent(filename)}`, '_blank');
    }

    clearFilters() {
        this.filterConfig = { confidence: 'all', status: 'all' };
        if (this.elements.searchInput) this.elements.searchInput.value = '';
        this.renderResults();
    }

    updateResultsStats(files) {
        // Disparar evento para actualizar estadísticas en el dashboard
        window.dispatchEvent(new CustomEvent('resultsStatsUpdate', {
            detail: {
                totalFiles: files.length,
                avgConfidence: files.length > 0 
                    ? files.reduce((sum, f) => sum + (f.confidence || 0), 0) / files.length 
                    : 0,
                totalBatches: this.groupedByBatch.size
            }
        }));
    }

    updateBatchSelector() {
        if (!this.elements.batchSelector) return;
        
        const batches = Array.from(this.groupedByBatch.keys()).sort().reverse();
        const html = `
            <option value="">Todos los lotes</option>
            ${batches.map(batchId => `
                <option value="${batchId}" ${this.selectedBatch === batchId ? 'selected' : ''}>
                    Lote ${batchId.split('_')[1] || batchId}
                </option>
            `).join('')}
        `;
        
        this.elements.batchSelector.innerHTML = html;
    }

    handleBatchCompleted(batchData) {
        // Auto-reload cuando se completa un lote
        setTimeout(() => {
            this.loadResults(false);
        }, 1000);
    }

    showNotification(message, type = 'info', duration = 5000) {
        window.dispatchEvent(new CustomEvent('showNotification', {
            detail: { message, type, duration }
        }));
    }

    // Métodos para acciones específicas de lotes
    viewBatchFiles(batchId) {
        this.selectedBatch = batchId;
        this.currentView = 'list';
        this.renderResults();
        this.updateBatchSelector();
    }

    async extractBatchResults(batchId) {
        // Implementar extracción específica de lote
        this.showNotification('Funcionalidad en desarrollo', 'info');
    }
}

// Instancia global del results viewer
window.resultsViewer = new ResultsViewer();