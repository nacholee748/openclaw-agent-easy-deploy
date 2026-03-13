# ☁️ OpenClaw en AWS EC2

Infraestructura como Código con [Pulumi](https://www.pulumi.com/) (Python) para desplegar OpenClaw en una instancia EC2 de AWS.

## ⚠️ Sobre la Capa Gratuita

Este proyecto usa `m7i-flex.large` (8GB RAM), elegible para Free Tier **solo en cuentas creadas después del 15 de julio de 2025**.

| Recurso | Especificación | Free Tier |
|---------|----------------|-----------|
| EC2 | m7i-flex.large (2 vCPU, 8GB RAM) | 750 hrs/mes por 6 meses |
| EBS | 30GB gp3 | Incluido |
| Transferencia | Salida a internet | 100GB/mes |

Para cuentas anteriores a julio 2025, el Free Tier solo cubre `t2.micro` (1GB RAM), que es insuficiente para OpenClaw.

Referencia: [aws.amazon.com/free](https://aws.amazon.com/free) | [Documentación EC2 Free Tier](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                       AWS Cloud                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Security Group (openclaw-sg)                 │ │
│  │  Inbound:  SSH (22) ← Tu IP                            │ │
│  │  Outbound: HTTPS (443), HTTP (80)                      │ │
│  │                                                         │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │       EC2 m7i-flex.large (8GB RAM)               │  │ │
│  │  │                                                  │  │ │
│  │  │  Ubuntu 22.04 + Node.js 22 + OpenClaw            │  │ │
│  │  │  Usuario: openclaw (sin sudo)                    │  │ │
│  │  │  Servicio: systemd                               │  │ │
│  │  │                                                  │  │ │
│  │  │  IAM Role: CloudWatch Logs + SSM                 │  │ │
│  │  │  Volumen: 30GB gp3                               │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                              │
    SSH (Key Pair)              SSM Session Manager
         ▼                              ▼
    Tu Terminal                    AWS Console
```

## Prerrequisitos

- [Pulumi CLI](https://www.pulumi.com/docs/install/)
- [AWS CLI](https://aws.amazon.com/cli/) configurado
- Python 3.8+
- Cuenta AWS con Free Tier disponible

## Despliegue Paso a Paso

### 1. Preparar entorno

```bash
cd openclaw-infraestructure/iac-aws
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar

```bash
# Crear stack
pulumi stack init dev

# Tu IP pública para acceso SSH
pulumi config set myIp $(curl -s https://checkip.amazonaws.com)

# Tu profile de AWS CLI
pulumi config set awsProfile tu-profile
```

### 3. Desplegar

```bash
# Autenticarse (si usas SSO)
aws sso login --profile tu-profile

# Crear infraestructura
AWS_PROFILE=tu-profile PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes
```

El despliegue toma ~10 minutos (incluye compilación de OpenClaw).

### 4. Conectar

```bash
# Guardar clave SSH (se guarda en esta misma carpeta, excluida del repo por .gitignore)
pulumi stack output private_key_pem --show-secrets > openclaw-key.pem
chmod 400 openclaw-key.pem

# Conectar a la instancia
ssh -i openclaw-key.pem ubuntu@$(pulumi stack output public_ip)
```

También puedes conectarte desde la consola AWS usando **Session Manager** (EC2 → Instances → Connect).

### 5. Configurar OpenClaw

```bash
# Ejecutar wizard de configuración (crea openclaw.json)
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs configure"

# Seleccionar:
# - Gateway: Local (this machine)
# - Sections: Workspace, luego Model
# - Provider: Google (o el de tu API key)
# - Auth: API key
# - Usa la key del .env

# Reiniciar servicio
sudo systemctl restart openclaw
sudo systemctl status openclaw
```

### 6. Usar OpenClaw

```bash
# Chat interactivo
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs tui"

# Health check
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs health"
```

## Limpieza

```bash
AWS_PROFILE=tu-profile PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes
rm openclaw-key.pem
```

## Variables de Configuración

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `myIp` | Sí | — | Tu IP pública para acceso SSH |
| `awsProfile` | No | `default` | Profile de AWS CLI |
| `awsRegion` | No | `us-east-1` | Región de AWS |

## Recursos Creados

| Recurso | Nombre | Descripción |
|---------|--------|-------------|
| Key Pair | openclaw-key | Acceso SSH |
| IAM Role | openclaw-ec2-role | CloudWatch + SSM |
| Security Group | openclaw-sg | Firewall |
| EC2 Instance | openclaw-agent | Servidor con OpenClaw |

## Estructura

```
openclaw-infraestructure/iac-aws/
├── __main__.py                  # Código Pulumi (infraestructura)
├── Pulumi.yaml                  # Config del proyecto
├── Pulumi.dev.yaml.example      # Ejemplo de config del stack
├── Pulumi.dev.yaml              # Tu config (NO se versiona)
├── requirements.txt             # Dependencias Python
├── README.md                    # Este archivo
├── openclaw-key.pem             # Clave SSH (NO se versiona)
└── scripts/
    └── install-openclaw.sh      # Script de instalación manual
```

> 📌 `openclaw-key.pem` y `Pulumi.dev.yaml` están en `.gitignore` por seguridad.
