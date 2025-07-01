/**
 * JavaScript principal para el Sistema OCR
 * Maneja la interactividad del frontend y mejoras de UX
 */

// Variables globales
let uploadForm = null;
let fileInput = null;
let imagePreview = null;
let submitBtn = null;
let btnText = null;
let btnSpinner = null;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
    setupEventListeners();
    setupFormValidation();
    
    // Inicializar tooltips de Bootstrap si existen
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

/**
 * Inicializa los componentes principales
 */
function initializeComponents() {
    uploadForm = document.getElementById('uploadForm');
    fileInput = document.getElementById('file');
    imagePreview = document.getElementById('imagePreview');
    submitBtn = document.getElementById('submitBtn');
    btnText = document.getElementById('btnText');
    btnSpinner = document.getElementById('btnSpinner');
    
    console.log('Componentes inicializados correctamente');
}

/**
 * Configura los event listeners
 */
function setupEventListeners() {
    // Preview de imagen al seleccionar archivo
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Manejo del formulario de upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Drag and drop para el input de archivo
    if (fileInput) {
        setupDragAndDrop();
    }
    
    // Event listeners para mejoras de UX
    setupUXEnhancements();
}

/**
 * Maneja la selección de archivo y muestra preview
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (file) {
        // Validar tipo de archivo
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp'];
        
        if (!allowedTypes.includes(file.type)) {
            showAlert('Tipo de archivo no válido. Use PNG, JPG, JPEG, GIF, BMP, TIFF o WEBP.', 'error');
            fileInput.value = '';
            hideImagePreview();
            return;
        }
        
        // Validar tamaño de archivo (16MB máximo)
        const maxSize = 16 * 1024 * 1024; // 16MB en bytes
        if (file.size > maxSize) {
            showAlert('El archivo es demasiado grande. Máximo 16MB permitido.', 'error');
            fileInput.value = '';
            hideImagePreview();
            return;
        }
        
        // Mostrar preview de la imagen
        showImagePreview(file);
        
        // Analizar imagen y sugerir perfil
        analyzeImageAndSuggestProfile(file);
    } else {
        hideImagePreview();
    }
}

/**
 * Muestra el preview de la imagen seleccionada
 */
function showImagePreview(file) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const imageInfo = getImageInfo(file);
        
        imagePreview.innerHTML = `
            <div class="row align-items-center">
                <div class="col-md-6 text-center">
                    <img src="${e.target.result}" alt="Preview" class="img-fluid rounded shadow" style="max-height: 200px;">
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-info-circle me-2"></i>Información del Archivo:</h6>
                    <ul class="list-unstyled small">
                        <li><strong>Nombre:</strong> ${imageInfo.name}</li>
                        <li><strong>Tamaño:</strong> ${imageInfo.size}</li>
                        <li><strong>Tipo:</strong> ${imageInfo.type}</li>
                        <li><strong>Dimensiones:</strong> <span id="imageDimensions">Calculando...</span></li>
                    </ul>
                    <div id="profileSuggestion" class="mt-2"></div>
                </div>
            </div>
        `;
        
        imagePreview.classList.add('active');
        imagePreview.style.display = 'block';
        
        // Calcular dimensiones de la imagen
        const img = new Image();
        img.onload = function() {
            document.getElementById('imageDimensions').textContent = `${img.width} x ${img.height} píxeles`;
        };
        img.src = e.target.result;
    };
    
    reader.readAsDataURL(file);
}

/**
 * Oculta el preview de imagen
 */
function hideImagePreview() {
    if (imagePreview) {
        imagePreview.innerHTML = '';
        imagePreview.classList.remove('active');
        imagePreview.style.display = 'none';
    }
}

/**
 * Obtiene información básica del archivo
 */
function getImageInfo(file) {
    return {
        name: file.name,
        size: formatFileSize(file.size),
        type: file.type
    };
}

/**
 * Formatea el tamaño del archivo
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Analiza la imagen y sugiere un perfil de rendimiento
 */
function analyzeImageAndSuggestProfile(file) {
    // Análisis básico basado en tamaño de archivo
    const fileSize = file.size;
    const suggestionElement = document.getElementById('profileSuggestion');
    
    if (!suggestionElement) return;
    
    let suggestedProfile = 'rapido';
    let suggestion = '';
    let badgeClass = 'bg-success';
    
    if (fileSize < 500 * 1024) { // Menos de 500KB
        suggestedProfile = 'ultra_rapido';
        suggestion = 'Imagen pequeña - Perfil Ultra Rápido recomendado';
        badgeClass = 'bg-primary';
    } else if (fileSize > 2 * 1024 * 1024) { // Más de 2MB
        suggestedProfile = 'normal';
        suggestion = 'Imagen grande - Perfil Normal recomendado para mejor calidad';
        badgeClass = 'bg-warning';
    } else {
        suggestion = 'Tamaño óptimo - Perfil Rápido recomendado';
    }
    
    suggestionElement.innerHTML = `
        <div class="alert alert-info py-2 mb-0">
            <i class="fas fa-lightbulb me-2"></i>
            <span class="badge ${badgeClass} me-2">${suggestedProfile}</span>
            ${suggestion}
        </div>
    `;
    
    // Actualizar el select del perfil
    const profileSelect = document.getElementById('profile');
    if (profileSelect) {
        profileSelect.value = suggestedProfile;
        highlightProfileSelect(profileSelect);
    }
}

/**
 * Resalta temporalmente el select de perfil
 */
function highlightProfileSelect(selectElement) {
    selectElement.classList.add('border-warning');
    setTimeout(() => {
        selectElement.classList.remove('border-warning');
    }, 2000);
}

/**
 * Maneja el envío del formulario
 */
function handleFormSubmit(event) {
    // Validar que se haya seleccionado un archivo
    if (!fileInput.files || fileInput.files.length === 0) {
        event.preventDefault();
        showAlert('Por favor seleccione un archivo antes de continuar.', 'error');
        return false;
    }
    
    // Mostrar estado de carga
    showLoadingState();
    
    // El formulario se enviará normalmente
    return true;
}

/**
 * Muestra el estado de carga
 */
function showLoadingState() {
    if (submitBtn && btnText && btnSpinner) {
        submitBtn.disabled = true;
        btnText.textContent = 'Procesando...';
        btnSpinner.classList.remove('d-none');
        
        // Mostrar overlay de carga
        showLoadingOverlay();
    }
}

/**
 * Muestra un overlay de carga
 */
function showLoadingOverlay() {
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
    
    // Remover overlay después de 30 segundos como máximo (fallback)
    setTimeout(() => {
        if (document.body.contains(overlay)) {
            document.body.removeChild(overlay);
        }
    }, 30000);
}

/**
 * Configura drag and drop para el input de archivo
 */
function setupDragAndDrop() {
    const dropZone = fileInput.closest('.card-body');
    
    if (!dropZone) return;
    
    // Prevenir comportamiento por defecto
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Resaltar zona de drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    // Manejar drop
    dropZone.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropZone.classList.add('border-primary', 'bg-light');
    }
    
    function unhighlight() {
        dropZone.classList.remove('border-primary', 'bg-light');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            
            // Disparar evento change manualmente
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
}

/**
 * Configura validación de formulario en tiempo real
 */
function setupFormValidation() {
    const form = uploadForm;
    if (!form) return;
    
    // Validación en tiempo real para todos los inputs
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldError);
    });
}

/**
 * Valida un campo individual
 */
function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    
    // Limpiar errores previos
    clearFieldError(event);
    
    // Validaciones específicas
    if (field.type === 'file' && field.files.length === 0) {
        showFieldError(field, 'Debe seleccionar un archivo');
        return false;
    }
    
    return true;
}

/**
 * Muestra error en un campo específico
 */
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    // Buscar o crear elemento de feedback
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    
    feedback.textContent = message;
}

/**
 * Limpia errores de un campo
 */
function clearFieldError(event) {
    const field = event.target;
    field.classList.remove('is-invalid');
    
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

/**
 * Configura mejoras de UX adicionales
 */
function setupUXEnhancements() {
    // Smooth scrolling para enlaces internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Auto-hide alerts después de 10 segundos
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        });
    }, 10000);
    
    // Mejorar accesibilidad con focus visible
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
}

/**
 * Muestra una alerta personalizada
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertContainer.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertContainer.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertContainer);
    
    // Auto-remove después de la duración especificada
    setTimeout(() => {
        if (document.body.contains(alertContainer)) {
            alertContainer.remove();
        }
    }, duration);
}

/**
 * Utilidades para la página de resultados
 */
if (window.location.pathname.includes('results')) {
    // Configurar funcionalidad específica de resultados
    setupResultsPageEnhancements();
}

function setupResultsPageEnhancements() {
    // Expandir/colapsar secciones
    setupCollapsibleSections();
    
    // Comparación de imágenes mejorada
    setupImageComparison();
    
    // Copy to clipboard para texto extraído
    setupCopyToClipboard();
    
    // Download all files functionality
    setupBulkDownload();
}

/**
 * Configura secciones colapsables
 */
function setupCollapsibleSections() {
    const cardHeaders = document.querySelectorAll('.card-header');
    cardHeaders.forEach(header => {
        if (header.dataset.collapsible !== 'false') {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const cardBody = header.nextElementSibling;
                if (cardBody && cardBody.classList.contains('card-body')) {
                    cardBody.style.display = cardBody.style.display === 'none' ? 'block' : 'none';
                    
                    const icon = header.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('fa-chevron-down');
                        icon.classList.toggle('fa-chevron-up');
                    }
                }
            });
        }
    });
}

/**
 * Configura comparación mejorada de imágenes
 */
function setupImageComparison() {
    const images = document.querySelectorAll('.image-container img');
    images.forEach(img => {
        img.addEventListener('click', function() {
            showImageModal(this.src, this.alt);
        });
    });
}

/**
 * Muestra imagen en modal para mejor visualización
 */
function showImageModal(src, alt) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${alt}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${src}" class="img-fluid" alt="${alt}">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

/**
 * Configura funcionalidad de copiar al portapapeles
 */
function setupCopyToClipboard() {
    const textContent = document.querySelector('.text-content pre');
    if (textContent) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
        copyBtn.innerHTML = '<i class="fas fa-copy me-1"></i>Copiar';
        
        const container = textContent.closest('.card-body');
        if (container) {
            container.style.position = 'relative';
            container.appendChild(copyBtn);
            
            copyBtn.addEventListener('click', function() {
                navigator.clipboard.writeText(textContent.textContent).then(() => {
                    copyBtn.innerHTML = '<i class="fas fa-check me-1"></i>Copiado';
                    copyBtn.classList.replace('btn-outline-secondary', 'btn-success');
                    
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy me-1"></i>Copiar';
                        copyBtn.classList.replace('btn-success', 'btn-outline-secondary');
                    }, 2000);
                });
            });
        }
    }
}

/**
 * Configura descarga masiva de archivos
 */
function setupBulkDownload() {
    const downloadSection = document.querySelector('.card:has(.fas.fa-download)');
    if (downloadSection) {
        const header = downloadSection.querySelector('.card-header');
        if (header) {
            const bulkBtn = document.createElement('button');
            bulkBtn.className = 'btn btn-sm btn-primary ms-2';
            bulkBtn.innerHTML = '<i class="fas fa-download me-1"></i>Descargar Todo';
            header.appendChild(bulkBtn);
            
            bulkBtn.addEventListener('click', function() {
                const downloadLinks = downloadSection.querySelectorAll('a[href*="download"]');
                downloadLinks.forEach((link, index) => {
                    setTimeout(() => {
                        link.click();
                    }, index * 1000); // Delay de 1 segundo entre descargas
                });
            });
        }
    }
}

// Exportar funciones para uso global si es necesario
window.OCRSystem = {
    showAlert,
    formatFileSize,
    showImageModal
};
