"""
housekeeping.py - Limpieza de datos antiguos para evitar llenado de disco.
"""

import os
import logging
from typing import Dict, Any

import psycopg2

logger = logging.getLogger(__name__)

# ── Configuración de DB ─────────────────────────────────────────────────────
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = os.getenv("PG_DATABASE", "network_monitor")
DB_USER = os.getenv("PG_USER", "netmon_user")
DB_PASS = os.getenv("PG_PASSWORD", "changeme")

# Cuántos días de historial queremos conservar (por defecto 30)
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))

def _get_pg_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )

def run_housekeeping() -> Dict[str, Any]:
    """
    Elimina registros de tráfico más antiguos que RETENTION_DAYS.
    """
    logger.info(f"Iniciando housekeeping de tráfico de red (Retención: {RETENTION_DAYS} días)...")
    conn = _get_pg_connection()
    cursor = conn.cursor()
    
    stats = {"registros_eliminados": 0, "dias_retencion": RETENTION_DAYS}
    
    try:
        # Se ejecuta el borrado de registros antiguos
        query = f"DELETE FROM trafico_red WHERE timestamp_evento < NOW() - INTERVAL '{RETENTION_DAYS} days'"
        cursor.execute(query)
        stats["registros_eliminados"] = cursor.rowcount
        
        # Vacuuma la tabla para recuperar el espacio en disco (Opcional, pero recomendado en Postgres)
        # Nota: Un VACUUM FULL requiere bloqueos, por lo que aquí solo hacemos commit.
        conn.commit()
        
        logger.info(f"Housekeeping completado. Registros eliminados: {stats['registros_eliminados']}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en housekeeping: {e}", exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()
        
    return stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_housekeeping()
