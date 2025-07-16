/**
 * RESULTS VIEWER MODULE - SISTEMA OCR EMPRESARIAL
 * FILOSOFÍA: INTEGRIDAD TOTAL + INTERFACE EXCELLENCE
 * 
 * Módulo encargado de mostrar y gestionar los resultados del procesamiento OCR
 * con capacidades avanzadas de filtrado, navegación y visualización.
 */

window.OCRSystem = window.OCRSystem || {};

(function() {
    'use strict';

    class ResultsViewer {
        constructor(config) {
            this.config = config;
            this.apiClient = config.apiClient;
            this.results = [];
            this.filteredResults = [];
            this.currentBatch = null;
            this.filters = {
                status: 'all',
                batch: 'all'
            };
            
            // Referencias DOM
            this.resultsTable = document.getElementById(config.resultsTableId);
            this.batchSelector = document.getElementById(config.batchSelectorId);
            this.statusFilter = document.getElementById(config.statusFilterId);
            
            this.init();
        }

        init() {
            this.setupEventListeners();
            console.log('📊 Results Viewer inicializado');
        }

        /**
         * Configurar event listeners
         */
        setupEventListeners() {
            // Escuchar cambios en filtros si los elementos existen
            if (this.statusFilter) {
                this.statusFilter.addEventListener('change', () => {
                    this.filters.status = this.statusFilter.value;
                    this.applyFilters();
                });
            }
            
            if (this.batchSelector) {
                this.batchSelector.addEventListener('change', () => {
                    this.filters.batch = this.batchSelector.value;
                    console.log(`📋 Cargando lote específico: ${this.filters.batch}`);
                    this.applyFilters();
                });
            }
        }

        /**
         * Refrescar datos de resultados
         */
        async refresh() {
            try {
                console.log('🔄 Refrescando resultados...');
                
                // Mostrar indicador de carga
                this.showLoading(true);
                
                // Cargar datos
                await this.loadResults();
                // Actualizar selector de lotes después de cargar resultados
                this.updateBatchSelector();
                
                // Aplicar filtros
                this.applyFilters();
                
                // Actualizar visualización
                this.updateDisplay();
                
                console.log('✅ Resultados refrescados exitosamente');
                
            } catch (error) {
                console.error('❌ Error refrescando resultados:', error);
                this.showError('Error cargando resultados: ' + error.message);
            } finally {
                this.showLoading(false);
            }
        }

        /**
         * Cargar resultados desde el API
         */
        async loadResults() {
            try {
                const data = await this.apiClient.extractResults();
                
                if (data && data.archivos_procesados) {
                    // FIX: ORDENAMIENTO POR FECHA DE PROCESAMIENTO (MAYOR A MENOR)
                    // Los archivos ya vienen ordenados del backend, pero aseguramos el orden
                    this.results = data.archivos_procesados.map((archivo, index) => ({
                        id: index + 1,
                        filename: archivo.nombre_archivo || 'unknown',
                        codigo_sorteo: archivo.codigo_sorteo || '',
                        id_whatsapp: archivo.id_whatsapp || '',
                        nombre_usuario: archivo.nombre_usuario || '',
                        caption: archivo.caption || '',
                        hora_exacta: archivo.hora_exacta || '',
                        numero_llegada: archivo.numero_llegada || index + 1,
                        referencia: archivo.referencia || '',
                        monto: archivo.monto || '',
                        bancoorigen: archivo.bancoorigen || '',
                        banco_destino: archivo.datosbeneficiario?.banco_destino || '',
                        cedula: archivo.datosbeneficiario?.cedula || '',
                        telefono: archivo.datosbeneficiario?.telefono || '',
                        pago_fecha: archivo.pago_fecha || '',
                        concepto: archivo.concepto || '',
                        texto_total_ocr: archivo.texto_total_ocr || '',
                        confidence: archivo.extraction_stats?.confidence || 0,
                        total_words: archivo.extraction_stats?.total_words || 0,
                        processing_time: archivo.extraction_stats?.processing_time || 0,
                        status: this.determineStatus(archivo),
                        // FIX: CAMPOS DE LOTE AGREGADOS
                        lote_id: archivo.lote_id || 'N/A',
                        lote_fecha: archivo.lote_fecha || 'N/A',
                        raw_data: archivo
                    }));
                    
                    console.log(`📊 Cargados ${this.results.length} resultados`);
                } else {
                    this.results = [];
                    console.log('📊 No hay resultados disponibles');
                }
                
            } catch (error) {
                console.error('❌ Error cargando resultados:', error);
                this.results = [];
                throw error;
            }
        }

        /**
         * Determinar estado del resultado
         */
        determineStatus(archivo) {
            // Verificar si tiene datos principales
            const hasMainData = archivo.referencia || archivo.monto || archivo.bancoorigen;
            const hasOCR = archivo.texto_total_ocr && archivo.texto_total_ocr.length > 0;
            const confidence = archivo.extraction_stats?.confidence || 0;
            
            if (!hasOCR) {
                return 'error';
            }
            
            if (confidence < 0.7) {
                return 'warning';
            }
            
            if (hasMainData && confidence >= 0.8) {
                return 'success';
            }
            
            return 'warning';
        }

        /**
         * Cargar historial de lotes
         */
        async loadBatchHistory() {
            try {
                const batches = await this.apiClient.getBatchHistory();
                this.updateBatchSelector(batches);
            } catch (error) {
                console.warn('⚠️ Error cargando historial de lotes:', error);
            }
        }

        /**
         * Actualizar selector de lotes
         */
        updateBatchSelector(batches) {
            if (!this.batchSelector) return;
            
            // FIX: OBTENER LOTES ÚNICOS DE LOS RESULTADOS PROCESADOS
            const uniqueBatches = new Set();
            const batchOptions = [];
            
            // Obtener lotes únicos de los resultados actuales
            if (this.results && this.results.length > 0) {
                this.results.forEach(result => {
                    if (result.lote_id && result.lote_id !== 'N/A' && !uniqueBatches.has(result.lote_id)) {
                        uniqueBatches.add(result.lote_id);
                        batchOptions.push({
                            id: result.lote_id,
                            fecha: result.lote_fecha,
                            name: result.lote_id
                        });
                    }
                });
            }
            
            // Ordenar por fecha (más reciente primero)
            batchOptions.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
            
            // Limpiar opciones existentes
            this.batchSelector.innerHTML = '<option value="all">Todos los Lotes</option>';
            
            // Agregar lotes únicos
            batchOptions.forEach((batch, index) => {
                const option = document.createElement('option');
                option.value = batch.id;
                const batchNumber = index + 1;
                const fechaFormateada = new Date(batch.fecha).toLocaleDateString();
                option.textContent = `Lote #${batchNumber} - ${fechaFormateada} (${batch.id})`;
                this.batchSelector.appendChild(option);
            });
            
            console.log(`📋 Selector de lotes actualizado: ${batchOptions.length} lotes únicos`);
        }

        /**
         * Actualizar información del lote actual
         */
        updateCurrentBatchInfo(batchInfo) {
            const currentBatchInfoElement = document.getElementById('currentBatchInfo');
            if (currentBatchInfoElement && batchInfo) {
                const batchDate = new Date(batchInfo.date).toLocaleDateString();
                currentBatchInfoElement.textContent = `Lote #${batchInfo.number || 'N/A'} - ${batchDate}`;
            }
        }

        /**
         * Cargar lote específico
         */
        async loadBatch() {
            const batchId = this.filters.batch;
            
            if (batchId === 'current') {
                // Cargar último lote
                await this.loadResults();
            } else {
                // Cargar lote específico (implementar según necesidad)
                console.log(`📋 Cargando lote específico: ${batchId}`);
                // Por ahora, usar los mismos resultados
                await this.loadResults();
            }
            
            this.applyFilters();
            this.updateDisplay();
        }

        /**
         * Aplicar filtros a los resultados
         */
        applyFilters() {
            this.filteredResults = this.results.filter(result => {
                // Filtro por estado
                if (this.filters.status !== 'all') {
                    if (this.filters.status === 'success' && result.status !== 'success') {
                        return false;
                    }
                    if (this.filters.status === 'error' && result.status !== 'error') {
                        return false;
                    }
                }
                
                // FIX: FILTRO POR LOTE IMPLEMENTADO
                // Filtro por lote
                if (this.filters.batch && this.filters.batch !== 'all') {
                    if (result.lote_id !== this.filters.batch) {
                        return false;
                    }
                }
                
                return true;
            });
            
            console.log(`🔍 Filtros aplicados: ${this.filteredResults.length}/${this.results.length} resultados`);
            this.updateDisplay();
        }

        /**
         * Actualizar visualización de resultados
         */
        updateDisplay() {
            if (!this.resultsTable) return;

            if (this.filteredResults.length === 0) {
                this.resultsTable.innerHTML = `
                    <tr id="emptyResultsMessage">
                        <td colspan="8" class="text-center text-muted py-5">
                            <i class="fas fa-search fa-2x mb-2"></i><br>
                            ${this.results.length === 0 ? 'No hay resultados para mostrar' : 'No hay resultados que coincidan con los filtros'}
                        </td>
                    </tr>
                `;
                this.updateResultsCountDisplay(0);
                return;
            }

            // Mostrar TODOS los resultados sin limitación
            const html = this.filteredResults.map(result => this.renderResultRow(result)).join('');
            this.resultsTable.innerHTML = html;
            
            this.attachEventListeners();
            this.updateSummary();
            this.updateResultsCountDisplay(this.filteredResults.length);
            this.setupScrollButtons();
        }

        /**
         * Actualizar contador de resultados
         */
        updateResultsCountDisplay(count) {
            const resultsCountElement = document.getElementById('resultsCount');
            if (resultsCountElement) {
                resultsCountElement.textContent = `${count} resultado${count !== 1 ? 's' : ''}`;
            }
        }

        /**
         * Configurar botones de scroll
         */
        setupScrollButtons() {
            const scrollToTopBtn = document.getElementById('scrollToTopBtn');
            const scrollToBottomBtn = document.getElementById('scrollToBottomBtn');
            const tableContainer = document.getElementById('resultsTableContainer');
            
            if (scrollToTopBtn && tableContainer) {
                scrollToTopBtn.addEventListener('click', () => {
                    tableContainer.scrollTo({
                        top: 0,
                        behavior: 'smooth'
                    });
                    console.log('📄 Scroll hacia arriba activado');
                });
            }
            
            if (scrollToBottomBtn && tableContainer) {
                scrollToBottomBtn.addEventListener('click', () => {
                    tableContainer.scrollTo({
                        top: tableContainer.scrollHeight,
                        behavior: 'smooth'
                    });
                    console.log('📄 Scroll hacia abajo activado');
                });
            }
            
            // Mostrar/ocultar botones según posición de scroll
            if (tableContainer) {
                tableContainer.addEventListener('scroll', () => {
                    this.updateScrollButtons();
                });
            }
        }

        /**
         * Actualizar estado de botones de scroll
         */
        updateScrollButtons() {
            const scrollToTopBtn = document.getElementById('scrollToTopBtn');
            const scrollToBottomBtn = document.getElementById('scrollToBottomBtn');
            const tableContainer = document.getElementById('resultsTableContainer');
            
            if (!tableContainer || !scrollToTopBtn || !scrollToBottomBtn) return;
            
            const isAtTop = tableContainer.scrollTop === 0;
            const isAtBottom = tableContainer.scrollTop + tableContainer.clientHeight >= tableContainer.scrollHeight - 1;
            
            scrollToTopBtn.disabled = isAtTop;
            scrollToBottomBtn.disabled = isAtBottom;
            
            // Actualizar indicadores visuales
            scrollToTopBtn.classList.toggle('btn-outline-primary', isAtTop);
            scrollToTopBtn.classList.toggle('btn-primary', !isAtTop);
            
            scrollToBottomBtn.classList.toggle('btn-outline-primary', isAtBottom);
            scrollToBottomBtn.classList.toggle('btn-primary', !isAtBottom);
        }

        /**
         * Renderizar fila de resultado
         */
        renderResultRow(result) {
            const statusClass = this.getStatusClass(result.status);
            const statusIcon = this.getStatusIcon(result.status);
            const displayMonto = result.monto ? `${result.monto}` : '-';
            
            return `
                <tr class="result-row" data-result-id="${result.id}">
                    <td>${result.numero_llegada}</td>
                    <td>
                        <div class="result-filename" title="${result.filename}">
                            ${this.truncateText(result.filename, 30)}
                        </div>
                        <small class="text-muted">${result.caption}</small>
                    </td>
                    <!-- COLUMNA 'CÓDIGO' OCULTA POR SOLICITUD DEL USUARIO -->
                    <td>
                        <div class="result-usuario" title="${result.nombre_usuario}">
                            ${result.nombre_usuario || '-'}
                        </div>
                        <small class="text-muted">${result.hora_exacta}</small>
                    </td>
                    <td>
                        <div class="result-monto">${displayMonto}</div>
                    </td>
                    <td>
                        <div class="result-banco" title="${result.bancoorigen}">
                            ${this.truncateText(result.bancoorigen, 20)}
                        </div>
                    </td>
                    <td>
                        <div class="result-lote" title="${result.lote_id}">
                            ${this.truncateText(result.lote_id, 15)}
                        </div>
                        <small class="text-muted">${new Date(result.lote_fecha).toLocaleDateString()}</small>
                    </td>
                    <td>
                        <span class="result-status ${statusClass}">
                            <i class="fas ${statusIcon}"></i>
                            ${this.getStatusText(result.status)}
                        </span>
                    </td>
                    <td>
                        <div class="result-actions">
                            <!-- BOTÓN 'VER DETALLES' RESTAURADO POR SOLICITUD DEL USUARIO -->
                            <button type="button" class="btn btn-sm btn-view view-result-btn" 
                                    data-result-id="${result.id}" title="Ver detalles">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-download download-result-btn" 
                                    data-result-id="${result.id}" title="Descargar JSON">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }

        /**
         * Adjuntar event listeners a elementos dinámicos
         */
        attachEventListeners() {
            // BOTONES DE VER DETALLES RESTAURADOS POR SOLICITUD DEL USUARIO
            document.querySelectorAll('.view-result-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const resultId = parseInt(e.target.closest('.view-result-btn').getAttribute('data-result-id'));
                    this.showResultDetails(resultId);
                });
            });
            
            // Botones de descarga
            document.querySelectorAll('.download-result-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const resultId = parseInt(e.target.closest('.download-result-btn').getAttribute('data-result-id'));
                    this.downloadResult(resultId);
                });
            });
        }

        /**
         * Mostrar detalles de un resultado
         */
        showResultDetails(resultId) {
            const result = this.filteredResults.find(r => r.id === resultId);
            if (!result) return;

            // Crear modal dinámicamente si no existe
            let modal = document.getElementById('resultDetailModal');
            if (!modal) {
                modal = this.createDetailModal();
                document.body.appendChild(modal);
            }

            // Poblar modal con datos
            this.populateDetailModal(result);
            
            // Mostrar modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }

        /**
         * Crear modal de detalles
         */
        createDetailModal() {
            const modalHTML = `
                <div class="modal fade result-detail-modal" id="resultDetailModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-file-alt me-2"></i>Detalles del Resultado
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body" id="resultDetailContent">
                                <!-- El contenido se carga dinámicamente -->
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                                <button type="button" class="btn btn-primary" id="downloadDetailBtn">
                                    <i class="fas fa-download me-2"></i>Descargar JSON
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            const modalElement = document.createElement('div');
            modalElement.innerHTML = modalHTML;
            return modalElement.firstElementChild;
        }

        /**
         * Poblar modal con datos del resultado
         */
        populateDetailModal(result) {
            const content = document.getElementById('resultDetailContent');
            if (!content) return;

            content.innerHTML = `
                <div class="detail-section">
                    <h6><i class="fas fa-info-circle me-2"></i>Información del Archivo</h6>
                    <div class="detail-field">
                        <span class="label">Nombre del Archivo:</span>
                        <span class="value">${result.filename}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Número de Llegada:</span>
                        <span class="value">${result.numero_llegada}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Caption:</span>
                        <span class="value">${result.caption}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h6><i class="fas fa-user me-2"></i>Parámetros de Seguimiento</h6>
                    <div class="detail-field">
                        <span class="label">Código de Sorteo:</span>
                        <span class="value">${result.codigo_sorteo}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">ID WhatsApp:</span>
                        <span class="value">${result.id_whatsapp}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Nombre de Usuario:</span>
                        <span class="value">${result.nombre_usuario}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Hora Exacta:</span>
                        <span class="value">${result.hora_exacta}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h6><i class="fas fa-credit-card me-2"></i>Datos Extraídos</h6>
                    <div class="detail-field">
                        <span class="label">Referencia:</span>
                        <span class="value">${result.referencia}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Monto:</span>
                        <span class="value">${result.monto}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Banco Origen:</span>
                        <span class="value">${result.bancoorigen}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Banco Destino:</span>
                        <span class="value">${result.banco_destino}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Cédula:</span>
                        <span class="value">${result.cedula}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Teléfono:</span>
                        <span class="value">${result.telefono}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Fecha de Pago:</span>
                        <span class="value">${result.pago_fecha}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Concepto:</span>
                        <span class="value">${result.concepto}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h6><i class="fas fa-chart-line me-2"></i>Estadísticas</h6>
                    <div class="detail-field">
                        <span class="label">Confianza OCR:</span>
                        <span class="value">${(result.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Palabras Detectadas:</span>
                        <span class="value">${result.total_words}</span>
                    </div>
                    <div class="detail-field">
                        <span class="label">Tiempo de Procesamiento:</span>
                        <span class="value">${result.processing_time.toFixed(3)}s</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h6><i class="fas fa-align-left me-2"></i>Texto OCR Completo</h6>
                    <div class="border rounded p-3 bg-light" style="max-height: 200px; overflow-y: auto;">
                        <pre class="mb-0" style="white-space: pre-wrap; font-size: 0.875rem;">${result.texto_total_ocr}</pre>
                    </div>
                </div>
            `;

            // Configurar botón de descarga
            const downloadBtn = document.getElementById('downloadDetailBtn');
            if (downloadBtn) {
                downloadBtn.onclick = () => this.downloadResult(result.id);
            }
        }

        /**
         * Descargar resultado como JSON
         */
        downloadResult(resultId) {
            const result = this.filteredResults.find(r => r.id === resultId);
            if (!result) return;

            try {
                const blob = new Blob([JSON.stringify(result.raw_data, null, 2)], {
                    type: 'application/json'
                });

                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `resultado_${result.filename.replace(/\.[^/.]+$/, "")}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);

                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        `Resultado descargado: ${result.filename}`,
                        'success'
                    );
                }
            } catch (error) {
                console.error('❌ Error descargando resultado:', error);
                if (window.OCRSystem.Main) {
                    window.OCRSystem.Main.showNotification(
                        'Error al descargar el resultado',
                        'error'
                    );
                }
            }
        }

        /**
         * Actualizar resumen de estadísticas
         */
        updateSummary() {
            const stats = this.calculateStats();
            
            // Actualizar elementos de resumen si existen
            const totalProcessed = document.getElementById('totalProcessed');
            const totalSuccess = document.getElementById('totalSuccess');
            const totalErrors = document.getElementById('totalErrors');
            const successRate = document.getElementById('successRate');
            
            if (totalProcessed) totalProcessed.textContent = stats.total;
            if (totalSuccess) totalSuccess.textContent = stats.success;
            if (totalErrors) totalErrors.textContent = stats.errors;
            if (successRate) successRate.textContent = stats.successRate;
        }

        /**
         * Calcular estadísticas de resultados
         */
        calculateStats() {
            const total = this.filteredResults.length;
            const success = this.filteredResults.filter(r => r.status === 'success').length;
            const errors = this.filteredResults.filter(r => r.status === 'error').length;
            const successRate = total > 0 ? ((success / total) * 100).toFixed(1) + '%' : '0%';

            return { total, success, errors, successRate };
        }

        /**
         * Mostrar/ocultar indicador de carga
         */
        showLoading(show) {
            // Implementar indicador de carga si es necesario
            const loadingElement = document.querySelector('.results-loading');
            if (loadingElement) {
                loadingElement.style.display = show ? 'flex' : 'none';
            }
        }

        /**
         * Mostrar mensaje de error
         */
        showError(message) {
            if (window.OCRSystem.Main) {
                window.OCRSystem.Main.showNotification(message, 'error');
            } else {
                console.error('❌', message);
            }
        }

        /**
         * Obtener clase CSS para estado
         */
        getStatusClass(status) {
            const classes = {
                success: 'success',
                warning: 'warning',
                error: 'error'
            };
            return classes[status] || 'error';
        }

        /**
         * Obtener icono para estado
         */
        getStatusIcon(status) {
            const icons = {
                success: 'fa-check-circle',
                warning: 'fa-exclamation-triangle',
                error: 'fa-times-circle'
            };
            return icons[status] || 'fa-times-circle';
        }

        /**
         * Obtener texto para estado
         */
        getStatusText(status) {
            const texts = {
                success: 'Exitoso',
                warning: 'Advertencia',
                error: 'Error'
            };
            return texts[status] || 'Error';
        }

        /**
         * Truncar texto
         */
        truncateText(text, maxLength) {
            if (!text || text.length <= maxLength) return text || '-';
            return text.substring(0, maxLength - 3) + '...';
        }

        /**
         * Obtener resultados actuales
         */
        getResults() {
            return [...this.filteredResults];
        }

        /**
         * Obtener número de resultados
         */
        getResultCount() {
            return this.filteredResults.length;
        }

        /**
         * Limpiar resultados
         */
        clear() {
            this.results = [];
            this.filteredResults = [];
            this.updateDisplay();
        }
    }

    // Exportar el Results Viewer
    window.OCRSystem.ResultsViewer = ResultsViewer;

    console.log('📊 Results Viewer module loaded');

})();