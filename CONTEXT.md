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
- Instancia EC2 `m7i-flex.large` (8GB RAM) creada y funcionando
- Instance ID: `i-0878b43a7b96ae9c0`
- Región: `us-east-1`
- Usuario SSH: `ubuntu`
- Repo OpenClaw clonado en la instancia en `/home/openclaw/openclaw`
- Servicio systemd `openclaw.service` creado y habilitado
- Documentación completa (README, SECURITY, CONTRIBUTING, LICENSE)
- `.gitignore` configurado (excluye .pem, .env, Pulumi.dev.yaml, venv, __pycache__)
- Docker (Dockerfile + docker-compose.yml) listos

### ⏸️ Pendiente (retomar aquí)

1. **Instalar Node.js 22 en la instancia** — El user-data falló porque tenía un bug (intentó `pip install` en vez de instalar Node.js). Ejecutar en la instancia:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
   sudo apt-get install -y nodejs
   sudo npm install -g pnpm
   sudo su - openclaw -c "cd ~/openclaw && pnpm install && pnpm build"
   ```

2. **Configurar API key** — Editar `/home/openclaw/.openclaw/.env` y agregar al menos una key

3. **Iniciar OpenClaw** — `sudo systemctl start openclaw`

4. **Corregir user-data en `__main__.py`** — El script de user-data tiene el bug del `requirements.txt`. Hay que actualizarlo para que futuros despliegues funcionen sin intervención manual.

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

### Pulumi (desde openclaw-infraestructure/iac-aws/)

```bash
source venv/bin/activate
AWS_PROFILE=nacholee PULUMI_CONFIG_PASSPHRASE="" pulumi stack select dev
AWS_PROFILE=nacholee PULUMI_CONFIG_PASSPHRASE="" pulumi up
```

### Detener instancia

```bash
AWS_PROFILE=nacholee aws ec2 stop-instances --instance-ids i-0878b43a7b96ae9c0
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
- El servicio systemd está habilitado pero NO iniciado (necesita API key)
