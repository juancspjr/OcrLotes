/**
 * Optimized JavaScript for OCR System - Performance focused
 * Reduces bundle size and improves load times
 */

// Global variables - optimized declarations
const OCRSystem = {
    elements: {},
    cache: new Map(),
    
    // Initialize system
    init() {
        this.initializeElements();
        this.setupEventListeners();
        this.setupTooltips();
    },
    
    // Cache DOM elements for better performance
    initializeElements() {
        this.elements = {
            uploadForm: document.getElementById('uploadForm'),
            fileInput: document.getElementById('file'),
            imagePreview: document.getElementById('imagePreview'),
            submitBtn: document.getElementById('submitBtn'),
            btnText: document.getElementById('btnText'),
            btnSpinner: document.getElementById('btnSpinner')
        };
    },
    
    // Optimized event listener setup
    setupEventListeners() {
        const { fileInput, uploadForm } = this.elements;
        
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
            this.setupDragDrop();
        }
        
        if (uploadForm) {
            uploadForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        }
        
        // Optimize scroll behavior
        this.setupSmoothScroll();
        this.setupAutoHideAlerts();
    },
    
    // File selection handler - optimized
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return this.hideImagePreview();
        
        // Validate file type and size
        if (!this.validateFile(file)) return;
        
        // Show preview and analyze
        this.showImagePreview(file);
        this.analyzeAndSuggestProfile(file);
    },
    
    // Optimized file validation
    validateFile(file) {
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp'];
        const maxSize = 16 * 1024 * 1024; // 16MB
        
        if (!allowedTypes.includes(file.type)) {
            this.showAlert('Tipo de archivo no válido. Use PNG, JPG, JPEG, GIF, BMP, TIFF o WEBP.', 'error');
            this.resetFileInput();
            return false;
        }
        
        if (file.size > maxSize) {
            this.showAlert('El archivo es demasiado grande. Máximo 16MB permitido.', 'error');
            this.resetFileInput();
            return false;
        }
        
        return true;
    },
    
    // Optimized image preview
    showImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const info = this.getFileInfo(file);
            const preview = this.elements.imagePreview;
            
            preview.innerHTML = this.generatePreviewHTML(e.target.result, info);
            preview.classList.add('active');
            preview.style.display = 'block';
            
            // Calculate dimensions asynchronously
            this.calculateImageDimensions(e.target.result);
        };
        reader.readAsDataURL(file);
    },
    
    // Generate preview HTML template
    generatePreviewHTML(src, info) {
        return `
            <div class="row align-items-center">
                <div class="col-md-6 text-center">
                    <img src="${src}" alt="Preview" class="img-fluid rounded shadow" style="max-height: 200px;">
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-info-circle me-2"></i>Información del Archivo:</h6>
                    <ul class="list-unstyled small">
                        <li><strong>Nombre:</strong> ${info.name}</li>
                        <li><strong>Tamaño:</strong> ${info.size}</li>
                        <li><strong>Tipo:</strong> ${info.type}</li>
                        <li><strong>Dimensiones:</strong> <span id="imageDimensions">Calculando...</span></li>
                    </ul>
                    <div id="profileSuggestion" class="mt-2"></div>
                </div>
            </div>
        `;
    },
    
    // Optimized file info extraction
    getFileInfo(file) {
        return {
            name: file.name,
            size: this.formatFileSize(file.size),
            type: file.type
        };
    },
    
    // Efficient file size formatting
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Form submission handler
    handleFormSubmit(event) {
        if (!this.elements.fileInput.files?.length) {
            event.preventDefault();
            this.showAlert('Por favor seleccione un archivo antes de continuar.', 'error');
            return false;
        }
        
        this.showLoadingState();
        return true;
    },
    
    // Optimized loading state
    showLoadingState() {
        const { submitBtn, btnText, btnSpinner } = this.elements;
        if (submitBtn && btnText && btnSpinner) {
            submitBtn.disabled = true;
            btnText.textContent = 'Procesando...';
            btnSpinner.classList.remove('d-none');
            this.showLoadingOverlay();
        }
    },
    
    // Performance optimized alert system
    showAlert(message, type = 'info', duration = 5000) {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        alertEl.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        const iconMap = { error: 'exclamation-triangle', success: 'check-circle', info: 'info-circle' };
        alertEl.innerHTML = `
            <i class="fas fa-${iconMap[type] || 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertEl);
        setTimeout(() => alertEl.remove(), duration);
    },
    
    // Utility functions
    hideImagePreview() {
        const preview = this.elements.imagePreview;
        if (preview) {
            preview.innerHTML = '';
            preview.classList.remove('active');
            preview.style.display = 'none';
        }
    },
    
    resetFileInput() {
        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
            this.hideImagePreview();
        }
    },
    
    // Performance optimizations
    setupSmoothScroll() {
        // Use event delegation for better performance
        document.addEventListener('click', (e) => {
            const anchor = e.target.closest('a[href^="#"]');
            if (anchor) {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    },
    
    setupAutoHideAlerts() {
        // Auto-hide alerts with timeout
        setTimeout(() => {
            document.querySelectorAll('.alert-dismissible .btn-close')
                .forEach(btn => btn.click());
        }, 10000);
    },
    
    setupTooltips() {
        // Initialize tooltips efficiently
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));
    },
    
    // Additional optimized methods...
    calculateImageDimensions(src) {
        const img = new Image();
        img.onload = () => {
            const dimEl = document.getElementById('imageDimensions');
            if (dimEl) dimEl.textContent = `${img.width} x ${img.height} píxeles`;
        };
        img.src = src;
    },
    
    analyzeAndSuggestProfile(file) {
        const size = file.size;
        let profile = 'rapido', suggestion = '', badgeClass = 'bg-success';
        
        if (size < 500 * 1024) {
            profile = 'ultra_rapido';
            suggestion = 'Imagen pequeña - Perfil Ultra Rápido recomendado';
            badgeClass = 'bg-primary';
        } else if (size > 2 * 1024 * 1024) {
            profile = 'normal';
            suggestion = 'Imagen grande - Perfil Normal recomendado para mejor calidad';
            badgeClass = 'bg-warning';
        } else {
            suggestion = 'Tamaño óptimo - Perfil Rápido recomendado';
        }
        
        const suggestionEl = document.getElementById('profileSuggestion');
        if (suggestionEl) {
            suggestionEl.innerHTML = `
                <div class="alert alert-info py-2 mb-0">
                    <i class="fas fa-lightbulb me-2"></i>
                    <span class="badge ${badgeClass} me-2">${profile}</span>
                    ${suggestion}
                </div>
            `;
        }
        
        // Update profile select
        const profileSelect = document.getElementById('profile');
        if (profileSelect) {
            profileSelect.value = profile;
            this.highlightElement(profileSelect);
        }
    },
    
    highlightElement(element) {
        element.classList.add('border-warning');
        setTimeout(() => element.classList.remove('border-warning'), 2000);
    },
    
    setupDragDrop() {
        const dropZone = this.elements.fileInput?.closest('.card-body');
        if (!dropZone) return;
        
        const preventDefaults = (e) => {
            e.preventDefault();
            e.stopPropagation();
        };
        
        const highlight = () => dropZone.classList.add('border-primary', 'bg-light');
        const unhighlight = () => dropZone.classList.remove('border-primary', 'bg-light');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.elements.fileInput.files = files;
                this.elements.fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }, false);
    },
    
    showLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <div class="mt-3">
                    <h5 class="text-light">Procesando documento...</h5>
                    <p class="text-light">Esto puede tomar unos momentos dependiendo del tamaño y complejidad de la imagen.</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        setTimeout(() => overlay.remove(), 30000); // Auto-remove fallback
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    OCRSystem.init();
    
    // Initialize results page if applicable
    if (window.location.pathname.includes('results')) {
        OCRSystem.setupResultsPage();
    }
});

// Results page specific optimizations
OCRSystem.setupResultsPage = function() {
    // Collapsible sections
    document.querySelectorAll('.card-header').forEach(header => {
        if (header.dataset.collapsible !== 'false') {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                if (content) content.classList.toggle('show');
            });
        }
    });
    
    // Image modal functionality
    document.querySelectorAll('.image-container img').forEach(img => {
        img.addEventListener('click', function() {
            OCRSystem.showImageModal(this.src, this.alt);
        });
    });
    
    // Copy to clipboard
    document.querySelectorAll('.copy-text-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = document.querySelector(this.getAttribute('data-target'));
            if (target && navigator.clipboard) {
                navigator.clipboard.writeText(target.textContent)
                    .then(() => OCRSystem.showAlert('Texto copiado al portapapeles', 'success'))
                    .catch(() => OCRSystem.showAlert('Error al copiar texto', 'error'));
            }
        });
    });
};

OCRSystem.showImageModal = function(src, alt) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${alt || 'Imagen'}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${src}" class="img-fluid" alt="${alt || 'Imagen'}">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
};