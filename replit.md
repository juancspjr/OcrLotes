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
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```