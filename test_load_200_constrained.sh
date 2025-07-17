#!/bin/bash

# --- CONFIGURACIÓN DE LA PRUEBA ---
NUM_ARCHIVOS=200
ENDPOINT="http://localhost:5000/api/ocr/process_image"
DIRECTORIO_IMAGENES="test_images_200"
TIPO_IMAGEN="png"
# --- FIN CONFIGURACIÓN ---

echo "=== PRUEBA DE CARGA ASÍNCRONA CON RECURSOS LIMITADOS ==="
echo "Iniciando prueba de carga asíncrona con $NUM_ARCHIVOS archivos simulando entorno de 2GB RAM / 4 núcleos..."

# Capturar estado inicial
echo "Estado inicial del sistema:"
free -h
echo "Load average inicial:"
uptime

START_TIME=$(date +%s.%N)
echo "Tiempo de inicio: $(date)"

# Crear archivo de monitoreo
echo "Timestamp,Memory_Used_MB,Memory_Available_MB,CPU_Load" > resource_monitor.csv

# Función de monitoreo en segundo plano
monitor_resources() {
    while true; do
        TIMESTAMP=$(date +%s)
        MEMORY_USED=$(free -m | awk 'NR==2{print $3}')
        MEMORY_AVAILABLE=$(free -m | awk 'NR==2{print $7}')
        CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
        echo "$TIMESTAMP,$MEMORY_USED,$MEMORY_AVAILABLE,$CPU_LOAD" >> resource_monitor.csv
        sleep 2
    done
}

# Iniciar monitoreo
monitor_resources &
MONITOR_PID=$!

echo "Enviando $NUM_ARCHIVOS archivos de forma asíncrona..."

for i in $(seq 1 $NUM_ARCHIVOS); do
    ARCHIVO_ACTUAL="${DIRECTORIO_IMAGENES}/image_${i}.${TIPO_IMAGEN}"

    if [ ! -f "$ARCHIVO_ACTUAL" ]; then
        echo "Error: Archivo no encontrado - $ARCHIVO_ACTUAL"
        kill $MONITOR_PID
        exit 1
    fi

    # Envía cada archivo de forma concurrente
    curl -X POST -H "Content-Type: multipart/form-data" \
         -F "file=@$ARCHIVO_ACTUAL" \
         $ENDPOINT > /dev/null 2>&1 &

    # Mostrar progreso cada 20 archivos
    if [ $((i % 20)) -eq 0 ]; then
        echo "Enviados $i/$NUM_ARCHIVOS archivos..."
    fi
done

wait # Espera a que todos los procesos de curl terminen
END_TIME=$(date +%s.%N)

DURATION=$(python3 -c "print(f'{$END_TIME - $START_TIME:.2f}')")

echo "--- ENVÍO DE SOLICITUDES COMPLETADO ---"
echo "Tiempo Total de Envío de $NUM_ARCHIVOS Solicitudes (Asíncronas): $DURATION segundos"
echo "Tiempo de finalización del envío: $(date)"
echo "El sistema ahora estará procesando los archivos en segundo plano con recursos limitados."

# Monitorear estado durante el procesamiento
echo "Esperando a que el procesamiento backend finalice..."
echo "Estado del sistema después del envío:"
free -h
uptime

# Esperar más tiempo para el procesamiento
sleep 90

echo "Verificando archivos procesados..."
PROCESSED_COUNT_RESULTS=$(find data/results/ -name "*.json" | wc -l)
PROCESSED_COUNT_HISTORIAL=$(find data/historial/ -name "*.json" | wc -l)
PROCESSED_COUNT_TOTAL=$((PROCESSED_COUNT_RESULTS + PROCESSED_COUNT_HISTORIAL))

echo "Archivos JSON en data/results/: $PROCESSED_COUNT_RESULTS"
echo "Archivos JSON en data/historial/: $PROCESSED_COUNT_HISTORIAL"
echo "Total archivos procesados: $PROCESSED_COUNT_TOTAL"

# Detener monitoreo
kill $MONITOR_PID 2>/dev/null

echo "Estado final del sistema:"
free -h
uptime

echo "=== RESUMEN DE LA PRUEBA ==="
echo "Archivos enviados: $NUM_ARCHIVOS"
echo "Tiempo de envío: $DURATION segundos"
echo "Archivos procesados: $PROCESSED_COUNT_TOTAL"
echo "Tasa de éxito: $(python3 -c "print(f'{$PROCESSED_COUNT_TOTAL/$NUM_ARCHIVOS*100:.1f}%')")"
echo "Archivo de monitoreo: resource_monitor.csv"

echo "Continúa monitoreando para verificar que todos los archivos se procesen completamente."