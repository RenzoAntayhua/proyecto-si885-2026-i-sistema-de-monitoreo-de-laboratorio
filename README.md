# 🛡️ Sysmon Telemetry Platform

Plataforma unificada para la captura, procesamiento y visualización de tráfico de red a nivel de endpoints utilizando Sysmon, Wazuh, PostgreSQL, Python ETL y Next.js.

## 📐 Arquitectura del Sistema

El sistema utiliza una arquitectura orientada a eventos para capturar el tráfico de red de los laboratorios en tiempo real.

```mermaid
graph TD
    subgraph Laboratorios Universitarios
        A1[PC 1 - Sysmon] -->|Logs| WZ(Wazuh Agent)
        A2[PC 2 - Sysmon] -->|Logs| WZ
    end

    subgraph Azure Cloud - VPS Ubuntu
        WZ -->|Puerto 1514| WM(Wazuh Manager)
        WM -->|JSON Logs| OS(OpenSearch / Filebeat)
        
        OS -->|REST API| ETL(Python ETL Worker)
        
        subgraph Procesamiento
            ETL -->|Limpia y Geolocaliza| ETL
        end
        
        ETL -->|Inserta| DB[(PostgreSQL)]
        
        API(FastAPI Backend) -->|Lee métricas| DB
        DASH(Next.js Dashboard) -->|Peticiones HTTP| API
    end

    subgraph Usuario Final
        USER((Administrador TI)) -->|HTTPS 8443| DASH
        USER -->|Reportes PBIX| PBI(Power BI Embedded)
        PBI -->|DirectQuery| DB
    end
```

## 🚀 Tecnologías Utilizadas
- **Infraestructura:** Terraform, Microsoft Azure.
- **Seguridad y Captura:** Sysmon (Event ID 3), Wazuh HIDS.
- **Data Pipeline:** Python 3, OpenSearch, MaxMind GeoIP.
- **Almacenamiento:** PostgreSQL.
- **Frontend & BI:** React / Next.js, Power BI.
- **CI/CD:** GitHub Actions.

## 🛠️ Despliegue Automático (Terraform)
La infraestructura se levanta en Azure utilizando Terraform.
1. Instalar Terraform y Azure CLI (`az login`).
2. Entrar a `infrastructure/terraform`.
3. Ejecutar `terraform init && terraform apply -auto-approve`.

## 📦 Estructura del Repositorio
- `/infrastructure`: Scripts de Terraform para IaC.
- `/server`: Backend en FastAPI y script ETL (`worker.py`).
- `/dashboard`: Frontend en Next.js.
- `/installer`: Código fuente del instalador para las PCs clientes en C#.
- `/docs`: Informes del proyecto (FD01 - FD05) y Diccionario de Datos.
