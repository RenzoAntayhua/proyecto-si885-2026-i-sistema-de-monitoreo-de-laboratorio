-- ============================================================================
-- Sistema de Monitoreo de Red Distribuido - Schema PostgreSQL
-- Archivo: infrastructure/schema.sql
-- Descripción: DDL completo para la base de datos network_monitor
-- ============================================================================

-- Habilitar extensión para generación de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLA: laboratorios
-- Descripción: Registra los laboratorios de cómputo monitoreados.
-- ============================================================================
CREATE TABLE IF NOT EXISTS laboratorios (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre          VARCHAR(255)    NOT NULL UNIQUE,
    descripcion     TEXT,
    creado_en       TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE laboratorios IS 'Laboratorios de cómputo monitoreados por el sistema.';
COMMENT ON COLUMN laboratorios.id IS 'Identificador único del laboratorio (UUID v4).';
COMMENT ON COLUMN laboratorios.nombre IS 'Nombre único del laboratorio (ej: LAB-101).';
COMMENT ON COLUMN laboratorios.descripcion IS 'Descripción opcional del laboratorio.';
COMMENT ON COLUMN laboratorios.creado_en IS 'Fecha y hora de creación del registro.';

-- ============================================================================
-- TABLA: computadoras
-- Descripción: PCs registradas en cada laboratorio con agente Wazuh instalado.
-- ============================================================================
CREATE TABLE IF NOT EXISTS computadoras (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    hostname        VARCHAR(255)    NOT NULL,
    laboratorio_id  UUID            NOT NULL REFERENCES laboratorios(id) ON DELETE CASCADE,
    ip_local        VARCHAR(45),
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    registrado_en   TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_computadoras_laboratorio_id ON computadoras(laboratorio_id);

COMMENT ON TABLE computadoras IS 'Computadoras registradas con agente Wazuh + Sysmon instalado.';
COMMENT ON COLUMN computadoras.hostname IS 'Nombre de máquina Windows (Environment.MachineName).';
COMMENT ON COLUMN computadoras.laboratorio_id IS 'FK al laboratorio al que pertenece la PC.';
COMMENT ON COLUMN computadoras.ip_local IS 'Dirección IP local de la PC en la red del laboratorio.';
COMMENT ON COLUMN computadoras.activo IS 'Indica si el agente de Wazuh sigue activo y conectado.';

-- ============================================================================
-- TABLA: trafico_red
-- Descripción: Eventos de tráfico de red capturados por Sysmon (Event ID 3)
--              y procesados por el motor ETL desde Wazuh Indexer.
-- ============================================================================
CREATE TABLE IF NOT EXISTS trafico_red (
    id                  BIGSERIAL       PRIMARY KEY,
    computadora_id      UUID            NOT NULL REFERENCES computadoras(id) ON DELETE CASCADE,
    timestamp_evento    TIMESTAMP       NOT NULL,
    ip_origen           VARCHAR(45),
    ip_destino          VARCHAR(45),
    pais_destino        VARCHAR(100),
    ciudad_destino      VARCHAR(100),
    puerto_destino      INT,
    protocolo           VARCHAR(10),
    proceso             VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_trafico_red_timestamp ON trafico_red(timestamp_evento);
CREATE INDEX IF NOT EXISTS idx_trafico_red_computadora ON trafico_red(computadora_id);

COMMENT ON TABLE trafico_red IS 'Eventos de conexión de red (Sysmon Event ID 3) procesados por ETL.';
COMMENT ON COLUMN trafico_red.timestamp_evento IS 'Timestamp original del evento capturado por Sysmon.';
COMMENT ON COLUMN trafico_red.ip_origen IS 'IP de origen de la conexión (sourceIp).';
COMMENT ON COLUMN trafico_red.ip_destino IS 'IP de destino de la conexión (destinationIp).';
COMMENT ON COLUMN trafico_red.pais_destino IS 'País estimado de la IP destino (GeoIP).';
COMMENT ON COLUMN trafico_red.ciudad_destino IS 'Ciudad estimada de la IP destino (GeoIP).';
COMMENT ON COLUMN trafico_red.puerto_destino IS 'Puerto de destino de la conexión.';
COMMENT ON COLUMN trafico_red.protocolo IS 'Protocolo de red utilizado (tcp, udp, etc.).';
COMMENT ON COLUMN trafico_red.proceso IS 'Ruta del ejecutable que originó la conexión (Sysmon Image).';

-- ============================================================================
-- TABLA: etl_estado
-- Descripción: Tabla de control para el motor ETL. Guarda el estado de la
--              última ejecución para implementar carga incremental.
-- ============================================================================
CREATE TABLE IF NOT EXISTS etl_estado (
    id                      SERIAL      PRIMARY KEY,
    ultimo_timestamp        TIMESTAMP   NOT NULL DEFAULT '1970-01-01 00:00:00',
    registros_procesados    BIGINT      DEFAULT 0,
    actualizado_en          TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Insertar registro inicial de estado ETL
INSERT INTO etl_estado (ultimo_timestamp, registros_procesados)
VALUES ('1970-01-01 00:00:00', 0)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE etl_estado IS 'Estado de control del motor ETL para carga incremental.';
COMMENT ON COLUMN etl_estado.ultimo_timestamp IS 'Timestamp del último evento procesado exitosamente.';
COMMENT ON COLUMN etl_estado.registros_procesados IS 'Total acumulado de registros procesados.';

-- ============================================================================
-- VISTA: v_trafico_resumen
-- Descripción: Vista de conveniencia para Power BI y consultas de dashboard.
-- ============================================================================
CREATE OR REPLACE VIEW v_trafico_resumen AS
SELECT
    tr.id,
    tr.timestamp_evento,
    tr.ip_origen,
    tr.ip_destino,
    tr.pais_destino,
    tr.ciudad_destino,
    tr.puerto_destino,
    tr.protocolo,
    c.hostname,
    c.ip_local,
    l.nombre AS laboratorio_nombre,
    tr.proceso
FROM trafico_red tr
JOIN computadoras c ON tr.computadora_id = c.id
JOIN laboratorios l ON c.laboratorio_id = l.id
ORDER BY tr.timestamp_evento DESC;

COMMENT ON VIEW v_trafico_resumen IS 'Vista consolidada de tráfico con datos de PC y laboratorio para BI.';
