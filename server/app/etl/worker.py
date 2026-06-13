"""
worker.py - Demonio de Streaming en Tiempo Real para el ETL.

Este script ejecuta el ciclo ETL en un bucle infinito, asegurando que los datos
pasen de OpenSearch a PostgreSQL con un retardo de tan solo unos segundos.
Está diseñado para ser ejecutado en segundo plano con PM2 o Systemd.
"""

import time
import logging
import sys

# Ajustar el sys.path para poder importar los módulos de app
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.etl.engine import run_etl

# Configuración de log exclusiva para el worker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("etl_worker")

# Tiempo de espera en segundos entre cada chequeo de nuevos eventos
SLEEP_INTERVAL_SECONDS = 1

def start_worker():
    logger.info("===================================================")
    logger.info("Iniciando Worker ETL en Tiempo Real (Streaming)")
    logger.info(f"Intervalo de sincronización: {SLEEP_INTERVAL_SECONDS} segundos")
    logger.info("Presiona Ctrl+C para detener")
    logger.info("===================================================")

    while True:
        try:
            # Ejecutamos el ciclo ETL normal
            procesados = run_etl()
            
            if procesados > 0:
                logger.info(f"Ciclo completado. {procesados} nuevos eventos ingestados a PostgreSQL.")
            
        except Exception as e:
            # Si ocurre un error (ej. se cae Postgres u OpenSearch momentáneamente),
            # no detenemos el script. Logueamos y esperamos al siguiente ciclo.
            logger.error(f"Error crítico en el ciclo ETL: {e}", exc_info=True)
            logger.warning(f"Reintentando en {SLEEP_INTERVAL_SECONDS * 2} segundos...")
            time.sleep(SLEEP_INTERVAL_SECONDS * 2)
            continue
        
        # Esperar antes de consultar de nuevo
        time.sleep(SLEEP_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        start_worker()
    except KeyboardInterrupt:
        logger.info("Worker detenido manualmente por el usuario.")
        sys.exit(0)
