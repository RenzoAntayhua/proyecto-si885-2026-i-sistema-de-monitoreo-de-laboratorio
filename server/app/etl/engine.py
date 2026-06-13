"""
engine.py - Motor ETL: OpenSearch (Wazuh Indexer) → PostgreSQL.

Extrae eventos Sysmon Event ID 3 (NetworkConnect) del índice wazuh-alerts-*,
los transforma y los carga en la tabla trafico_red.
Implementa carga incremental usando la tabla etl_estado.
"""

import os
import logging
import ipaddress
from datetime import datetime, timezone
from typing import Optional, Tuple

import psycopg2
import psycopg2.extras
import maxminddb
from opensearchpy import OpenSearch
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configuración ───────────────────────────────────────────────────────────
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "admin")

DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = os.getenv("PG_DATABASE", "network_monitor")
DB_USER = os.getenv("PG_USER", "netmon_user")
DB_PASS = os.getenv("PG_PASSWORD", "changeme")
MAXMIND_DB_PATH = os.getenv("MAXMIND_DB_PATH", "GeoLite2-City.mmdb")


def _get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
        timeout=30,
    )


def _get_pg_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )


def _get_last_timestamp(cursor) -> str:
    cursor.execute("SELECT ultimo_timestamp FROM etl_estado ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row and row[0]:
        return row[0].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return "1970-01-01T00:00:00.000Z"


def _build_query(since_timestamp: str, size: int = 1000) -> dict:
    """Construye la query DSL para filtrar eventos Sysmon NetworkConnect."""
    return {
        "size": size,
        "sort": [{"timestamp": {"order": "asc"}}],
        "query": {
            "bool": {
                "must": [
                    {"match": {"data.win.system.eventID": "3"}},
                    {"match": {"data.win.system.providerName": "Microsoft-Windows-Sysmon"}},
                    {"exists": {"field": "agent.labels.laboratorio"}}
                ],
                "filter": [
                    {"range": {"timestamp": {"gt": since_timestamp}}}
                ]
            }
        },
        "_source": [
            "timestamp",
            "agent.name",
            "agent.labels.laboratorio",
            "data.win.eventdata.sourceIp",
            "data.win.eventdata.destinationIp",
            "data.win.eventdata.destinationPort",
            "data.win.eventdata.protocol",
            "data.win.eventdata.image",
            "data.win.system.systemTime"
        ]
    }


def _resolve_computadora_id(cursor, hostname: str) -> Optional[str]:
    """Resuelve el UUID de computadora a partir del hostname."""
    cursor.execute(
        "SELECT id FROM computadoras WHERE LOWER(TRIM(hostname)) = LOWER(TRIM(%s)) LIMIT 1",
        (hostname,)
    )
    row = cursor.fetchone()
    return str(row[0]) if row else None


def _safe_get(source: dict, dotted_key: str, default=None):
    """Accede a un valor anidado usando notación con puntos."""
    keys = dotted_key.split(".")
    current = source
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def _resolve_geoip(destination_ip: Optional[str], geoip_reader) -> Tuple[Optional[str], Optional[str]]:
    """
    Resuelve país y ciudad de una IP destino.
    Para IPs privadas/LAN devuelve etiquetas locales para facilitar análisis.
    """
    if not destination_ip:
        return None, None

    try:
        ip_obj = ipaddress.ip_address(destination_ip)
    except ValueError:
        return None, None

    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
        return "LAN", "Red Local"

    if geoip_reader is None:
        return None, None

    try:
        geo_data = geoip_reader.get(destination_ip) or {}
    except Exception:
        logger.debug("No se pudo resolver GeoIP para %s", destination_ip, exc_info=True)
        return None, None

    country = _safe_get(geo_data, "country.names.es") or _safe_get(geo_data, "country.names.en")
    city = _safe_get(geo_data, "city.names.es") or _safe_get(geo_data, "city.names.en")
    return country, city


def run_etl() -> int:
    """
    Ejecuta el ciclo ETL completo.
    Retorna el número de registros procesados.
    """
    logger.info("Iniciando ciclo ETL...")
    conn = _get_pg_connection()
    cursor = conn.cursor()
    total_inserted = 0
    last_event_ts = None
    geoip_reader = None

    try:
        # 0. Cargar base de datos GeoIP si está disponible
        if os.path.exists(MAXMIND_DB_PATH):
            geoip_reader = maxminddb.open_database(MAXMIND_DB_PATH)
            logger.info("Base GeoIP cargada desde %s", MAXMIND_DB_PATH)
        else:
            logger.warning("No se encontró base GeoIP en %s. Se continuará sin geolocalización pública.", MAXMIND_DB_PATH)

        # 1. Obtener último timestamp procesado
        since_ts = _get_last_timestamp(cursor)
        logger.info(f"Buscando eventos desde: {since_ts}")

        # 2. Conectar a OpenSearch
        os_client = _get_opensearch_client()

        # 3. Scroll a través de resultados
        has_more = True
        while has_more:
            query = _build_query(since_ts, size=10000)
            response = os_client.search(index="wazuh-alerts-*", body=query)
            hits = response.get("hits", {}).get("hits", [])

            if not hits:
                has_more = False
                break

            # 4. Transformar y preparar para inserción
            records = []
            for hit in hits:
                source = hit.get("_source", {})
                
                # Avanzamos el timestamp siempre, independientemente de si omitimos el registro
                # Extraer tiempos
                reception_ts_str = source.get("timestamp", "")
                system_ts_str = _safe_get(source, "data.win.system.systemTime")

                try:
                    # Tiempo de recepción (para el estado del ETL)
                    reception_ts = datetime.fromisoformat(reception_ts_str.replace("Z", "+00:00"))
                    
                    # Tiempo real del evento (para el gráfico)
                    if system_ts_str:
                        ts_evento = datetime.fromisoformat(system_ts_str.replace("Z", "+00:00"))
                    else:
                        ts_evento = reception_ts
                except (ValueError, AttributeError):
                    reception_ts = datetime.now(timezone.utc)
                    ts_evento = reception_ts
                
                last_event_ts = reception_ts

                hostname = _safe_get(source, "agent.name")
                if not hostname:
                    continue

                computadora_id = _resolve_computadora_id(cursor, hostname)
                if not computadora_id:
                    logger.warning(f"PC no registrada: {hostname}, omitiendo evento.")
                    continue

                destination_ip = _safe_get(source, "data.win.eventdata.destinationIp")
                pais_destino, ciudad_destino = _resolve_geoip(destination_ip, geoip_reader)
                
                # Extraer solo el nombre del ejecutable (ej. "chrome.exe") en lugar de la ruta completa
                image_path = _safe_get(source, "data.win.eventdata.image")
                proceso_name = image_path.split("\\")[-1].split("/")[-1] if image_path else None

                records.append((
                    computadora_id,
                    ts_evento,
                    _safe_get(source, "data.win.eventdata.sourceIp"),
                    destination_ip,
                    pais_destino,
                    ciudad_destino,
                    _safe_get(source, "data.win.eventdata.destinationPort"),
                    _safe_get(source, "data.win.eventdata.protocol"),
                    proceso_name,
                ))

            # 5. Bulk insert
            if records:
                insert_sql = """
                    INSERT INTO trafico_red
                        (
                            computadora_id, timestamp_evento, ip_origen, ip_destino,
                            pais_destino, ciudad_destino, puerto_destino, protocolo, proceso
                        )
                    VALUES %s
                """
                psycopg2.extras.execute_values(cursor, insert_sql, records, page_size=500)
                total_inserted += len(records)
                logger.info(f"Insertados {len(records)} registros (total: {total_inserted})")

            # Actualizar since_ts para siguiente página
            if last_event_ts:
                since_ts = last_event_ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            if len(hits) < 500:
                has_more = False

        # 6. Actualizar estado ETL
        if last_event_ts:
            cursor.execute("""
                UPDATE etl_estado SET
                    ultimo_timestamp = %s,
                    registros_procesados = registros_procesados + %s,
                    actualizado_en = NOW()
                WHERE id = (SELECT id FROM etl_estado ORDER BY id DESC LIMIT 1)
            """, (last_event_ts, total_inserted))

        conn.commit()
        logger.info(f"ETL completado. Total registros procesados: {total_inserted}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error en ETL: {e}", exc_info=True)
        raise
    finally:
        if geoip_reader is not None:
            geoip_reader.close()
        cursor.close()
        conn.close()

    return total_inserted
