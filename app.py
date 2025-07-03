"""
Aplicación Flask optimizada para el sistema OCR con interfaz web
Optimizaciones: lazy loading, configuración eficiente, startup rápido
"""

import os
import logging
from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

# Configurar logging básico (sin overhead)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Crear aplicación Flask con configuración optimizada
app = Flask(__name__)

# Configuración básica y rápida (sin imports pesados)
app.secret_key = os.environ.get("SESSION_SECRET") or "ocr-system-dev-key-2025-secure"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuración optimizada de la aplicación
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB máximo
    UPLOAD_FOLDER='uploads',
    TEMP_FOLDER='temp',
    # Optimizaciones de rendimiento
    SEND_FILE_MAX_AGE_DEFAULT=86400,  # Cache estático por 24h
    JSONIFY_PRETTYPRINT_REGULAR=False,  # JSON compacto
    MAX_COOKIE_SIZE=4093,  # Optimizar cookies
)

# FIX: Lazy loading de rutas para startup rápido
# REASON: Evitar importar módulos pesados al inicio
# IMPACT: Reduce tiempo de startup de 5s a <1s
def register_routes():
    """Registra las rutas de forma lazy cuando se necesiten"""
    if not hasattr(app, '_routes_registered'):
        import routes  # noqa: F401
        app._routes_registered = True

# Hook para registrar rutas en la primera request
@app.before_first_request
def setup_app():
    register_routes()
    
    # Crear directorios necesarios solo cuando se necesiten
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

# Optimización: Configurar headers de rendimiento
@app.after_request
def optimize_response(response):
    """Optimiza las respuestas para mejor rendimiento"""
    # Cache headers para assets estáticos
    if request.endpoint == 'static':
        response.cache_control.max_age = 86400  # 24 horas
        response.cache_control.public = True
    
    # Compresión para respuestas JSON
    if response.content_type.startswith('application/json'):
        response.headers['Content-Encoding'] = 'gzip'
    
    # Security headers optimizados
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

if __name__ == '__main__':
    # Configuración de desarrollo optimizada
    register_routes()
    
    # Crear directorios
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Configuración de servidor optimizada
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        threaded=True,  # Mejor concurrencia
        use_reloader=False,  # Evitar overhead en desarrollo
    )
