# Sistema OCR de Bajos Recursos

## Overview

This is a Python-based OCR (Optical Character Recognition) system designed for processing financial documents with low-resource requirements. The system focuses on pre-processing images to improve OCR accuracy without using machine learning or cloud services. It features a modular architecture with both web interface and command-line capabilities.

## System Architecture

### Backend Architecture
- **Flask Web Framework**: Lightweight web server for HTTP interface
- **Modular Python Design**: Four main processing modules working in sequence
- **File-based Processing**: Local image processing without external dependencies
- **Tesseract OCR Engine**: Core OCR functionality with customizable configurations

### Frontend Architecture
- **Bootstrap 5 Dark Theme**: Responsive web interface
- **Progressive Enhancement**: Works with and without JavaScript
- **Real-time File Preview**: Client-side image preview before processing
- **Dashboard Results**: Comprehensive result visualization with charts

### Processing Pipeline
1. **Image Validation** (`validador_ocr.py`): Quality analysis and diagnostics
2. **Image Enhancement** (`mejora_ocr.py`): Adaptive preprocessing based on diagnostics
3. **OCR Application** (`aplicador_ocr.py`): Text extraction with confidence validation
4. **Process Orchestration** (`main_ocr_process.py`): Coordinates all modules

## Key Components

### Core Processing Modules
- **ValidadorOCR**: Analyzes image quality, resolution, contrast, text regions
- **MejoradorOCR**: Applies adaptive image enhancements based on performance profiles
- **AplicadorOCR**: Executes OCR with Tesseract and extracts structured data
- **OrquestadorOCR**: Main coordinator that manages the complete workflow

### Web Interface
- **Flask Routes** (`routes.py`): File upload, processing, and result display
- **HTML Templates**: Bootstrap-based responsive interface
- **Static Assets**: Custom CSS/JS for enhanced user experience

### Configuration System
- **Centralized Config** (`config.py`): All system constants and settings
- **Performance Profiles**: Different processing modes (ultra_rapido, rapido, etc.)
- **Tesseract Configurations**: OCR engine parameter sets

## Data Flow

1. **Image Upload**: User uploads image via web interface or CLI
2. **Validation Phase**: Image quality analysis with detailed metrics
3. **Enhancement Phase**: Adaptive preprocessing based on validation results
4. **OCR Phase**: Text extraction with confidence scoring
5. **Result Generation**: Structured JSON output with diagnostics
6. **File Cleanup**: Temporary files managed automatically

## External Dependencies

### Core Libraries
- **OpenCV**: Image processing and computer vision operations
- **Pillow (PIL)**: Image manipulation and format handling
- **pytesseract**: Python wrapper for Tesseract OCR engine
- **scikit-image**: Additional image processing utilities
- **NumPy**: Numerical operations for image arrays

### Web Framework
- **Flask**: Web application framework
- **Werkzeug**: WSGI utilities and security helpers

### System Requirements
- **Tesseract OCR**: Must be installed at system level
- **Python 3.7+**: Core runtime environment
- **Ubuntu/Linux**: Optimized for Ubuntu but portable

## Deployment Strategy

### Local Development
- Direct Python execution with `python app.py`
- Development server on `0.0.0.0:5000`
- Auto-creation of required directories (`uploads`, `temp`, `static`)

### Production Considerations
- WSGI-ready Flask application
- ProxyFix middleware for reverse proxy support
- Environment-based configuration with `SESSION_SECRET`
- File size limits (16MB max) for security

### Resource Optimization
- No GPU requirements - CPU-only processing
- Multiple performance profiles for different hardware capabilities
- Efficient memory management with temporary file cleanup
- Minimal dependencies to reduce resource footprint

## Changelog

```
Changelog:
- July 01, 2025. Initial setup
- July 01, 2025. Critical fixes applied:
  * Implemented "Extreme Character Conservation Philosophy" for screenshot processing
  * Enhanced screenshot detection heuristics (aspect ratio, resolution-based)
  * Conservative deskew: only applies to scanned documents, skips screenshots
  * Reduced bilateral filtering and denoising for digital captures
  * Aggressive sharpening compensation for screenshots after light processing
  * Fixed JSON serialization errors with numpy types
  * Improved data structure validation in result generation
- July 01, 2025. Migration to Replit and critical OCR enhancement:
  * Fixed Flask session secret key configuration for Replit compatibility
  * Implemented CRITICAL FIX: Early color inversion detection in image processing
  * Now detects dark backgrounds and inverts colors BEFORE any processing steps
  * Prevents text degradation by avoiding processing white text on black backgrounds
  * Enforces "Extreme Character Conservation Philosophy" at the earliest stage
  * Ensures optimal OCR accuracy for dark-themed screenshots and documents
- July 01, 2025. Major system optimization implementing user-requested improvements:
  * ELIMINATED deskew phase completely - prevents false inclination detection in screenshots
  * ENHANCED binarization with advanced multi-algorithm system (Otsu, Sauvola, Adaptive)
  * UPGRADED to 'normal' profile by default for maximum precision OCR
  * IMPLEMENTED text display in BLACK color for better visibility in web interface  
  * INCREASED OCR confidence thresholds from 30 to 60 for higher accuracy
  * ADDED advanced image enhancement techniques beyond simple upscaling:
    - CLAHE adaptive histogram equalization for better contrast distribution
    - Unsharp masking for character-preserving sharpening
    - Adaptive gamma correction for optimal brightness
    - Intelligent edge enhancement for character definition
  * INTEGRATED "Sistema de Pre-procesamiento Inteligente" with extreme character conservation
  * OPTIMIZED Tesseract configurations for screenshot processing (high_confidence mode)
  * FIXED JSON serialization errors with NumPy types in all processing modules
- July 02, 2025. MAJOR ARCHITECTURAL TRANSFORMATION - ELITE Strategy Implementation:
  * REVOLUTIONARY CHANGE: Implemented complete ELITE OCR strategy eliminating dual-pass
  * BINARIZACIÓN ELITE: New algorithm producing perfect binary images (fondo 245-255, texto 0-10)
  * SINGLE-PASS OCR: Eliminated dual-pass processing for dramatic speed improvement
  * HISTOGRAM ANALYSIS: Added intelligent analysis of image tonalities for optimal binarization
  * CCA PURIFICATION: Implemented connected component analysis to eliminate non-textual elements
  * ELITE CONFIGURATION: New Tesseract configurations optimized for perfect binary images
  * SPEED OPTIMIZATION: Significantly faster processing while maintaining superior quality
  * ARCHITECTURAL MODULES UPDATED:
    - config.py: Added binarizacion_elite and analisis_componentes_conectados configurations
    - validador_ocr.py: Added histogram analysis for tonality ranges
    - mejora_ocr.py: Implemented ELITE binarization and CCA purification
    - aplicador_ocr.py: Transformed to single-pass OCR with ELITE optimizations
  * IMPACT: System now processes images with elite-level binary quality for optimal OCR results
- July 02, 2025. ADVANCED BACKGROUND UNIFICATION IMPLEMENTATION:
  * REVOLUTIONARY ENHANCEMENT: Implemented advanced heterogeneous background unification strategy
  * LOCAL VARIATION ANALYSIS: Added detection of multiple background types within single images
  * ADAPTIVE LOCALIZED BINARIZATION: Sauvola-Niblack hybrid algorithm for complex backgrounds
  * ABSOLUTE SHARPNESS: Post-binarization character sharpening for perfect text definition
  * INTELLIGENT BACKGROUND FILLING: Unified all background variations to uniform white (245-255)
  * ARCHITECTURAL MODULES ENHANCED:
    - config.py: Added unificacion_fondos_avanzada configuration parameters
    - validador_ocr.py: Added _analizar_variaciones_locales_fondo function
    - mejora_ocr.py: Enhanced _aplicar_binarizacion_elite with advanced background processing
  * IMPACT: Perfect background unification with absolute text sharpness for maximum OCR accuracy
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```