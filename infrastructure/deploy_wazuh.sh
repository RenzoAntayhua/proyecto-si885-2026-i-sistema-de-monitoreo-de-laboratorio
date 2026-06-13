#!/bin/bash
# ============================================================================
# Sistema de Monitoreo de Red Distribuido
# Script: deploy_wazuh.sh
# Descripción: Despliegue desatendido de Wazuh All-in-one + PostgreSQL
#              en un servidor Debian/Ubuntu.
# Uso: sudo bash deploy_wazuh.sh
# ============================================================================

set -euo pipefail

# ── Colores para output ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Variables configurables ─────────────────────────────────────────────────
DB_NAME="network_monitor"
DB_USER="netmon_user"
DB_PASS="NetMon_S3cur3_$(openssl rand -hex 4)"
SCHEMA_PATH="$(dirname "$0")/schema.sql"

# ── Funciones auxiliares ────────────────────────────────────────────────────
log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script debe ejecutarse como root (sudo)."
        exit 1
    fi
}

check_os() {
    if ! grep -qiE 'debian|ubuntu' /etc/os-release 2>/dev/null; then
        log_error "Este script solo soporta Debian/Ubuntu."
        exit 1
    fi
    log_ok "Sistema operativo compatible detectado."
}

check_connectivity() {
    if ! curl -s --connect-timeout 5 https://packages.wazuh.com > /dev/null 2>&1; then
        log_error "No se puede conectar a packages.wazuh.com. Verifique la conectividad."
        exit 1
    fi
    log_ok "Conectividad a Internet verificada."
}

get_primary_ip() {
    ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1
}

# ── Verificaciones previas ──────────────────────────────────────────────────
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Sistema de Monitoreo de Red - Despliegue del Servidor Central${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

check_root
check_os
check_connectivity

PRIMARY_IP=$(get_primary_ip)
log_info "IP principal detectada: ${PRIMARY_IP}"

# ── 1. Actualización del sistema ────────────────────────────────────────────
log_info "Actualizando paquetes del sistema..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl apt-transport-https lsb-release gnupg2 \
    software-properties-common unzip wget ufw
log_ok "Sistema actualizado."

# ── 2. Instalación de Wazuh All-in-one (desatendida) ───────────────────────
log_info "Descargando e instalando Wazuh All-in-one (Manager + Indexer + Dashboard)..."

curl -sO https://packages.wazuh.com/4.9/wazuh-install.sh
curl -sO https://packages.wazuh.com/4.9/config.yml

# Configurar config.yml con la IP del servidor
cat > config.yml << WAZUH_CONFIG
nodes:
  indexer:
    - name: node-1
      ip: "${PRIMARY_IP}"

  server:
    - name: wazuh-1
      ip: "${PRIMARY_IP}"

  dashboard:
    - name: dashboard
      ip: "${PRIMARY_IP}"
WAZUH_CONFIG

# Usamos el modo all-in-one para simplificar y evitar errores de validación de IP
# Solo ejecutamos si no existe wazuh-control
if ! command -v /var/ossec/bin/wazuh-control >/dev/null 2>&1; then
    bash wazuh-install.sh --all-in-one -i
else
    log_warn "Wazuh ya parece estar instalado. Saltando instalación de binarios para continuar con el resto..."
fi

# Extraer credenciales de Wazuh
WAZUH_PASSWORDS_FILE="/tmp/wazuh-passwords.txt"
tar -xvf wazuh-install-files.tar -C /tmp/ 2>/dev/null || true
if [[ -f /tmp/wazuh-install-files/wazuh-passwords.txt ]]; then
    cp /tmp/wazuh-install-files/wazuh-passwords.txt "${WAZUH_PASSWORDS_FILE}"
fi

log_ok "Wazuh All-in-one instalado correctamente."

# ── 3. Instalación de PostgreSQL ────────────────────────────────────────────
log_info "Instalando PostgreSQL..."

apt-get install -y -qq postgresql postgresql-contrib

systemctl enable postgresql
systemctl start postgresql

# Crear usuario y base de datos
su - postgres -c "psql -c \"CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';\"" 2>/dev/null || \
    log_warn "Usuario ${DB_USER} ya existe."
su - postgres -c "psql -c \"CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};\"" 2>/dev/null || \
    log_warn "Base de datos ${DB_NAME} ya existe."
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};\""

# Ejecutar schema
if [[ -f "${SCHEMA_PATH}" ]]; then
    cp "${SCHEMA_PATH}" /tmp/schema.sql
    chmod 644 /tmp/schema.sql
    su - postgres -c "psql -d ${DB_NAME} -f /tmp/schema.sql"
    rm /tmp/schema.sql
    log_ok "Schema SQL aplicado correctamente."
else
    log_warn "No se encontró schema.sql en ${SCHEMA_PATH}. Ejecute manualmente."
fi

# Configurar pg_hba.conf para aceptar conexiones remotas (para Power BI)
PG_HBA=$(find /etc/postgresql -name pg_hba.conf | head -1)
PG_CONF=$(find /etc/postgresql -name postgresql.conf | head -1)

if [[ -n "$PG_HBA" ]]; then
    # Permitir que netmon_user acceda a todas las DBs desde cualquier IP
    echo "host    all    ${DB_USER}    0.0.0.0/0    md5" >> "$PG_HBA"
fi

if [[ -n "$PG_CONF" ]]; then
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
fi

systemctl restart postgresql
log_ok "PostgreSQL configurado y ejecutándose."

# ── 4. Instalación de Python 3.11+ ─────────────────────────────────────────
log_info "Instalando Python 3..."

apt-get install -y -qq python3 python3-pip python3-venv
log_ok "Python $(python3 --version) instalado."

# ── 5. Instalación de Node.js 20 LTS ───────────────────────────────────────
log_info "Instalando Node.js 20 LTS..."

curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y -qq nodejs
log_ok "Node.js $(node --version) / npm $(npm --version) instalado."

# ── 6. Configuración de Firewall (UFW) ─────────────────────────────────────
log_info "Configurando firewall (UFW)..."

ufw allow 5432/tcp
ufw --force enable

# SSH
ufw allow 22/tcp comment "SSH"

# Wazuh Agent communication
ufw allow 1514/tcp comment "Wazuh Agent events"
ufw allow 1515/tcp comment "Wazuh Agent registration"

# Wazuh API
ufw allow 55000/tcp comment "Wazuh API"

# Wazuh Indexer (OpenSearch)
ufw allow 9200/tcp comment "Wazuh Indexer (OpenSearch)"

# Wazuh Dashboard
ufw allow 443/tcp comment "Wazuh Dashboard (HTTPS)"

# PostgreSQL (para Power BI)
ufw allow 5432/tcp comment "PostgreSQL"

# FastAPI Backend
ufw allow 8000/tcp comment "FastAPI Backend"

# Next.js Dashboard
ufw allow 3000/tcp comment "Next.js Dashboard"

ufw reload
log_ok "Firewall configurado."

# ── 7. Resumen final ───────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ DESPLIEGUE COMPLETADO EXITOSAMENTE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}IP del Servidor:${NC}        ${PRIMARY_IP}"
echo ""
echo -e "  ${CYAN}── Wazuh ──${NC}"
echo -e "  Dashboard:              https://${PRIMARY_IP}:443"
echo -e "  API:                    https://${PRIMARY_IP}:55000"
echo -e "  Indexer (OpenSearch):   https://${PRIMARY_IP}:9200"
echo -e "  Contraseñas:            ${WAZUH_PASSWORDS_FILE:-'Ver wazuh-install-files.tar'}"
echo ""
echo -e "  ${CYAN}── PostgreSQL ──${NC}"
echo -e "  Base de datos:          ${DB_NAME}"
echo -e "  Usuario:                ${DB_USER}"
echo -e "  Contraseña:             ${DB_PASS}"
echo -e "  Puerto:                 5432"
echo ""
echo -e "  ${CYAN}── Servicios pendientes de despliegue ──${NC}"
echo -e "  FastAPI Backend:        http://${PRIMARY_IP}:8000"
echo -e "  Next.js Dashboard:      http://${PRIMARY_IP}:3000"
echo ""
echo -e "  ${YELLOW}⚠ IMPORTANTE: Guarde las credenciales de PostgreSQL.${NC}"
echo -e "  ${YELLOW}  Configure el archivo server/.env con estos valores.${NC}"
echo ""

# Guardar credenciales en archivo seguro
CREDS_FILE="/root/.netmonitor_credentials"
cat > "${CREDS_FILE}" << EOF
# Network Monitor - Credenciales del servidor
# Generadas: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
SERVER_IP=${PRIMARY_IP}
EOF
chmod 600 "${CREDS_FILE}"
log_ok "Credenciales guardadas en ${CREDS_FILE}"
