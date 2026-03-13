# Contexto del Proyecto - OpenClaw Agent Easy Deploy

> Este archivo sirve para retomar el trabajo desde cualquier PC. Léelo al inicio de cada sesión.

## Repositorio

- GitHub: https://github.com/nacholee748/openclaw-agent-easy-deploy.git
- Branch: `main`
- SSH key de GitHub: `~/.ssh/github_nacholee748_ed25519`
- Git user: `nacholee748`

## Estado Actual

### ✅ Completado

- Infraestructura AWS desplegada con Pulumi (Python)
- Instancia EC2 `m7i-flex.large` (8GB RAM) creada
- Instance ID: `i-0878b43a7b96ae9c0`
- Región: `us-east-1`
- Node.js 22, pnpm y OpenClaw instalados y compilados
- OpenClaw configurado con Gemini API key
- Gateway corriendo como servicio systemd en `ws://127.0.0.1:18789`
- Modelo configurado: `google/gemini-3.1-pro-preview`
- TUI probado y funcionando (rate limit de Gemini free tier)
- Documentación completa (README, SECURITY, CONTRIBUTING, LICENSE)
- Docker (Dockerfile + docker-compose.yml) listos
- `.gitignore` configurado

### ⏸️ Pendiente

- Probar con modelo `gemini-2.0-flash` (límites más generosos en free tier)
- Considerar OpenRouter como alternativa (modelos gratuitos disponibles)
- Actualizar user-data en `__main__.py` para que futuros despliegues no requieran intervención manual (el actual tiene bugs del primer deploy)

## Configuración de OpenClaw - Lo que aprendimos

### Archivos de configuración en la instancia

| Archivo | Propósito |
|---------|-----------|
| `/home/openclaw/.openclaw/.env` | API keys y variables de entorno |
| `/home/openclaw/.openclaw/openclaw.json` | Config principal (generada por `configure`) |
| `/etc/systemd/system/openclaw.service` | Servicio systemd |

### Proceso de configuración inicial

1. Ejecutar el wizard interactivo (crea `openclaw.json`):
   ```bash
   sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs configure"
   ```
   Opciones seleccionadas:
   - Gateway: **Local (this machine)**
   - Workspace: `~/.openclaw/workspace`
   - Model/auth provider: **Google**
   - Auth method: **Google Gemini API key**
   - Usa la `GEMINI_API_KEY` del `.env`

2. El servicio systemd debe ejecutar `gateway` (no solo `run-node.mjs`):
   ```
   ExecStart=/usr/bin/node scripts/run-node.mjs gateway
   ```

3. Iniciar servicio:
   ```bash
   sudo systemctl restart openclaw
   ```

### Cómo usar OpenClaw

```bash
# TUI (chat interactivo en terminal)
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs tui"

# Health check
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs health"

# Ver modelos disponibles
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs models --help"

# Cambiar modelo default
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs config set model google/gemini-2.0-flash"

# Ver logs
journalctl -u openclaw -f
cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

### Subcomandos principales de OpenClaw CLI

| Comando | Descripción |
|---------|-------------|
| `gateway` | Inicia el WebSocket Gateway (lo que corre como servicio) |
| `configure` | Wizard interactivo de configuración |
| `tui` | Chat interactivo en terminal |
| `agent --message "..."` | Enviar mensaje al agente |
| `health` | Health check del gateway |
| `models` | Gestionar modelos |
| `config set <key> <value>` | Cambiar configuración |
| `status` | Estado de canales y sesiones |
| `doctor` | Diagnóstico y fixes rápidos |

## Comandos Frecuentes

### Iniciar la instancia (está detenida para ahorrar recursos)

```bash
AWS_PROFILE=nacholee aws ec2 start-instances --instance-ids i-0878b43a7b96ae9c0
```

### Obtener IP pública (cambia cada vez que se inicia)

```bash
AWS_PROFILE=nacholee aws ec2 describe-instances \
  --instance-ids i-0878b43a7b96ae9c0 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

### Conectar por SSH

```bash
ssh -i openclaw-infraestructure/iac-aws/openclaw-key.pem ubuntu@<IP_PUBLICA>
```

### Detener instancia

```bash
AWS_PROFILE=nacholee aws ec2 stop-instances --instance-ids i-0878b43a7b96ae9c0
```

### Pulumi (desde openclaw-infraestructure/iac-aws/)

```bash
source venv/bin/activate
AWS_PROFILE=nacholee PULUMI_CONFIG_PASSPHRASE="" pulumi stack select dev
AWS_PROFILE=nacholee PULUMI_CONFIG_PASSPHRASE="" pulumi up
```

### Destruir todo

```bash
cd openclaw-infraestructure/iac-aws
AWS_PROFILE=nacholee PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes
```

## Configuración AWS

- Profile: `nacholee` (SSO)
- Login: `aws sso login --profile nacholee`
- Región: `us-east-1`
- Cuenta creada: Feb 2026 (Free Tier extendido, incluye m7i-flex.large)

## Estructura del Proyecto

```
openclaw-agent-easy-deploy/
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
├── CONTEXT.md                          ← Este archivo
├── .gitignore
├── .editorconfig
├── openclaw-config/
│   ├── openclaw.env.example            # Template (versionado)
│   └── openclaw.env                    # Config real (NO versionado)
├── openclaw-infraestructure/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── iac-aws/
│       ├── __main__.py                 # Código Pulumi
│       ├── Pulumi.yaml
│       ├── Pulumi.dev.yaml.example
│       ├── Pulumi.dev.yaml             # NO versionado
│       ├── requirements.txt
│       ├── README.md
│       ├── openclaw-key.pem            # NO versionado
│       └── scripts/
│           └── install-openclaw.sh
└── .kiro/specs/openclaw-ec2-deployment/
    ├── design.md
    ├── requirements.md
    └── tasks.md
```

## Notas Importantes

- La IP pública cambia cada vez que se inicia la instancia
- `openclaw-key.pem` se genera con: `pulumi stack output private_key_pem --show-secrets > openclaw-key.pem`
- El usuario `openclaw` en la instancia NO tiene sudo (por seguridad)
- OpenClaw usa `openclaw.json` como config principal (generado por `configure`), NO solo el `.env`
- El `.env` es para API keys y variables de entorno, el `openclaw.json` es para la config del gateway/modelo
- Gemini free tier tiene rate limits estrictos; `gemini-2.0-flash` tiene límites más generosos
- El gateway escucha en `ws://127.0.0.1:18789` (solo localhost)
