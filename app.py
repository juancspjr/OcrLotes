"""
Aplicación Flask para el sistema OCR con interfaz web
"""

import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Crear aplicación Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuración de la aplicación
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB máximo
    UPLOAD_FOLDER='uploads',
    TEMP_FOLDER='temp'
)

# Importar rutas
import routes

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
