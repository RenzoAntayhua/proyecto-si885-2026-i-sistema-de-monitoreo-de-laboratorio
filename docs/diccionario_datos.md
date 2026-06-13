# Diccionario de Datos - PostgreSQL

Este diccionario describe la estructura de almacenamiento utilizada en PostgreSQL para la persistencia del sistema ETL y visualización en Power BI.

## Tabla: `laboratorios`
Almacena la información de los entornos monitoreados.
- `id` (UUID): Identificador único del laboratorio (PK).
- `nombre` (VARCHAR): Nombre representativo (ej. "LAB-A").
- `fecha_registro` (TIMESTAMP): Fecha de inserción.

## Tabla: `computadoras`
Registro de agentes conectados al sistema.
- `id` (UUID): Identificador único del agente (PK).
- `laboratorio_id` (UUID): Referencia al laboratorio (FK).
- `hostname` (VARCHAR): Nombre del host de la PC.
- `ip_address` (VARCHAR): Dirección IP local de la computadora.
- `status` (VARCHAR): Estado actual ("Online", "Disconnected").
- `last_sync` (TIMESTAMP): Última vez que el agente reportó.

## Tabla: `trafico_red`
Tabla central de hechos (Fact Table) que almacena cada evento de Sysmon.
- `id` (SERIAL): Identificador único del evento (PK).
- `computadora_id` (UUID): Computadora origen (FK).
- `timestamp_evento` (TIMESTAMP): Hora real del evento (systemTime).
- `ip_origen` (VARCHAR): IP del proceso que inicia la conexión.
- `ip_destino` (VARCHAR): IP externa a la que se conecta.
- `pais_destino` (VARCHAR): Geolocalización del destino (vía MaxMind).
- `ciudad_destino` (VARCHAR): Ciudad del destino.
- `puerto_destino` (INTEGER): Puerto de conexión.
- `protocolo` (VARCHAR): TCP / UDP.
- `proceso` (VARCHAR): Nombre del ejecutable (ej. chrome.exe).
