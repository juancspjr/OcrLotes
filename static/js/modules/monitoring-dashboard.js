/**
 * MONITORING DASHBOARD MODULE - SISTEMA OCR EMPRESARIAL
 * FILOSOFÍA: INTEGRIDAD TOTAL + INTERFACE EXCELLENCE
 * 
 * Módulo encargado del monitoreo avanzado del sistema con métricas,
 * estado de componentes y análisis de rendimiento en tiempo real.
 */

window.OCRSystem = window.OCRSystem || {};

(function() {
    'use strict';

    class MonitoringDashboard {
        constructor(config) {
            this.config = config;
            this.apiClient = config.apiClient;
            this.refreshInterval = null;
            this.isAutoRefreshEnabled = true;
            this.refreshRate = 10000; // 10 segundos
            
            this.init();
        }

        init() {
            this.setupAutoRefresh();
            console.log('📈 Monitoring Dashboard inicializado');
        }

        /**
         * Configurar actualización automática
         */
        setupAutoRefresh() {
            if (this.isAutoRefreshEnabled) {
                this.refreshInterval = setInterval(() => {
                    // Solo actualizar si la pestaña de monitoreo está activa
                    const monitoringTab = document.getElementById('monitoringSection');
                    if (monitoringTab && monitoringTab.classList.contains('active')) {
                        this.refresh();
                    }
                }, this.refreshRate);
            }
        }

        /**
         * Refrescar todos los datos del dashboard
         */
        async refresh() {
            try {
                console.log('📈 Refrescando dashboard de monitoreo...');
                
                await Promise.all([
                    this.updateSystemMetrics(),
                    this.updateSystemStatus(),
                    this.updateBatchHistory()
                ]);
                
            } catch (error) {
                console.error('❌ Error refrescando dashboard:', error);
                this.showError('Error actualizando métricas del sistema');
            }
        }

        /**
         * Actualizar métricas del sistema
         */
        async updateSystemMetrics() {
            try {
                const metrics = await this.apiClient.getSystemMetrics();
                
                // Actualizar contadores principales
                this.updateElement('totalProcessed', metrics.totalProcessed || 0);
                this.updateElement('totalSuccess', metrics.totalSuccess || 0);
                this.updateElement('totalErrors', metrics.totalErrors || 0);
                this.updateElement('successRate', metrics.successRate || '0%');
                
                // Actualizar indicadores visuales
                this.updateSuccessRateIndicator(metrics.successRate);
                
            } catch (error) {
                console.error('❌ Error obteniendo métricas:', error);
                // Mostrar valores por defecto en caso de error
                this.updateElement('totalProcessed', 0);
                this.updateElement('totalSuccess', 0);
                this.updateElement('totalErrors', 0);
                this.updateElement('successRate', '0%');
            }
        }

        /**
         * Actualizar estado de componentes del sistema
         */
        async updateSystemStatus() {
            try {
                const systemInfo = await this.apiClient.getSystemInfo();
                
                // Estado del worker OCR
                this.updateStatusBadge('workerStatus', 
                    systemInfo.backend_status === 'ok' ? 'Activo' : 'Inactivo',
                    systemInfo.backend_status === 'ok' ? 'success' : 'danger'
                );
                
                // Estado de la base de datos
                this.updateStatusBadge('dbStatus', 
                    systemInfo.backend_status === 'ok' ? 'Conectado' : 'Desconectado',
                    systemInfo.backend_status === 'ok' ? 'success' : 'danger'
                );
                
                // Estado de la API
                this.updateStatusBadge('apiStatus',
                    systemInfo.backend_status === 'ok' ? 'Operativo' : 'Error',
                    systemInfo.backend_status === 'ok' ? 'success' : 'danger'
                );
                
                // Actualizar latencia si está disponible
                if (systemInfo.latency !== null) {
                    this.updateLatencyIndicator(systemInfo.latency);
                }
                
            } catch (error) {
                console.error('❌ Error obteniendo estado del sistema:', error);
                
                // Mostrar estados de error
                this.updateStatusBadge('workerStatus', 'Error', 'danger');
                this.updateStatusBadge('dbStatus', 'Error', 'danger');
                this.updateStatusBadge('apiStatus', 'Error', 'danger');
            }
        }

        /**
         * Actualizar historial de lotes
         */
        async updateBatchHistory() {
            try {
                const batches = await this.apiClient.getBatchHistory();
                this.renderBatchHistory(batches.slice(0, 10)); // Mostrar últimos 10 lotes
                
            } catch (error) {
                console.error('❌ Error obteniendo historial de lotes:', error);
                this.renderBatchHistory([]);
            }
        }

        /**
         * Renderizar historial de lotes
         */
        renderBatchHistory(batches) {
            const batchHistoryBody = document.getElementById('batchHistoryBody');
            if (!batchHistoryBody) return;

            if (batches.length === 0) {
                batchHistoryBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-muted py-4">
                            <i class="fas fa-clock fa-2x mb-2"></i><br>
                            No hay historial disponible
                        </td>
                    </tr>
                `;
                return;
            }

            const html = batches.map(batch => this.renderBatchRow(batch)).join('');
            batchHistoryBody.innerHTML = html;
        }

        /**
         * Renderizar fila de lote
         */
        renderBatchRow(batch) {
            const date = new Date(batch.date);
            const processingTime = this.calculateProcessingTime(batch);
            const successRate = batch.totalFiles > 0 ? 
                ((batch.successCount / batch.totalFiles) * 100).toFixed(1) : 0;

            return `
                <tr class="batch-row" data-batch-id="${batch.id}">
                    <td>
                        <span class="font-monospace small">${this.truncateText(batch.id, 20)}</span>
                    </td>
                    <td>
                        <div>${date.toLocaleDateString()}</div>
                        <small class="text-muted">${date.toLocaleTimeString()}</small>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-info">${batch.totalFiles}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-success">${batch.successCount}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-danger">${batch.errorCount}</span>
                    </td>
                    <td class="text-center">
                        <span class="text-muted">${processingTime}</span>
                    </td>
                    <td class="text-center">
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-sm btn-outline-primary view-batch-btn" 
                                    data-batch-id="${batch.id}" title="Ver detalles">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-success download-batch-btn" 
                                    data-batch-id="${batch.id}" title="Descargar lote">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }

        /**
         * Calcular tiempo de procesamiento estimado
         */
        calculateProcessingTime(batch) {
            // Estimación basada en número de archivos (placeholder)
            const avgTimePerFile = 0.5; // 500ms por archivo
            const estimatedTime = batch.totalFiles * avgTimePerFile;
            
            if (estimatedTime < 60) {
                return `${estimatedTime.toFixed(1)}s`;
            } else {
                return `${(estimatedTime / 60).toFixed(1)}m`;
            }
        }

        /**
         * Actualizar indicador de tasa de éxito
         */
        updateSuccessRateIndicator(successRate) {
            const rateValue = parseFloat(successRate) || 0;
            const element = document.getElementById('successRate');
            
            if (element) {
                // Cambiar color según la tasa de éxito
                element.className = 'h4';
                if (rateValue >= 90) {
                    element.className += ' text-success';
                } else if (rateValue >= 70) {
                    element.className += ' text-warning';
                } else {
                    element.className += ' text-danger';
                }
            }
        }

        /**
         * Actualizar indicador de latencia
         */
        updateLatencyIndicator(latency) {
            // Crear elemento de latencia si no existe
            let latencyElement = document.getElementById('systemLatency');
            if (!latencyElement) {
                const systemStatusCard = document.querySelector('.card-header:contains("Estado del Sistema")')?.parentElement;
                if (systemStatusCard) {
                    const latencyHTML = `
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <div class="fw-bold">Latencia</div>
                                <div class="text-muted small">Tiempo de respuesta</div>
                            </div>
                            <span class="badge bg-info" id="systemLatency">${latency}ms</span>
                        </div>
                    `;
                    systemStatusCard.querySelector('.card-body').insertAdjacentHTML('beforeend', latencyHTML);
                }
            } else {
                latencyElement.textContent = `${latency}ms`;
                
                // Cambiar color según latencia
                latencyElement.className = 'badge';
                if (latency < 100) {
                    latencyElement.className += ' bg-success';
                } else if (latency < 500) {
                    latencyElement.className += ' bg-warning';
                } else {
                    latencyElement.className += ' bg-danger';
                }
            }
        }

        /**
         * Actualizar elemento DOM con valor
         */
        updateElement(elementId, value) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = value;
                
                // Añadir animación de actualización
                element.classList.add('updating');
                setTimeout(() => {
                    element.classList.remove('updating');
                }, 300);
            }
        }

        /**
         * Actualizar badge de estado
         */
        updateStatusBadge(elementId, text, type) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = text;
                element.className = `badge bg-${type}`;
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
         * Truncar texto
         */
        truncateText(text, maxLength) {
            if (!text || text.length <= maxLength) return text || '-';
            return text.substring(0, maxLength - 3) + '...';
        }

        /**
         * Habilitar/deshabilitar actualización automática
         */
        toggleAutoRefresh(enabled) {
            this.isAutoRefreshEnabled = enabled;
            
            if (enabled) {
                this.setupAutoRefresh();
            } else {
                if (this.refreshInterval) {
                    clearInterval(this.refreshInterval);
                    this.refreshInterval = null;
                }
            }
        }

        /**
         * Cambiar tasa de actualización
         */
        setRefreshRate(rateMs) {
            this.refreshRate = rateMs;
            
            if (this.isAutoRefreshEnabled) {
                // Reiniciar intervalo con nueva tasa
                this.toggleAutoRefresh(false);
                this.toggleAutoRefresh(true);
            }
        }

        /**
         * Obtener estadísticas actuales
         */
        getCurrentStats() {
            return {
                totalProcessed: this.getElementValue('totalProcessed'),
                totalSuccess: this.getElementValue('totalSuccess'),
                totalErrors: this.getElementValue('totalErrors'),
                successRate: this.getElementValue('successRate')
            };
        }

        /**
         * Obtener valor de elemento DOM
         */
        getElementValue(elementId) {
            const element = document.getElementById(elementId);
            return element ? element.textContent : null;
        }

        /**
         * Destruir instancia y limpiar recursos
         */
        destroy() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        }
    }

    // Exportar el Monitoring Dashboard
    window.OCRSystem.MonitoringDashboard = MonitoringDashboard;

    console.log('📈 Monitoring Dashboard module loaded');

})();