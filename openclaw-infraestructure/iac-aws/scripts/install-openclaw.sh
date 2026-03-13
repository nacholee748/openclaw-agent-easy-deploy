#!/bin/bash
# =============================================================================
# OpenClaw Installation Script
# Este script instala y configura OpenClaw en una instancia EC2 Ubuntu
# =============================================================================

set -e

echo "=========================================="
echo "  OpenClaw Installation Script"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
OPENCLAW_USER="openclaw"
OPENCLAW_HOME="/home/${OPENCLAW_USER}"
OPENCLAW_DIR="${OPENCLAW_HOME}/openclaw"
NODE_VERSION="22"

# -----------------------------------------------------------------------------
# Funciones auxiliares
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root (usa sudo)"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# 1. Actualizar sistema
# -----------------------------------------------------------------------------

update_system() {
    log_info "Actualizando sistema..."
    apt-get update
    apt-get upgrade -y
}

# -----------------------------------------------------------------------------
# 2. Instalar Node.js 22
# -----------------------------------------------------------------------------

install_nodejs() {
    log_info "Instalando Node.js ${NODE_VERSION}..."
    
    if command -v node &> /dev/null; then
        CURRENT_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$CURRENT_VERSION" -ge "$NODE_VERSION" ]; then
            log_info "Node.js ${CURRENT_VERSION} ya instalado"
            return
        fi
    fi
    
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y nodejs
    
    log_info "Node.js $(node -v) instalado"
}

# -----------------------------------------------------------------------------
# 3. Instalar pnpm
# -----------------------------------------------------------------------------

install_pnpm() {
    log_info "Instalando pnpm..."
    
    if command -v pnpm &> /dev/null; then
        log_info "pnpm ya instalado"
        return
    fi
    
    npm install -g pnpm
    log_info "pnpm $(pnpm -v) instalado"
}

# -----------------------------------------------------------------------------
# 4. Crear usuario openclaw
# -----------------------------------------------------------------------------

create_user() {
    log_info "Creando usuario ${OPENCLAW_USER}..."
    
    if id "${OPENCLAW_USER}" &>/dev/null; then
        log_info "Usuario ${OPENCLAW_USER} ya existe"
        return
    fi
    
    useradd -m -s /bin/bash ${OPENCLAW_USER}
    log_info "Usuario ${OPENCLAW_USER} creado"
}

# -----------------------------------------------------------------------------
# 5. Clonar e instalar OpenClaw
# -----------------------------------------------------------------------------

install_openclaw() {
    log_info "Instalando OpenClaw..."
    
    if [ -d "${OPENCLAW_DIR}" ]; then
        log_info "OpenClaw ya clonado, actualizando..."
        su - ${OPENCLAW_USER} -c "cd ${OPENCLAW_DIR} && git pull"
    else
        log_info "Clonando repositorio OpenClaw..."
        su - ${OPENCLAW_USER} -c "git clone https://github.com/openclaw/openclaw.git ${OPENCLAW_DIR}"
    fi
    
    log_info "Instalando dependencias (esto puede tomar unos minutos)..."
    su - ${OPENCLAW_USER} -c "cd ${OPENCLAW_DIR} && pnpm install"
    
    log_info "Compilando OpenClaw..."
    su - ${OPENCLAW_USER} -c "cd ${OPENCLAW_DIR} && pnpm build"
    
    log_info "OpenClaw instalado correctamente"
}

# -----------------------------------------------------------------------------
# 6. Crear configuración base
# -----------------------------------------------------------------------------

create_config() {
    log_info "Creando configuración base..."
    
    CONFIG_DIR="${OPENCLAW_HOME}/.openclaw"
    ENV_FILE="${CONFIG_DIR}/.env"
    
    su - ${OPENCLAW_USER} -c "mkdir -p ${CONFIG_DIR}"
    
    if [ -f "${ENV_FILE}" ]; then
        log_warn "Archivo de configuración ya existe, no se sobrescribirá"
        return
    fi
    
    # Generar token aleatorio
    GATEWAY_TOKEN=$(openssl rand -hex 32)
    
    cat > ${ENV_FILE} << EOF
# =============================================================================
# OpenClaw Configuration
# =============================================================================

# Token de autenticación para el gateway (generado automáticamente)
OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN}

# -----------------------------------------------------------------------------
# API Keys - Descomenta y configura al menos una:
# -----------------------------------------------------------------------------

# OpenAI
# OPENAI_API_KEY=sk-...

# Anthropic (Claude)
# ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
# GEMINI_API_KEY=...

# OpenRouter (acceso a múltiples modelos)
# OPENROUTER_API_KEY=sk-or-...

# -----------------------------------------------------------------------------
# Modelo por defecto
# -----------------------------------------------------------------------------
# Ejemplos: gpt-4o, gpt-4o-mini, claude-3-5-sonnet, gemini-2.0-flash
# OPENCLAW_DEFAULT_MODEL=gemini-2.0-flash

# -----------------------------------------------------------------------------
# Configuración opcional
# -----------------------------------------------------------------------------

# Directorio de estado (default: ~/.openclaw)
# OPENCLAW_STATE_DIR=~/.openclaw

# Cargar variables de entorno del shell
# OPENCLAW_LOAD_SHELL_ENV=1
EOF

    chown ${OPENCLAW_USER}:${OPENCLAW_USER} ${ENV_FILE}
    chmod 600 ${ENV_FILE}
    
    log_info "Configuración creada en ${ENV_FILE}"
}

# -----------------------------------------------------------------------------
# 7. Crear servicio systemd
# -----------------------------------------------------------------------------

create_systemd_service() {
    log_info "Creando servicio systemd..."
    
    SERVICE_FILE="/etc/systemd/system/openclaw.service"
    
    cat > ${SERVICE_FILE} << EOF
[Unit]
Description=OpenClaw AI Agent
After=network.target

[Service]
Type=simple
User=${OPENCLAW_USER}
WorkingDirectory=${OPENCLAW_DIR}
ExecStart=/usr/bin/node scripts/run-node.mjs
Restart=always
RestartSec=10
Environment=NODE_ENV=production

# Límites de recursos
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable openclaw
    
    log_info "Servicio systemd creado y habilitado"
}

# -----------------------------------------------------------------------------
# 8. Mostrar instrucciones finales
# -----------------------------------------------------------------------------

show_instructions() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}  OpenClaw instalado correctamente!${NC}"
    echo "=========================================="
    echo ""
    echo "Próximos pasos:"
    echo ""
    echo "1. Configura tu API key:"
    echo "   sudo nano /home/${OPENCLAW_USER}/.openclaw/.env"
    echo ""
    echo "2. Descomenta y agrega tu API key (OpenAI, Anthropic, etc.)"
    echo ""
    echo "3. Inicia el servicio:"
    echo "   sudo systemctl start openclaw"
    echo ""
    echo "4. Verifica el estado:"
    echo "   sudo systemctl status openclaw"
    echo ""
    echo "5. Ver logs:"
    echo "   journalctl -u openclaw -f"
    echo ""
    echo "Para ejecutar manualmente:"
    echo "   sudo su - ${OPENCLAW_USER}"
    echo "   cd ~/openclaw && pnpm start"
    echo ""
    echo "=========================================="
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    check_root
    update_system
    install_nodejs
    install_pnpm
    create_user
    install_openclaw
    create_config
    create_systemd_service
    show_instructions
}

# Ejecutar
main "$@"
