#!/bin/bash

# --- CONFIGURACIÓN DE LA PRUEBA ---
NUM_ARCHIVOS=200
ENDPOINT="http://localhost:5000/api/ocr/process_image"
DIRECTORIO_IMAGENES="test_images_200"
TIPO_IMAGEN="png"
# --- FIN CONFIGURACIÓN ---

echo "Iniciando prueba de carga asíncrona con $NUM_ARCHIVOS archivos..."
START_TIME=$(date +%s.%N)

for i in $(seq 1 $NUM_ARCHIVOS); do
    ARCHIVO_ACTUAL="${DIRECTORIO_IMAGENES}/image_${i}.${TIPO_IMAGEN}"

    if [ ! -f "$ARCHIVO_ACTUAL" ]; then
        echo "Error: Archivo no encontrado - $ARCHIVO_ACTUAL"
        exit 1
    fi

    # Envía cada archivo de forma concurrente (asíncrona desde el cliente)
    curl -X POST -H "Content-Type: multipart/form-data" \
         -F "file=@$ARCHIVO_ACTUAL" \
         $ENDPOINT > /dev/null 2>&1 &

    # Sin sleep para máxima asincronía
done

wait # Espera a que todos los procesos de 'curl' en segundo plano terminen
END_TIME=$(date +%s.%N)

DURATION=$(echo "$END_TIME - $START_TIME" | bc)
echo "--- ENVÍO DE SOLICITUDES COMPLETADO ---"
echo "Tiempo Total de Envío de $NUM_ARCHIVOS Solicitudes (Asíncronas): $DURATION segundos"
echo "El sistema ahora estará procesando los archivos en segundo plano."
echo "Monitoreando logs y directorios de resultados..."

# Pausa para permitir que el backend termine de procesar
echo "Esperando a que el procesamiento backend finalice..."
sleep 60

echo "Verificando archivos procesados..."
PROCESSED_COUNT=$(find data/results/ data/historial/ -name "*.json" | wc -l)
echo "Archivos JSON de resultados encontrados (total acumulado): $PROCESSED_COUNT"