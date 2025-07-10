/**
 * MONITORING DASHBOARD - SISTEMA OCR EMPRESARIAL
 * Módulo para monitoreo avanzado de recursos por lote con visualización gráfica
 * FILOSOFÍA: PERFECCIÓN CONTINUA + TRANSPARENCIA TOTAL + PULSO DE INFORMACIÓN
 */

class MonitoringDashboard {
    constructor() {
        this.charts = {};
        this.batchMetrics = [];
        this.realTimeMetrics = null;
        this.pollingInterval = null;
        this.pollingFrequency = 5000; // 5 segundos
        this.maxDataPoints = 50; // Máximo de lotes a mostrar en gráficos
        this.isPolling = false;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeCharts();
    }

    /**
     * INICIALIZACIÓN DE ELEMENTOS DOM
     */
    initializeElements() {
        this.elements = {
            // Contenedores principales
            metricsContainer: document.getElementById('metricsContainer'),
            chartsContainer: document.getElementById('chartsContainer'),
            batchLogContainer: document.getElementById('batchLogContainer'),
            
            // Gráficos específicos
            cpuChart: document.getElementById('cpuChart'),
            memoryChart: document.getElementById('memoryChart'),
            processingTimeChart: document.getElementById('processingTimeChart'),
            confidenceChart: document.getElementById('confidenceChart'),
            
            // Controles
            togglePollingBtn: document.getElementById('togglePollingBtn'),
            refreshMetricsBtn: document.getElementById('refreshMetricsBtn'),
            clearLogBtn: document.getElementById('clearLogBtn'),
            
            // Métricas en tiempo real
            systemCpuValue: document.getElementById('systemCpuValue'),
            systemMemoryValue: document.getElementById('systemMemoryValue'),
            systemDiskValue: document.getElementById('systemDiskValue'),
            queueStatusValue: document.getElementById('queueStatusValue'),
            
            // Log de lotes
            batchLog: document.getElementById('batchLog')
        };
    }

    /**
     * BIND DE EVENTOS
     */
    bindEvents() {
        // Control de polling
        if (this.elements.togglePollingBtn) {
            this.elements.togglePollingBtn.addEventListener('click', () => {
                this.togglePolling();
            });
        }

        // Refresh manual
        if (this.elements.refreshMetricsBtn) {
            this.elements.refreshMetricsBtn.addEventListener('click', () => {
                this.refreshMetrics();
            });
        }

        // Limpiar log
        if (this.elements.clearLogBtn) {
            this.elements.clearLogBtn.addEventListener('click', () => {
                this.clearBatchLog();
            });
        }

        // Escuchar eventos de lotes completados
        window.addEventListener('batchCompleted', (e) => {
            this.handleBatchCompleted(e.detail);
        });

        // Escuchar eventos de estado de queue
        window.addEventListener('queueStatusUpdate', (e) => {
            this.updateQueueStatus(e.detail);
        });
    }

    /**
     * INICIALIZAR GRÁFICOS CHART.JS
     */
    initializeCharts() {
        // Configuración común para todos los gráficos
        const commonConfig = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Lotes'
                    }
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false
            }
        };

        // Gráfico de CPU
        if (this.elements.cpuChart) {
            this.charts.cpu = new Chart(this.elements.cpuChart, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU Usage (%)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    ...commonConfig,
                    scales: {
                        ...commonConfig.scales,
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'CPU (%)'
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de Memoria
        if (this.elements.memoryChart) {
            this.charts.memory = new Chart(this.elements.memoryChart, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Memory Usage (MB)',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    ...commonConfig,
                    scales: {
                        ...commonConfig.scales,
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Memoria (MB)'
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de Tiempo de Procesamiento
        if (this.elements.processingTimeChart) {
            this.charts.processingTime = new Chart(this.elements.processingTimeChart, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Processing Time (s)',
                        data: [],
                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                        borderColor: 'rgb(75, 192, 192)',
                        borderWidth: 1
                    }]
                },
                options: {
                    ...commonConfig,
                    scales: {
                        ...commonConfig.scales,
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Tiempo (segundos)'
                            }
                        }
                    }
                }
            });
        }

        // Gráfico de Confianza Promedio
        if (this.elements.confidenceChart) {
            this.charts.confidence = new Chart(this.elements.confidenceChart, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Avg Confidence (%)',
                        data: [],
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    ...commonConfig,
                    scales: {
                        ...commonConfig.scales,
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Confianza (%)'
                            }
                        }
                    }
                }
            });
        }
    }

    /**
     * INICIAR/DETENER POLLING DE MÉTRICAS
     */
    togglePolling() {
        if (this.isPolling) {
            this.stopPolling();
        } else {
            this.startPolling();
        }
    }

    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this.updatePollingButton();
        
        // Primera actualización inmediata
        this.refreshMetrics();
        
        // Configurar polling
        this.pollingInterval = setInterval(() => {
            this.refreshMetrics();
        }, this.pollingFrequency);
        
        this.logBatchEvent('🟢 Monitoreo en tiempo real activado', 'success');
    }

    stopPolling() {
        if (!this.isPolling) return;
        
        this.isPolling = false;
        this.updatePollingButton();
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        this.logBatchEvent('🔴 Monitoreo en tiempo real desactivado', 'info');
    }

    updatePollingButton() {
        if (!this.elements.togglePollingBtn) return;
        
        if (this.isPolling) {
            this.elements.togglePollingBtn.innerHTML = '<i class="fas fa-pause me-1"></i>Detener Monitoreo';
            this.elements.togglePollingBtn.className = 'btn btn-warning';
        } else {
            this.elements.togglePollingBtn.innerHTML = '<i class="fas fa-play me-1"></i>Iniciar Monitoreo';
            this.elements.togglePollingBtn.className = 'btn btn-success';
        }
    }

    /**
     * ACTUALIZAR MÉTRICAS DEL SISTEMA
     */
    async refreshMetrics() {
        try {
            // Obtener estado de cola (que incluye métricas del sistema)
            const queueData = await window.apiClient.getQueueStatus();
            
            if (queueData.system_info) {
                this.updateSystemMetrics(queueData.system_info);
            }
            
            if (queueData.queue_status) {
                this.updateQueueStatus(queueData.queue_status);
            }

            // Intentar obtener métricas específicas de lotes
            try {
                const batchMetrics = await window.apiClient.getBatchMetrics();
                if (batchMetrics && batchMetrics.length > 0) {
                    this.updateBatchMetrics(batchMetrics);
                }
            } catch (error) {
                // El endpoint de métricas de lotes puede no estar implementado aún
                console.log('Métricas de lotes no disponibles:', error.message);
            }

        } catch (error) {
            console.error('Error actualizando métricas:', error);
            this.logBatchEvent(`❌ Error actualizando métricas: ${error.getUserMessage()}`, 'error');
        }
    }

    /**
     * ACTUALIZAR MÉTRICAS DEL SISTEMA EN TIEMPO REAL
     */
    updateSystemMetrics(systemInfo) {
        this.realTimeMetrics = {
            ...systemInfo,
            timestamp: new Date().toISOString()
        };

        // Actualizar valores en la UI
        if (this.elements.systemCpuValue) {
            const cpuUsage = systemInfo.cpu_usage || 0;
            this.elements.systemCpuValue.textContent = `${cpuUsage.toFixed(1)}%`;
            this.elements.systemCpuValue.className = this.getCpuUsageClass(cpuUsage);
        }

        if (this.elements.systemMemoryValue) {
            const memoryUsage = systemInfo.memory_usage || 0;
            this.elements.systemMemoryValue.textContent = `${this.formatMemory(memoryUsage)}`;
            this.elements.systemMemoryValue.className = this.getMemoryUsageClass(memoryUsage);
        }

        if (this.elements.systemDiskValue) {
            const diskUsage = systemInfo.disk_usage || 0;
            this.elements.systemDiskValue.textContent = `${diskUsage.toFixed(1)}%`;
            this.elements.systemDiskValue.className = this.getDiskUsageClass(diskUsage);
        }

        // Actualizar indicador de worker
        this.updateWorkerStatus(systemInfo.worker_status === 'running');
    }

    /**
     * ACTUALIZAR ESTADO DE COLA
     */
    updateQueueStatus(queueStatus) {
        if (this.elements.queueStatusValue) {
            const total = (queueStatus.inbox || 0) + (queueStatus.processing || 0) + (queueStatus.completed || 0);
            this.elements.queueStatusValue.innerHTML = `
                <div class="queue-stats">
                    <span class="badge bg-secondary me-1">${queueStatus.inbox || 0} pendientes</span>
                    <span class="badge bg-warning me-1">${queueStatus.processing || 0} procesando</span>
                    <span class="badge bg-success">${queueStatus.completed || 0} completados</span>
                </div>
            `;
        }
    }

    /**
     * ACTUALIZAR MÉTRICAS DE LOTES
     */
    updateBatchMetrics(newMetrics) {
        // Agregar nuevas métricas al historial
        if (Array.isArray(newMetrics)) {
            this.batchMetrics = [...this.batchMetrics, ...newMetrics];
        } else {
            this.batchMetrics.push(newMetrics);
        }

        // Mantener solo los últimos maxDataPoints
        if (this.batchMetrics.length > this.maxDataPoints) {
            this.batchMetrics = this.batchMetrics.slice(-this.maxDataPoints);
        }

        // Actualizar gráficos
        this.updateCharts();
    }

    /**
     * MANEJAR EVENTO DE LOTE COMPLETADO
     */
    handleBatchCompleted(batchData) {
        // Crear métrica simulada del lote basada en los datos del backend
        const batchMetric = {
            batch_id: batchData.batch_id || batchData.request_id,
            timestamp_processed: new Date().toISOString(),
            num_images_processed: batchData.batch_info?.processed_count || 0,
            cpu_usage_avg_percent: this.realTimeMetrics?.cpu_usage || 0,
            memory_usage_avg_mb: this.realTimeMetrics?.memory_usage || 0,
            batch_processing_time_sec: batchData.batch_info?.processing_time_total || 0,
            num_errors_in_batch: batchData.batch_info?.error_count || 0,
            avg_confidence_percent: batchData.batch_info?.avg_confidence * 100 || 0
        };

        // Agregar al historial
        this.updateBatchMetrics(batchMetric);

        // Log del evento
        const logMessage = `🚀 Lote completado: ${batchMetric.num_images_processed} archivos en ${batchMetric.batch_processing_time_sec.toFixed(2)}s`;
        this.logBatchEvent(logMessage, 'success');
    }

    /**
     * ACTUALIZAR TODOS LOS GRÁFICOS
     */
    updateCharts() {
        if (this.batchMetrics.length === 0) return;

        // Preparar datos para gráficos
        const labels = this.batchMetrics.map((metric, index) => {
            const batchNum = metric.batch_id ? metric.batch_id.split('_')[2] || (index + 1) : (index + 1);
            return `L${batchNum}`;
        });

        // Actualizar gráfico de CPU
        if (this.charts.cpu) {
            this.charts.cpu.data.labels = labels;
            this.charts.cpu.data.datasets[0].data = this.batchMetrics.map(m => m.cpu_usage_avg_percent || 0);
            this.charts.cpu.update('none');
        }

        // Actualizar gráfico de Memoria
        if (this.charts.memory) {
            this.charts.memory.data.labels = labels;
            this.charts.memory.data.datasets[0].data = this.batchMetrics.map(m => m.memory_usage_avg_mb || 0);
            this.charts.memory.update('none');
        }

        // Actualizar gráfico de Tiempo de Procesamiento
        if (this.charts.processingTime) {
            this.charts.processingTime.data.labels = labels;
            this.charts.processingTime.data.datasets[0].data = this.batchMetrics.map(m => m.batch_processing_time_sec || 0);
            this.charts.processingTime.update('none');
        }

        // Actualizar gráfico de Confianza
        if (this.charts.confidence) {
            this.charts.confidence.data.labels = labels;
            this.charts.confidence.data.datasets[0].data = this.batchMetrics.map(m => m.avg_confidence_percent || 0);
            this.charts.confidence.update('none');
        }
    }

    /**
     * LOG DE EVENTOS DE LOTES
     */
    logBatchEvent(message, type = 'info') {
        if (!this.elements.batchLog) return;

        const timestamp = new Date().toLocaleTimeString('es-ES');
        const typeClass = this.getLogTypeClass(type);
        const icon = this.getLogTypeIcon(type);

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type} p-2 mb-1 rounded`;
        logEntry.innerHTML = `
            <div class="d-flex align-items-start">
                <span class="${typeClass} me-2">${icon}</span>
                <div class="flex-grow-1">
                    <span class="log-message">${this.escapeHtml(message)}</span>
                    <small class="log-time text-muted ms-2">${timestamp}</small>
                </div>
            </div>
        `;

        // Agregar al inicio del log
        this.elements.batchLog.insertBefore(logEntry, this.elements.batchLog.firstChild);

        // Mantener solo las últimas 100 entradas
        const entries = this.elements.batchLog.children;
        if (entries.length > 100) {
            this.elements.batchLog.removeChild(entries[entries.length - 1]);
        }

        // Auto-scroll si estaba al inicio
        if (this.elements.batchLog.scrollTop < 50) {
            this.elements.batchLog.scrollTop = 0;
        }
    }

    /**
     * LIMPIAR LOG DE LOTES
     */
    clearBatchLog() {
        if (this.elements.batchLog) {
            this.elements.batchLog.innerHTML = `
                <div class="log-entry text-center text-muted p-3">
                    <i class="fas fa-broom me-2"></i>Log limpiado
                </div>
            `;
        }
    }

    /**
     * ACTUALIZAR ESTADO DEL WORKER
     */
    updateWorkerStatus(isRunning) {
        const workerIndicator = document.getElementById('workerStatus');
        if (workerIndicator) {
            if (isRunning) {
                workerIndicator.innerHTML = '<i class="fas fa-circle text-success me-1"></i>Activo';
                workerIndicator.className = 'badge bg-success';
            } else {
                workerIndicator.innerHTML = '<i class="fas fa-circle text-danger me-1"></i>Inactivo';
                workerIndicator.className = 'badge bg-danger';
            }
        }
    }

    /**
     * UTILIDADES PARA CLASES CSS
     */
    getCpuUsageClass(usage) {
        if (usage > 80) return 'text-danger fw-bold';
        if (usage > 60) return 'text-warning fw-bold';
        return 'text-success fw-bold';
    }

    getMemoryUsageClass(usage) {
        if (usage > 2048) return 'text-danger fw-bold'; // > 2GB
        if (usage > 1024) return 'text-warning fw-bold'; // > 1GB
        return 'text-success fw-bold';
    }

    getDiskUsageClass(usage) {
        if (usage > 85) return 'text-danger fw-bold';
        if (usage > 70) return 'text-warning fw-bold';
        return 'text-success fw-bold';
    }

    getLogTypeClass(type) {
        const classes = {
            success: 'text-success',
            error: 'text-danger',
            warning: 'text-warning',
            info: 'text-info'
        };
        return classes[type] || classes.info;
    }

    getLogTypeIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    /**
     * UTILIDADES DE FORMATO
     */
    formatMemory(mb) {
        if (mb < 1024) return `${mb.toFixed(0)} MB`;
        return `${(mb / 1024).toFixed(1)} GB`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * OBTENER ESTADÍSTICAS DEL DASHBOARD
     */
    getMetricsStats() {
        if (this.batchMetrics.length === 0) {
            return {
                totalBatches: 0,
                avgProcessingTime: 0,
                avgCpuUsage: 0,
                avgMemoryUsage: 0,
                avgConfidence: 0
            };
        }

        const metrics = this.batchMetrics;
        return {
            totalBatches: metrics.length,
            avgProcessingTime: metrics.reduce((sum, m) => sum + (m.batch_processing_time_sec || 0), 0) / metrics.length,
            avgCpuUsage: metrics.reduce((sum, m) => sum + (m.cpu_usage_avg_percent || 0), 0) / metrics.length,
            avgMemoryUsage: metrics.reduce((sum, m) => sum + (m.memory_usage_avg_mb || 0), 0) / metrics.length,
            avgConfidence: metrics.reduce((sum, m) => sum + (m.avg_confidence_percent || 0), 0) / metrics.length
        };
    }

    /**
     * EXPORTAR MÉTRICAS
     */
    exportMetrics() {
        const stats = this.getMetricsStats();
        const exportData = {
            timestamp: new Date().toISOString(),
            summary: stats,
            batchMetrics: this.batchMetrics,
            realTimeMetrics: this.realTimeMetrics
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `metricas_sistema_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.logBatchEvent('📊 Métricas exportadas exitosamente', 'success');
    }

    /**
     * RESETEAR MÉTRICAS
     */
    resetMetrics() {
        this.batchMetrics = [];
        this.updateCharts();
        this.clearBatchLog();
        this.logBatchEvent('🔄 Métricas reseteadas', 'info');
    }

    /**
     * INICIALIZACIÓN AUTOMÁTICA
     */
    init() {
        // Cargar métricas iniciales
        this.refreshMetrics();
        
        // Log de inicio
        this.logBatchEvent('🟢 Dashboard de monitoreo inicializado', 'success');
        
        // Auto-inicio del polling si es necesario
        // this.startPolling(); // Descomentado si se quiere auto-inicio
    }
}

// Instancia global del monitoring dashboard
window.monitoringDashboard = new MonitoringDashboard();