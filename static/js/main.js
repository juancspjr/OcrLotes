/**
 * SISTEMA OCR EMPRESARIAL - MÓDULO PRINCIPAL
 * FILOSOFÍA: INTEGRIDAD TOTAL + INTERFACE EXCELLENCE
 * 
 * Este módulo coordina todos los componentes del sistema y gestiona
 * el estado global de la aplicación siguiendo el patrón de arquitectura modular.
 */

// Namespace global del sistema
window.OCRSystem = window.OCRSystem || {};

(function() {
    'use strict';
    
    // Configuración del sistema
    const CONFIG = {
        API_BASE_URL: window.location.origin,
        TOAST_DURATION: 5000,
        POLLING_INTERVAL: 2000,
        MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
        SUPPORTED_FORMATS: ['image/jpeg', 'image/jpg', 'image/png'],
        DEFAULT_PROFILE: 'ultra_rapido'
    };

    // Estado global del sistema
    let systemState = {
        initialized: false,
        currentTab: 'uploadSection',
        isProcessing: false,
        currentBatchId: null,
        apiKey: null,
        files: new Map(),
        results: new Map(),
        connectionStatus: 'checking'
    };

    // Referencias a módulos
    let modules = {
        apiClient: null,
        fileManager: null,
        resultsViewer: null,
        monitoringDashboard: null,
        apiDocs: null
    };

    /**
     * Inicialización del sistema principal
     */
    function init() {
        console.log('🚀 Inicializando Sistema OCR Empresarial...');
        
        try {
            // Verificar conectividad con backend
            checkBackendConnectivity()
                .then(() => {
                    initializeModules();
                    setupEventListeners();
                    setupTabNavigation();
                    setupNotificationSystem();
                    loadSystemState();
                    systemState.initialized = true;
                    console.log('✅ Sistema OCR Empresarial inicializado exitosamente');
                    showNotification('Sistema inicializado correctamente', 'success');
                })
                .catch(error => {
                    console.error('❌ Error inicializando sistema:', error);
                    showNotification('Error al conectar con el backend', 'error');
                });
        } catch (error) {
            console.error('❌ Error crítico en inicialización:', error);
            showNotification('Error crítico al inicializar el sistema', 'error');
        }
    }

    /**
     * Verificar conectividad con el backend
     */
    async function checkBackendConnectivity() {
        console.log('🔍 Verificando conectividad con backend...');
        
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/ocr/processed_files`);
            if (response.ok) {
                systemState.connectionStatus = 'connected';
                console.log('✅ Backend conectado exitosamente');
                return true;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            systemState.connectionStatus = 'error';
            console.error('❌ Error conectando con backend:', error);
            throw error;
        }
    }

    /**
     * Inicializar todos los módulos del sistema
     */
    function initializeModules() {
        console.log('🔧 Inicializando módulos...');
        
        // Inicializar API Client
        if (window.OCRSystem.APIClient) {
            modules.apiClient = new window.OCRSystem.APIClient(CONFIG.API_BASE_URL);
            console.log('🔧 API Client inicializado');
        }

        // Inicializar File Manager
        if (window.OCRSystem.FileManager) {
            modules.fileManager = new window.OCRSystem.FileManager({
                dropAreaId: 'dropArea',
                fileInputId: 'fileInput',
                fileListId: 'fileListTableBody',
                apiClient: modules.apiClient
            });
            console.log('🔧 File Manager inicializado');
        }

        // Inicializar Results Viewer
        if (window.OCRSystem.ResultsViewer) {
            modules.resultsViewer = new window.OCRSystem.ResultsViewer({
                resultsTableId: 'resultsTableBody',
                batchSelectorId: 'batchSelector',
                statusFilterId: 'statusFilter',
                apiClient: modules.apiClient
            });
            console.log('🔧 Results Viewer inicializado');
        }

        // Inicializar Monitoring Dashboard
        if (window.OCRSystem.MonitoringDashboard) {
            modules.monitoringDashboard = new window.OCRSystem.MonitoringDashboard({
                apiClient: modules.apiClient
            });
            console.log('🔧 Monitoring Dashboard inicializado');
        }

        // Inicializar API Docs
        if (window.OCRSystem.APIDocs) {
            modules.apiDocs = new window.OCRSystem.APIDocs({
                apiClient: modules.apiClient
            });
            console.log('🔧 API Docs inicializado');
        }
    }

    /**
     * Configurar event listeners globales
     */
    function setupEventListeners() {
        // Botón de procesar lote
        const processBatchBtn = document.getElementById('processBatchBtn');
        if (processBatchBtn) {
            processBatchBtn.addEventListener('click', handleProcessBatch);
        }

        // Botones de expandir/colapsar todos los archivos
        const expandAllBtn = document.getElementById('expandAllBtn');
        const collapseAllBtn = document.getElementById('collapseAllBtn');
        
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => {
                if (modules.fileManager) {
                    modules.fileManager.expandAll();
                }
            });
        }
        
        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', () => {
                if (modules.fileManager) {
                    modules.fileManager.collapseAll();
                }
            });
        }

        // Botón de generar parámetros de lote
        const generateBatchParamsBtn = document.getElementById('generateBatchParamsBtn');
        if (generateBatchParamsBtn) {
            generateBatchParamsBtn.addEventListener('click', () => {
                const modal = new bootstrap.Modal(document.getElementById('batchParamsModal'));
                modal.show();
            });
        }

        // Botón de aplicar parámetros de lote
        const applyBatchParamsBtn = document.getElementById('applyBatchParamsBtn');
        if (applyBatchParamsBtn) {
            applyBatchParamsBtn.addEventListener('click', handleApplyBatchParams);
        }

        // Botones de resultados
        const extractResultsBtn = document.getElementById('extractResultsBtn');
        const cleanResultsBtn = document.getElementById('cleanResultsBtn');
        
        if (extractResultsBtn) {
            extractResultsBtn.addEventListener('click', handleExtractResults);
        }
        
        if (cleanResultsBtn) {
            cleanResultsBtn.addEventListener('click', handleCleanResults);
        }

        // Escuchar cambios en filtros de resultados
        const statusFilter = document.getElementById('statusFilter');
        const batchSelector = document.getElementById('batchSelector');
        
        if (statusFilter) {
            statusFilter.addEventListener('change', handleFilterChange);
        }
        
        if (batchSelector) {
            batchSelector.addEventListener('change', handleBatchChange);
        }

        // Eventos globales
        window.addEventListener('beforeunload', saveSystemState);
        
        // Eventos de teclado
        document.addEventListener('keydown', handleKeyboardShortcuts);
    }

    /**
     * Configurar navegación entre pestañas
     */
    function setupTabNavigation() {
        const tabButtons = document.querySelectorAll('#mainTabs button[data-bs-toggle="tab"]');
        
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', (event) => {
                const targetTab = event.target.getAttribute('data-bs-target').replace('#', '');
                systemState.currentTab = targetTab;
                console.log(`📋 Cambiando a pestaña: ${targetTab.replace('Section', '')}`);
                
                // Actualizar módulos según la pestaña activa
                switch (targetTab) {
                    case 'resultsSection':
                        if (modules.resultsViewer) {
                            modules.resultsViewer.refresh();
                        }
                        break;
                    case 'monitoringSection':
                        if (modules.monitoringDashboard) {
                            modules.monitoringDashboard.refresh();
                        }
                        break;
                    case 'apiDocsSection':
                        if (modules.apiDocs) {
                            modules.apiDocs.refresh();
                        }
                        break;
                }
            });
        });
    }

    /**
     * Configurar sistema de notificaciones
     */
    function setupNotificationSystem() {
        // Verificar que el contenedor de toasts existe
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
    }

    /**
     * Manejar procesamiento de lote
     */
    async function handleProcessBatch() {
        if (systemState.isProcessing) {
            showNotification('Ya hay un procesamiento en curso', 'warning');
            return;
        }

        if (!modules.fileManager || modules.fileManager.getFileCount() === 0) {
            showNotification('No hay archivos para procesar', 'warning');
            return;
        }

        try {
            systemState.isProcessing = true;
            updateProcessButton(true);
            
            console.log('🚀 Iniciando procesamiento de lote...');
            showNotification('Iniciando procesamiento de lote...', 'info');
            
            const profile = document.getElementById('batchProfile')?.value || CONFIG.DEFAULT_PROFILE;
            const result = await modules.fileManager.processBatch(profile);
            
            if (result && result.status === 'exitoso') {
                systemState.currentBatchId = result.request_id;
                showNotification(`Lote procesado exitosamente: ${result.message}`, 'success');
                
                // Cambiar a la pestaña de resultados
                const resultsTab = document.querySelector('#results-tab');
                if (resultsTab) {
                    resultsTab.click();
                }
                
                // Actualizar resultados
                if (modules.resultsViewer) {
                    setTimeout(() => modules.resultsViewer.refresh(), 1000);
                }
            } else {
                throw new Error(result?.message || 'Error desconocido en el procesamiento');
            }
            
        } catch (error) {
            console.error('❌ Error procesando lote:', error);
            showNotification(`Error procesando lote: ${error.message}`, 'error');
        } finally {
            systemState.isProcessing = false;
            updateProcessButton(false);
        }
    }

    /**
     * Manejar aplicación de parámetros de lote
     */
    function handleApplyBatchParams() {
        const params = {
            codigo_sorteo: document.getElementById('batchCodigoSorteo')?.value || '',
            id_whatsapp: document.getElementById('batchIdWhatsapp')?.value || '',
            nombre_usuario: document.getElementById('batchNombreUsuario')?.value || '',
            caption: document.getElementById('batchCaption')?.value || '',
            hora_exacta: document.getElementById('batchHoraExacta')?.value || ''
        };

        if (modules.fileManager) {
            modules.fileManager.applyBatchParameters(params);
            showNotification('Parámetros aplicados a todos los archivos', 'success');
            
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('batchParamsModal'));
            if (modal) {
                modal.hide();
            }
        }
    }

    /**
     * Manejar extracción de resultados
     */
    async function handleExtractResults() {
        try {
            showNotification('Generando archivo de resultados...', 'info');
            
            if (modules.apiClient) {
                const results = await modules.apiClient.extractResults();
                
                // Crear y descargar archivo JSON
                const blob = new Blob([JSON.stringify(results, null, 2)], {
                    type: 'application/json'
                });
                
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `resultados_ocr_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                
                showNotification('Archivo de resultados descargado exitosamente', 'success');
            }
        } catch (error) {
            console.error('❌ Error extrayendo resultados:', error);
            showNotification(`Error extrayendo resultados: ${error.message}`, 'error');
        }
    }

    /**
     * Manejar limpieza de resultados
     */
    async function handleCleanResults() {
        if (!confirm('¿Estás seguro de que quieres limpiar todos los resultados? Esta acción no se puede deshacer.')) {
            return;
        }

        try {
            showNotification('Limpiando resultados del sistema...', 'info');
            
            if (modules.apiClient) {
                const result = await modules.apiClient.cleanResults();
                showNotification('Resultados limpiados exitosamente', 'success');
                
                // Actualizar vistas
                if (modules.resultsViewer) {
                    modules.resultsViewer.refresh();
                }
                if (modules.monitoringDashboard) {
                    modules.monitoringDashboard.refresh();
                }
            }
        } catch (error) {
            console.error('❌ Error limpiando resultados:', error);
            showNotification(`Error limpiando resultados: ${error.message}`, 'error');
        }
    }

    /**
     * Manejar cambios en filtros
     */
    function handleFilterChange() {
        if (modules.resultsViewer) {
            modules.resultsViewer.applyFilters();
        }
    }

    /**
     * Manejar cambio de lote
     */
    function handleBatchChange() {
        if (modules.resultsViewer) {
            modules.resultsViewer.loadBatch();
        }
    }

    /**
     * Manejar atajos de teclado
     */
    function handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + U - Ir a pestaña de subida
        if ((event.ctrlKey || event.metaKey) && event.key === 'u') {
            event.preventDefault();
            document.querySelector('#upload-tab')?.click();
        }
        
        // Ctrl/Cmd + R - Ir a pestaña de resultados
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            document.querySelector('#results-tab')?.click();
        }
        
        // Ctrl/Cmd + M - Ir a pestaña de monitoreo
        if ((event.ctrlKey || event.metaKey) && event.key === 'm') {
            event.preventDefault();
            document.querySelector('#monitoring-tab')?.click();
        }
        
        // Escape - Cerrar modales
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    }

    /**
     * Actualizar estado del botón de procesar
     */
    function updateProcessButton(isProcessing) {
        const button = document.getElementById('processBatchBtn');
        if (button) {
            if (isProcessing) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
                button.classList.add('loading');
            } else {
                button.disabled = modules.fileManager ? modules.fileManager.getFileCount() === 0 : true;
                button.innerHTML = '<i class="fas fa-play me-2"></i>Procesar Lote';
                button.classList.remove('loading');
            }
        }
    }

    /**
     * Actualizar contadores en la interfaz
     */
    function updateCounters() {
        const fileCount = modules.fileManager ? modules.fileManager.getFileCount() : 0;
        
        // Actualizar contador de archivos
        const filesInQueueCount = document.getElementById('filesInQueueCount');
        if (filesInQueueCount) {
            filesInQueueCount.textContent = fileCount;
        }
        
        const fileCountStatus = document.getElementById('fileCountStatus');
        if (fileCountStatus) {
            fileCountStatus.textContent = `${fileCount} archivo${fileCount !== 1 ? 's' : ''} listo${fileCount !== 1 ? 's' : ''} para procesar`;
        }
        
        // Actualizar estado del lote
        const batchStatus = document.getElementById('batchStatus');
        if (batchStatus) {
            if (fileCount === 0) {
                batchStatus.textContent = 'Listo para cargar';
            } else if (systemState.isProcessing) {
                batchStatus.textContent = 'Procesando...';
            } else {
                batchStatus.textContent = 'Listo para procesar';
            }
        }
        
        // Actualizar botón de procesar
        updateProcessButton(systemState.isProcessing);
    }

    /**
     * Mostrar notificación toast
     */
    function showNotification(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toastId = 'toast_' + Date.now();
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };

        const colorMap = {
            success: 'text-bg-success',
            error: 'text-bg-danger',
            warning: 'text-bg-warning',
            info: 'text-bg-info'
        };

        const toastHTML = `
            <div id="${toastId}" class="toast ${colorMap[type]}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas ${iconMap[type]} me-2"></i>
                    <strong class="me-auto">Sistema OCR</strong>
                    <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);

        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });

        toast.show();

        // Limpiar el DOM después de ocultar
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    /**
     * Cargar estado del sistema desde localStorage
     */
    function loadSystemState() {
        try {
            const savedState = localStorage.getItem('ocrSystemState');
            if (savedState) {
                const parsed = JSON.parse(savedState);
                systemState = { ...systemState, ...parsed };
                
                // Aplicar estado guardado
                if (systemState.currentBatchId) {
                    const currentBatchId = document.getElementById('currentBatchId');
                    if (currentBatchId) {
                        currentBatchId.textContent = systemState.currentBatchId;
                    }
                }
            }
        } catch (error) {
            console.warn('⚠️ Error cargando estado del sistema:', error);
        }
    }

    /**
     * Guardar estado del sistema en localStorage
     */
    function saveSystemState() {
        try {
            const stateToSave = {
                currentBatchId: systemState.currentBatchId,
                currentTab: systemState.currentTab
            };
            localStorage.setItem('ocrSystemState', JSON.stringify(stateToSave));
        } catch (error) {
            console.warn('⚠️ Error guardando estado del sistema:', error);
        }
    }

    // API pública del sistema principal
    window.OCRSystem.Main = {
        init: init,
        getState: () => ({ ...systemState }),
        getModules: () => ({ ...modules }),
        showNotification: showNotification,
        updateCounters: updateCounters,
        CONFIG: CONFIG
    };

    // Alias para inicialización
    window.OCRSystem.init = init;

    console.log('🎯 Interface Excellence Dashboard inicializado - MANDATO 14');

})();