#!/bin/bash
# install.sh - Script de inicialización (User Data) para la VM de Azure

# 1. Actualización básica del sistema
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y curl wget git jq software-properties-common apt-transport-https ca-certificates gnupg ufw

# 2. Configurar Firewall Base (UFW)
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8443/tcp
ufw allow 1514/tcp
ufw allow 1515/tcp
ufw allow 5432/tcp

# 3. Instalación de PostgreSQL
apt-get install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql

# Configurar acceso remoto para Postgres
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf
echo "host    all             all             0.0.0.0/0               md5" >> /etc/postgresql/*/main/pg_hba.conf
systemctl restart postgresql

# Crear base de datos y usuario de Sysmon
sudo -u postgres psql -c "CREATE DATABASE sysmon_db;"
sudo -u postgres psql -c "CREATE USER sysmon_user WITH ENCRYPTED PASSWORD 'Sysmon2026!*';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sysmon_db TO sysmon_user;"

# 4. Instalación de Node.js (v20) y PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g pm2

# 5. Instalación de Python 3 y Pip
apt-get install -y python3-pip python3-venv

# 6. Instalación de Nginx
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx

# 7. Despliegue de Wazuh Manager (Quickstart)
curl -sO https://packages.wazuh.com/4.9/wazuh-install.sh
curl -sO https://packages.wazuh.com/4.9/wazuh-install-files.tar
bash wazuh-install.sh -a

# 8. Marcar instalación completada (Útil para debuggear Terraform)
echo "Instalación completada exitosamente a las $(date)" > /var/log/sysmon_install.log
