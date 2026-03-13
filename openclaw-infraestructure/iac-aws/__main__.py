"""
OpenClaw EC2 Deployment - Infraestructura con Pulumi (Python)

Este script crea la infraestructura necesaria para desplegar un agente OpenClaw
en una instancia EC2 m7i-flex.large (8GB RAM) dentro del Free Tier extendido de AWS
(cuentas creadas después del 15 de julio de 2025).
"""

import pulumi
import pulumi_aws as aws
import pulumi_tls as tls

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Leer configuración del stack
config = pulumi.Config()

# Tu IP pública para acceso SSH (requerido)
# Configurar con: pulumi config set myIp TU_IP
my_ip = config.require("myIp")

# Profile de AWS CLI a usar (opcional, default: "default")
# Configurar con: pulumi config set awsProfile NOMBRE_PROFILE
aws_profile = config.get("awsProfile") or "default"

# Región de AWS (opcional, default: us-east-1)
# Configurar con: pulumi config set awsRegion us-east-1
aws_region = config.get("awsRegion") or "us-east-1"

# =============================================================================
# PROVIDER DE AWS CON PROFILE ESPECÍFICO
# =============================================================================

# Crear provider de AWS usando el profile especificado
aws_provider = aws.Provider(
    "aws-provider",
    profile=aws_profile,
    region=aws_region,
)

# Opciones para usar este provider en todos los recursos
provider_opts = pulumi.ResourceOptions(provider=aws_provider)

# =============================================================================
# 1. KEY PAIR - Para acceso SSH a la instancia
# =============================================================================

# Generar clave privada RSA de 4096 bits
private_key = tls.PrivateKey(
    "openclaw-key",
    algorithm="RSA",
    rsa_bits=4096,
)

# Crear Key Pair en AWS usando la clave pública generada
key_pair = aws.ec2.KeyPair(
    "openclaw-key",
    key_name="openclaw-key",
    public_key=private_key.public_key_openssh,
    opts=provider_opts,
)

# =============================================================================
# 2. IAM ROLE - Permisos para la instancia EC2
# =============================================================================

# Trust policy: permite que EC2 asuma este rol
assume_role_policy = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            principals=[
                aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=["ec2.amazonaws.com"],
                )
            ],
            actions=["sts:AssumeRole"],
        )
    ]
)

# Crear el IAM Role
role = aws.iam.Role(
    "openclaw-ec2-role",
    name="openclaw-ec2-role",
    assume_role_policy=assume_role_policy.json,
    opts=provider_opts,
)

# Política de permisos: CloudWatch Logs + SSM (para Session Manager)
logs_policy = aws.iam.RolePolicy(
    "openclaw-logs-policy",
    role=role.id,
    policy=pulumi.Output.all().apply(lambda _: """{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }]
    }"""),
    opts=provider_opts,
)

# Política para SSM Session Manager (acceso por consola AWS)
ssm_policy = aws.iam.RolePolicyAttachment(
    "openclaw-ssm-policy",
    role=role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    opts=provider_opts,
)

# Instance Profile: contenedor del rol para asociar a EC2
instance_profile = aws.iam.InstanceProfile(
    "openclaw-ec2-profile",
    name="openclaw-ec2-profile",
    role=role.name,
    opts=provider_opts,
)


# =============================================================================
# 3. SECURITY GROUP - Firewall de red
# =============================================================================

security_group = aws.ec2.SecurityGroup(
    "openclaw-sg",
    name="openclaw-sg",
    description="Security group for OpenClaw agent",
    # Regla de entrada: SSH solo desde tu IP
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH from my IP",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=[f"{my_ip}/32"],
        )
    ],
    # Regla de salida: HTTPS para comunicarse con APIs de LLM y SSM
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            description="HTTPS outbound for APIs and SSM",
            from_port=443,
            to_port=443,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupEgressArgs(
            description="HTTP outbound for package updates",
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={"Name": "openclaw-sg"},
    opts=provider_opts,
)

# =============================================================================
# 4. AMI - Imagen de Ubuntu 22.04 LTS
# =============================================================================

# Buscar la AMI más reciente de Ubuntu 22.04 de Canonical
ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
)

# =============================================================================
# 5. USER DATA - Script de instalación de OpenClaw
# =============================================================================

# OpenClaw es un proyecto Node.js que requiere:
# - Node.js 22+
# - pnpm
# - ~8GB RAM para compilar (m7i-flex.large)

user_data = """#!/bin/bash
set -e
exec > >(tee /var/log/openclaw-install.log) 2>&1

echo "=========================================="
echo "  OpenClaw Installation - Starting"
echo "=========================================="

# Variables
OPENCLAW_USER="openclaw"
OPENCLAW_HOME="/home/${OPENCLAW_USER}"
OPENCLAW_DIR="${OPENCLAW_HOME}/openclaw"
NODE_VERSION="22"

# -----------------------------------------------------------------------------
# 1. Actualizar sistema
# -----------------------------------------------------------------------------
echo "[1/7] Actualizando sistema..."
apt-get update
apt-get upgrade -y

# -----------------------------------------------------------------------------
# 2. Instalar Node.js 22
# -----------------------------------------------------------------------------
echo "[2/7] Instalando Node.js ${NODE_VERSION}..."
curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
apt-get install -y nodejs git

# -----------------------------------------------------------------------------
# 3. Instalar pnpm
# -----------------------------------------------------------------------------
echo "[3/7] Instalando pnpm..."
npm install -g pnpm

# -----------------------------------------------------------------------------
# 4. Crear usuario openclaw
# -----------------------------------------------------------------------------
echo "[4/7] Creando usuario ${OPENCLAW_USER}..."
useradd -m -s /bin/bash ${OPENCLAW_USER} || true

# -----------------------------------------------------------------------------
# 5. Clonar e instalar OpenClaw
# -----------------------------------------------------------------------------
echo "[5/7] Clonando OpenClaw..."
su - ${OPENCLAW_USER} -c "git clone https://github.com/openclaw/openclaw.git ${OPENCLAW_DIR}"

echo "[5/7] Instalando dependencias (esto toma ~1 minuto)..."
su - ${OPENCLAW_USER} -c "cd ${OPENCLAW_DIR} && pnpm install"

echo "[5/7] Compilando OpenClaw..."
su - ${OPENCLAW_USER} -c "cd ${OPENCLAW_DIR} && pnpm build"

# -----------------------------------------------------------------------------
# 6. Crear configuración base
# -----------------------------------------------------------------------------
echo "[6/7] Creando configuración..."
CONFIG_DIR="${OPENCLAW_HOME}/.openclaw"
WORKSPACE_DIR="${CONFIG_DIR}/workspace"
SESSIONS_DIR="${CONFIG_DIR}/agents/main/sessions"
su - ${OPENCLAW_USER} -c "mkdir -p ${CONFIG_DIR} ${WORKSPACE_DIR} ${SESSIONS_DIR}"

GATEWAY_TOKEN=$(openssl rand -hex 32)
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

cat > ${CONFIG_DIR}/.env << EOF
# OpenClaw Configuration
OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN}

# API Keys - Descomenta y configura al menos una:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GEMINI_API_KEY=...
# OPENROUTER_API_KEY=sk-or-...

# Modelo por defecto
# OPENCLAW_DEFAULT_MODEL=gemini-2.0-flash
EOF

chown ${OPENCLAW_USER}:${OPENCLAW_USER} ${CONFIG_DIR}/.env
chmod 600 ${CONFIG_DIR}/.env

# Precargar openclaw.json (evita tener que ejecutar 'configure' manualmente)
cat > ${CONFIG_DIR}/openclaw.json << EOF
{
  "wizard": {
    "lastRunAt": "${CURRENT_DATE}",
    "lastRunVersion": "auto",
    "lastRunCommand": "configure",
    "lastRunMode": "local"
  },
  "auth": {
    "profiles": {
      "google:default": {
        "provider": "google",
        "mode": "api_key"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.0-flash"
      },
      "models": {
        "google/gemini-2.0-flash": {
          "alias": "gemini"
        }
      },
      "workspace": "${WORKSPACE_DIR}",
      "compaction": { "mode": "safeguard" },
      "maxConcurrent": 4,
      "subagents": { "maxConcurrent": 8 }
    }
  },
  "tools": {
    "web": {
      "search": { "enabled": true, "provider": "gemini" },
      "fetch": { "enabled": true }
    }
  },
  "messages": { "ackReactionScope": "group-mentions" },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true,
    "ownerDisplay": "raw"
  },
  "gateway": { "mode": "local" },
  "meta": {
    "lastTouchedVersion": "auto",
    "lastTouchedAt": "${CURRENT_DATE}"
  }
}
EOF

chown ${OPENCLAW_USER}:${OPENCLAW_USER} ${CONFIG_DIR}/openclaw.json
chmod 600 ${CONFIG_DIR}/openclaw.json

# -----------------------------------------------------------------------------
# 7. Crear servicio systemd
# -----------------------------------------------------------------------------
echo "[7/7] Creando servicio systemd..."

cat > /etc/systemd/system/openclaw.service << EOF
[Unit]
Description=OpenClaw AI Agent
After=network.target

[Service]
Type=simple
User=${OPENCLAW_USER}
WorkingDirectory=${OPENCLAW_DIR}
ExecStart=/usr/bin/node scripts/run-node.mjs gateway
Restart=always
RestartSec=10
Environment=NODE_ENV=production
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable openclaw

echo "=========================================="
echo "  OpenClaw Installation - Complete!"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo "1. Edita /home/${OPENCLAW_USER}/.openclaw/.env"
echo "2. Agrega tu API key (OpenAI, Anthropic, etc.)"
echo "3. Ejecuta: sudo systemctl start openclaw"
echo ""
"""

# =============================================================================
# 6. EC2 INSTANCE - La instancia donde corre OpenClaw
# =============================================================================

instance = aws.ec2.Instance(
    "openclaw-agent",
    ami=ubuntu_ami.id,
    instance_type="m7i-flex.large",  # Free Tier para cuentas nuevas (8GB RAM)
    key_name=key_pair.key_name,
    vpc_security_group_ids=[security_group.id],
    iam_instance_profile=instance_profile.name,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=30,  # GB - máximo Free Tier
        volume_type="gp3",
    ),
    user_data=user_data,
    tags={"Name": "openclaw-agent"},
    opts=provider_opts,
)

# =============================================================================
# 7. OUTPUTS - Valores de salida
# =============================================================================

# ID de la instancia
pulumi.export("instance_id", instance.id)

# IP pública para conectarse
pulumi.export("public_ip", instance.public_ip)

# Clave privada SSH (secreto)
pulumi.export("private_key_pem", pulumi.Output.secret(private_key.private_key_pem))

# Comando SSH listo para usar
pulumi.export(
    "ssh_command",
    instance.public_ip.apply(lambda ip: f"ssh -i openclaw-key.pem ubuntu@{ip}")
)

# Comando para guardar la clave privada
pulumi.export(
    "save_key_command",
    "pulumi stack output private_key_pem --show-secrets > openclaw-key.pem && chmod 400 openclaw-key.pem"
)

# Información de configuración usada
pulumi.export("aws_profile_used", aws_profile)
pulumi.export("aws_region_used", aws_region)
