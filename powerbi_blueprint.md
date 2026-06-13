# Blueprint de Power BI - Monitoreo de Red

Este documento contiene la configuración técnica para generar los reportes de monitoreo en Power BI.

## 1. Modelo de Datos
- **Fuente**: PostgreSQL
- **Modo**: DirectQuery (recomendado para ver datos en tiempo real) o Import (para mejor rendimiento).
- **Tablas principales**: `v_trafico_resumen`

## 2. Fórmulas DAX Avanzadas

### Conteo de Eventos
```dax
Eventos Totales = COUNT('v_trafico_resumen'[id])
```

### Detección de IPs Externas (Flag)
```dax
Es Externa = 
IF(
    LEFT('v_trafico_resumen'[ip_destino], 3) = "192" || 
    LEFT('v_trafico_resumen'[ip_destino], 2) = "10" || 
    LEFT('v_trafico_resumen'[ip_destino], 3) = "172", 
    "Interna", 
    "Externa"
)
```

### Puertos de Riesgo
```dax
Nivel Riesgo = 
SWITCH( TRUE(),
    'v_trafico_resumen'[puerto_destino] IN {21, 22, 23, 3389, 445}, "Crítico",
    'v_trafico_resumen'[puerto_destino] > 1024, "Dinámico/Alto",
    "Estándar"
)
```

## 3. Estructura de los 4 Tableros Sugeridos

### T1: Ciberseguridad (Threat Hunting)
- **Kpis**: Conexiones a puertos críticos, IPs externas sospechosas.
- **Visuales**: Mapa de calor de IPs destino, Tabla de movimiento lateral (Origen=Local, Destino=Local).

### T2: Gestión de Activos (IT Inventory)
- **Kpis**: PCs activas hoy, Laboratorio con más carga.
- **Visuales**: Gráfico de barras de carga por PC, línea de tiempo de PCs conectadas simultáneamente.

### T3: Auditoría de Tráfico (Protocol Control)
- **Kpis**: % TCP vs UDP, Top 5 Servicios.
- **Visuales**: Treemap de protocolos, desglose de tráfico por puerto.

### T4: Mapa de Conexiones (Network Topology)
- **Visuales**: Sankey Diagram (Hostname -> IP Destino), Filtro por Laboratorio.

## 4. Publicación
Una vez diseñado el reporte (.pbix):
1. Archivo -> Publicar -> Mi área de trabajo.
2. Configura el **Gateway de Power BI** en el servidor si la base de datos no es accesible públicamente.
