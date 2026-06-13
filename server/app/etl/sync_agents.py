"""
sync_agents.py - Sincroniza el estado de los agentes de Wazuh con PostgreSQL.

Consulta la API de Wazuh para obtener los agentes activos y actualiza 
la columna 'activo' de la tabla 'computadoras' en PostgreSQL.
"""

import os
import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib3
from typing import List, Dict, Any

import psycopg2

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# ── Configuración de Wazuh API ──────────────────────────────────────────────
WAZUH_API_HOST = os.getenv("WAZUH_API_HOST", "localhost")
WAZUH_API_PORT = int(os.getenv("WAZUH_API_PORT", "55000"))
WAZUH_API_USER = os.getenv("WAZUH_API_USER", "wazuh")
WAZUH_API_PASS = os.getenv("WAZUH_API_PASS", "wazuh")

# ── Configuración de DB ─────────────────────────────────────────────────────
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = os.getenv("PG_DATABASE", "network_monitor")
DB_USER = os.getenv("PG_USER", "netmon_user")
DB_PASS = os.getenv("PG_PASSWORD", "changeme")


def _get_pg_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )


def get_wazuh_token() -> str:
    """Obtiene el JWT de la API de Wazuh."""
    url = f"https://{WAZUH_API_HOST}:{WAZUH_API_PORT}/security/user/authenticate"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(WAZUH_API_USER, WAZUH_API_PASS),
        verify=False,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("token")


def get_active_agents(token: str) -> List[str]:
    """Retorna una lista de hostnames (nombres) de agentes de Wazuh activos."""
    url = f"https://{WAZUH_API_HOST}:{WAZUH_API_PORT}/agents"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"status": "active", "limit": 100000}
    
    response = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    items = data.get("data", {}).get("affected_items", [])
    active_hostnames = [item.get("name") for item in items if item.get("name")]
    return active_hostnames


def run_agent_sync() -> Dict[str, Any]:
    """
    Sincroniza el estado 'activo' en la BD basado en los agentes activos de Wazuh.
    Retorna un diccionario con estadísticas de la sincronización.
    """
    logger.info("Iniciando sincronización de agentes Wazuh...")
    conn = _get_pg_connection()
    cursor = conn.cursor()
    
    stats = {
        "activos_en_wazuh": 0,
        "marcados_activos_db": 0,
        "marcados_inactivos_db": 0
    }

    try:
        # 1. Obtener agentes activos desde Wazuh API
        try:
            token = get_wazuh_token()
            active_hostnames = get_active_agents(token)
            stats["activos_en_wazuh"] = len(active_hostnames)
            logger.info(f"Agentes activos encontrados en Wazuh: {len(active_hostnames)}")
        except Exception as e:
            logger.error(f"No se pudo conectar a la API de Wazuh: {e}")
            raise RuntimeError(f"Error conectando a Wazuh API: {e}")

        # 2. Actualizar PostgreSQL
        logger.info(f"Hostnames recibidos de la API: {active_hostnames}")
        if active_hostnames:
            # Convertir a minúsculas y sin espacios para cruce seguro
            active_hostnames_clean = [h.strip().lower() for h in active_hostnames]

            # Marcar activos los que están en la lista
            cursor.execute(
                "UPDATE computadoras SET activo = TRUE WHERE LOWER(TRIM(hostname)) = ANY(%s) AND activo = FALSE",
                (active_hostnames_clean,)
            )
            stats["marcados_activos_db"] = cursor.rowcount
            
            # Marcar inactivos los que NO están en la lista
            cursor.execute(
                "UPDATE computadoras SET activo = FALSE WHERE LOWER(TRIM(hostname)) != ALL(%s) AND activo = TRUE",
                (active_hostnames_clean,)
            )
            stats["marcados_inactivos_db"] = cursor.rowcount
        else:
            # Si no hay ningún agente activo, marcar todos inactivos
            cursor.execute("UPDATE computadoras SET activo = FALSE WHERE activo = TRUE")
            stats["marcados_inactivos_db"] = cursor.rowcount

        conn.commit()
        logger.info(f"Sincronización completada. Activos restaurados: {stats['marcados_activos_db']}, "
                    f"Marcados inactivos: {stats['marcados_inactivos_db']}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error en sincronización de agentes: {e}", exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()

    return stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_agent_sync()
