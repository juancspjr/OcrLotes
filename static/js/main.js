/**
 * MAIN.JS - SISTEMA OCR EMPRESARIAL
 * Coordinador principal del frontend con filosofía Interface Excellence Soberana
 * FILOSOFÍA: INTEGRIDAD TOTAL + OPTIMIZACIÓN SOSTENIBLE + TRANSPARENCIA TOTAL
 */

class OCRDashboard {
    constructor() {
        this.isInitialized = false;
        this.currentPage = 'dashboard';
        this.notificationContainer = null;
        this.activeNotifications = new Map();
        
        // Estado global de la aplicación
        this.appState = {
            isLoading: false,
            systemStatus: 'unknown',
            queueStats: {},
            lastUpdate: null
        };

        this.initializeApp();
    }

    /**
     * INICIALIZACIÓN PRINCIPAL DE LA APLICACIÓN
     */
    async initializeApp() {
        try {
            console.log('🚀 Inicializando Sistema OCR Empresarial...');
            
            // Verificar dependencias críticas
            this.checkDependencies();
            
            // Configurar elementos DOM base
            this.setupDOMElements();
            
            // Configurar sistema de notificaciones
            this.setupNotificationSystem();
            
            // Configurar eventos globales
            this.setupGlobalEvents();
            
            // Verificar conectividad con backend
            await this.checkBackendConnectivity();
            
            // Inicializar módulos según elementos disponibles
            this.initializeModules();
            
            // Configurar auto-actualización
            this.setupAutoRefresh();
            
            // Marcar como inicializado
            this.isInitialized = true;
            
            console.log('✅ Sistema OCR Empresarial inicializado exitosamente');
            this.showNotification('✅ Sistema OCR inicializado correctamente', 'success', 3000);
            
        } catch (error) {
            console.error('❌ Error inicializando aplicación:', error);
            this.showNotification(`❌ Error de inicialización: ${error.message}`, 'error', 10000);
        }
    }

    /**
     * VERIFICAR DEPENDENCIAS CRÍTICAS
     */
    checkDependencies() {
        const requiredLibraries = ['bootstrap', 'Chart'];
        const missingLibraries = [];

        requiredLibraries.forEach(lib => {
            if (typeof window[lib] === 'undefined') {
                missingLibraries.push(lib);
            }
        });

        if (missingLibraries.length > 0) {
            console.warn('⚠️ Librerías faltantes:', missingLibraries);
        }

        // Verificar módulos propios
        const requiredModules = ['apiClient', 'fileManager', 'resultsViewer', 'monitoringDashboard'];
        const missingModules = requiredModules.filter(module => !window[module]);
        
        if (missingModules.length > 0) {
            console.warn('⚠️ Módulos faltantes:', missingModules);
        }
    }

    /**
     * CONFIGURAR ELEMENTOS DOM BASE
     */
    setupDOMElements() {
        // Agregar elementos de infraestructura si no existen
        this.ensureNotificationContainer();
        this.ensureLoadingOverlay();
        this.setupNavigationTabs();
    }

    ensureNotificationContainer() {
        this.notificationContainer = document.getElementById('notificationContainer');
        if (!this.notificationContainer) {
            this.notificationContainer = document.createElement('div');
            this.notificationContainer.id = 'notificationContainer';
            this.notificationContainer.className = 'notification-container position-fixed top-0 end-0 p-3';
            this.notificationContainer.style.zIndex = '9999';
            document.body.appendChild(this.notificationContainer);
        }
    }

    ensureLoadingOverlay() {
        let loadingOverlay = document.getElementById('loadingOverlay');
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'loadingOverlay';
            loadingOverlay.className = 'loading-overlay position-fixed top-0 start-0 w-100 h-100 d-none';
            loadingOverlay.style.zIndex = '9998';
            loadingOverlay.innerHTML = `
                <div class="d-flex align-items-center justify-content-center h-100 bg-dark bg-opacity-50">
                    <div class="card text-center p-4">
                        <div class="card-body">
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Cargando...</span>
                            </div>
                            <h5>Procesando...</h5>
                            <p class="text-muted mb-0">Por favor espere</p>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        }
    }

    setupNavigationTabs() {
        // Configurar navegación entre pestañas si existen
        const navTabs = document.querySelectorAll('[data-tab-target]');
        navTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.getAttribute('data-tab-target');
                this.switchTab(target);
            });
        });
    }

    /**
     * CONFIGURAR SISTEMA DE NOTIFICACIONES
     */
    setupNotificationSystem() {
        // Escuchar eventos de notificación globales
        window.addEventListener('showNotification', (e) => {
            const { message, type, duration } = e.detail;
            this.showNotification(message, type, duration);
        });

        // Auto-cleanup de notificaciones viejas
        setInterval(() => {
            this.cleanupOldNotifications();
        }, 30000); // cada 30 segundos
    }

    /**
     * CONFIGURAR EVENTOS GLOBALES
     */
    setupGlobalEvents() {
        // Error handler global para requests fallidos
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Promise rejection no manejada:', e.reason);
            this.showNotification('❌ Error inesperado del sistema', 'error');
        });

        // Handler para errores JavaScript
        window.addEventListener('error', (e) => {
            console.error('Error JavaScript:', e.error);
            // No mostrar notificación para todos los errores JS para evitar spam
        });

        // Manejar eventos de conectividad
        window.addEventListener('online', () => {
            this.showNotification('🌐 Conexión restaurada', 'success', 3000);
        });

        window.addEventListener('offline', () => {
            this.showNotification('⚠️ Sin conexión a internet', 'warning');
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    /**
     * VERIFICAR CONECTIVIDAD CON BACKEND
     */
    async checkBackendConnectivity() {
        try {
            console.log('🔍 Verificando conectividad con backend...');
            
            const data = await window.apiClient.getQueueStatus();
            
            if (data && data.status === 'ok') {
                this.appState.systemStatus = 'connected';
                this.appState.queueStats = data.queue_status || {};
                this.updateSystemStatusIndicator('connected');
                console.log('✅ Backend conectado exitosamente');
            } else {
                throw new Error('Respuesta inválida del backend');
            }
            
        } catch (error) {
            console.error('❌ Error conectando con backend:', error);
            this.appState.systemStatus = 'disconnected';
            this.updateSystemStatusIndicator('disconnected');
            this.showNotification('⚠️ No se pudo conectar con el servidor', 'warning');
        }
    }

    /**
     * INICIALIZAR MÓDULOS SEGÚN DISPONIBILIDAD
     */
    initializeModules() {
        // Inicializar File Manager si hay elementos de upload
        if (window.fileManager && document.getElementById('dropZone')) {
            console.log('🔧 Inicializando File Manager...');
            // File Manager se auto-inicializa
        }

        // Inicializar Results Viewer si hay contenedor de resultados
        if (window.resultsViewer && document.getElementById('resultsContainer')) {
            console.log('🔧 Inicializando Results Viewer...');
            window.resultsViewer.loadResults(false);
        }

        // Inicializar Monitoring Dashboard si hay contenedor de métricas
        if (window.monitoringDashboard && document.getElementById('chartsContainer')) {
            console.log('🔧 Inicializando Monitoring Dashboard...');
            window.monitoringDashboard.init();
        }

        // Configurar botones globales
        this.setupGlobalButtons();
    }

    /**
     * CONFIGURAR BOTONES GLOBALES
     */
    setupGlobalButtons() {
        // Botón de upload automático
        const autoUploadBtn = document.getElementById('autoUploadBtn');
        if (autoUploadBtn) {
            autoUploadBtn.addEventListener('click', () => this.handleAutoUpload());
        }

        // Botón de limpieza rápida
        const quickCleanBtn = document.getElementById('quickCleanBtn');
        if (quickCleanBtn) {
            quickCleanBtn.addEventListener('click', () => this.handleQuickClean());
        }

        // Botón de refresh global
        const globalRefreshBtn = document.getElementById('globalRefreshBtn');
        if (globalRefreshBtn) {
            globalRefreshBtn.addEventListener('click', () => this.handleGlobalRefresh());
        }

        // Botón de export completo
        const exportAllBtn = document.getElementById('exportAllBtn');
        if (exportAllBtn) {
            exportAllBtn.addEventListener('click', () => this.handleExportAll());
        }
    }

    /**
     * CONFIGURAR AUTO-ACTUALIZACIÓN
     */
    setupAutoRefresh() {
        // Auto-refresh del estado del sistema cada 30 segundos
        setInterval(() => {
            if (this.appState.systemStatus === 'connected') {
                this.refreshSystemStatus();
            }
        }, 30000);
    }

    /**
     * ACTUALIZAR ESTADO DEL SISTEMA
     */
    async refreshSystemStatus() {
        try {
            const data = await window.apiClient.getQueueStatus();
            this.appState.queueStats = data.queue_status || {};
            this.appState.lastUpdate = new Date();
            
            // Actualizar indicadores en UI
            this.updateQueueIndicators(this.appState.queueStats);
            
        } catch (error) {
            console.warn('⚠️ Error actualizando estado del sistema:', error);
            this.appState.systemStatus = 'disconnected';
            this.updateSystemStatusIndicator('disconnected');
        }
    }

    /**
     * ACTUALIZAR INDICADORES DE COLA
     */
    updateQueueIndicators(queueStats) {
        // Actualizar badge de archivos pendientes
        const pendingBadge = document.getElementById('pendingFilesBadge');
        if (pendingBadge) {
            const pendingCount = (queueStats.inbox || 0) + (queueStats.processing || 0);
            pendingBadge.textContent = pendingCount;
            pendingBadge.className = pendingCount > 0 ? 'badge bg-warning' : 'badge bg-secondary';
        }

        // Actualizar badge de archivos completados
        const completedBadge = document.getElementById('completedFilesBadge');
        if (completedBadge) {
            const completedCount = queueStats.completed || 0;
            completedBadge.textContent = completedCount;
            completedBadge.className = 'badge bg-success';
        }

        // Disparar evento para otros módulos
        window.dispatchEvent(new CustomEvent('queueStatusUpdate', {
            detail: queueStats
        }));
    }

    /**
     * ACTUALIZAR INDICADOR DE ESTADO DEL SISTEMA
     */
    updateSystemStatusIndicator(status) {
        const statusIndicator = document.getElementById('systemStatus');
        if (statusIndicator) {
            switch (status) {
                case 'connected':
                    statusIndicator.innerHTML = '<i class="fas fa-circle text-success me-1"></i>Conectado';
                    statusIndicator.className = 'badge bg-success';
                    break;
                case 'disconnected':
                    statusIndicator.innerHTML = '<i class="fas fa-circle text-danger me-1"></i>Desconectado';
                    statusIndicator.className = 'badge bg-danger';
                    break;
                default:
                    statusIndicator.innerHTML = '<i class="fas fa-circle text-warning me-1"></i>Verificando...';
                    statusIndicator.className = 'badge bg-warning';
            }
        }
    }

    /**
     * SISTEMA DE NOTIFICACIONES
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notificationId = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const notification = document.createElement('div');
        notification.id = notificationId;
        notification.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show notification-item`;
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        this.notificationContainer.appendChild(notification);
        this.activeNotifications.set(notificationId, {
            element: notification,
            createdAt: Date.now(),
            duration: duration
        });

        // Auto-remove si tiene duración definida
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notificationId);
            }, duration);
        }

        // Configurar evento de close manual
        notification.addEventListener('closed.bs.alert', () => {
            this.activeNotifications.delete(notificationId);
        });
    }

    removeNotification(notificationId) {
        const notification = this.activeNotifications.get(notificationId);
        if (notification && notification.element) {
            notification.element.remove();
            this.activeNotifications.delete(notificationId);
        }
    }

    cleanupOldNotifications() {
        const now = Date.now();
        for (const [id, notification] of this.activeNotifications.entries()) {
            // Remover notificaciones que han estado por más de 2 minutos
            if (now - notification.createdAt > 120000) {
                this.removeNotification(id);
            }
        }
    }

    getBootstrapAlertClass(type) {
        const mapping = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info'
        };
        return mapping[type] || 'info';
    }

    /**
     * MANEJO DE PESTAÑAS
     */
    switchTab(tabName) {
        // Ocultar todas las pestañas
        const tabContents = document.querySelectorAll('.tab-content-panel');
        tabContents.forEach(content => {
            content.classList.add('d-none');
        });

        // Mostrar pestaña objetivo
        const targetTab = document.getElementById(`${tabName}Tab`);
        if (targetTab) {
            targetTab.classList.remove('d-none');
            this.currentPage = tabName;
        }

        // Actualizar navegación activa
        const navItems = document.querySelectorAll('[data-tab-target]');
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-tab-target') === tabName) {
                item.classList.add('active');
            }
        });

        console.log(`📋 Cambiando a pestaña: ${tabName}`);
    }

    /**
     * HANDLERS DE ACCIONES GLOBALES
     */
    async handleAutoUpload() {
        if (!window.fileManager) {
            this.showNotification('⚠️ File Manager no disponible', 'warning');
            return;
        }

        try {
            this.setGlobalLoading(true);
            
            // Upload automático con metadatos por defecto
            const defaultMetadata = {
                numerosorteo: 'AUTO',
                fechasorteo: new Date().toISOString().split('T')[0].replace(/-/g, ''),
                nombre: 'Sistema',
                otro_valor: 'auto_upload'
            };

            const uploadResult = await window.fileManager.uploadFiles([], defaultMetadata);
            
            if (uploadResult) {
                // Auto-procesar después del upload
                await window.fileManager.processBatch();
            }

        } catch (error) {
            this.showNotification(`❌ Error en upload automático: ${error.getUserMessage()}`, 'error');
        } finally {
            this.setGlobalLoading(false);
        }
    }

    async handleQuickClean() {
        try {
            const confirmed = confirm('¿Limpiar solo la cola de archivos pendientes?');
            if (!confirmed) return;

            this.setGlobalLoading(true);
            await window.apiClient.cleanQueue();
            
            // Refresh de todos los módulos
            this.handleGlobalRefresh();
            
            this.showNotification('🧹 Cola limpiada exitosamente', 'success');

        } catch (error) {
            this.showNotification(`❌ Error limpiando cola: ${error.getUserMessage()}`, 'error');
        } finally {
            this.setGlobalLoading(false);
        }
    }

    async handleGlobalRefresh() {
        try {
            this.setGlobalLoading(true);
            
            // Refresh de estado del sistema
            await this.refreshSystemStatus();
            
            // Refresh de resultados si el viewer está disponible
            if (window.resultsViewer && typeof window.resultsViewer.loadResults === 'function') {
                await window.resultsViewer.loadResults(false);
            }

            // Refresh de métricas si el dashboard está disponible
            if (window.monitoringDashboard && typeof window.monitoringDashboard.refreshMetrics === 'function') {
                await window.monitoringDashboard.refreshMetrics();
            }

            this.showNotification('🔄 Datos actualizados', 'success', 3000);

        } catch (error) {
            this.showNotification(`❌ Error actualizando datos: ${error.message}`, 'error');
        } finally {
            this.setGlobalLoading(false);
        }
    }

    async handleExportAll() {
        try {
            this.setGlobalLoading(true);
            
            // Exportar resultados
            if (window.resultsViewer && typeof window.resultsViewer.extractResults === 'function') {
                await window.resultsViewer.extractResults();
            }

            // Exportar métricas si están disponibles
            if (window.monitoringDashboard && typeof window.monitoringDashboard.exportMetrics === 'function') {
                window.monitoringDashboard.exportMetrics();
            }

        } catch (error) {
            this.showNotification(`❌ Error exportando datos: ${error.getUserMessage()}`, 'error');
        } finally {
            this.setGlobalLoading(false);
        }
    }

    /**
     * KEYBOARD SHORTCUTS
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + R: Refresh global
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.handleGlobalRefresh();
        }

        // Ctrl/Cmd + U: Upload automático
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            this.handleAutoUpload();
        }

        // Ctrl/Cmd + E: Export all
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            this.handleExportAll();
        }

        // Escape: Cerrar modales/notificaciones
        if (e.key === 'Escape') {
            this.closeActiveModals();
        }
    }

    closeActiveModals() {
        // Cerrar modales de Bootstrap
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }

    /**
     * UTILIDADES DE UI
     */
    setGlobalLoading(loading) {
        this.appState.isLoading = loading;
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            if (loading) {
                loadingOverlay.classList.remove('d-none');
            } else {
                loadingOverlay.classList.add('d-none');
            }
        }
    }

    /**
     * OBTENER ESTADO DE LA APLICACIÓN
     */
    getAppState() {
        return {
            ...this.appState,
            modules: {
                fileManager: !!window.fileManager,
                resultsViewer: !!window.resultsViewer,
                monitoringDashboard: !!window.monitoringDashboard,
                apiClient: !!window.apiClient
            },
            dom: {
                notificationContainer: !!this.notificationContainer,
                activeNotifications: this.activeNotifications.size
            }
        };
    }

    /**
     * DEBUG Y UTILIDADES
     */
    debug() {
        console.log('🔍 Estado de la aplicación:', this.getAppState());
        console.log('🔍 Notificaciones activas:', Array.from(this.activeNotifications.keys()));
        console.log('🔍 Módulos disponibles:', {
            fileManager: window.fileManager,
            resultsViewer: window.resultsViewer,
            monitoringDashboard: window.monitoringDashboard,
            apiClient: window.apiClient
        });
    }
}

// INICIALIZACIÓN AUTOMÁTICA AL CARGAR LA PÁGINA
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 Iniciando Sistema OCR Empresarial - MANDATO 14');
    window.ocrDashboard = new OCRDashboard();
});

// EXPOSICIÓN GLOBAL PARA DEBUGGING
window.debugOCR = () => {
    if (window.ocrDashboard) {
        window.ocrDashboard.debug();
    } else {
        console.log('❌ Dashboard no inicializado');
    }
};