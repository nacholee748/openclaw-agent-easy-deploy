# 🦞 OpenClaw Agent - Easy Deploy

Guía sencilla para instalar y ejecutar [OpenClaw](https://github.com/openclaw/openclaw), un agente de IA de código abierto, de forma segura y aprovechando capas gratuitas de servicios en la nube.

## ¿Qué es OpenClaw?

OpenClaw es un agente de IA que puede ejecutar tareas en tu sistema: leer y escribir archivos, ejecutar comandos, navegar la web e interactuar con modelos de lenguaje como GPT-4, Claude, Gemini, entre otros.

## ¿Por qué este proyecto?

Ejecutar un agente de IA en tu computadora personal puede ser riesgoso: tiene acceso a tus archivos, credenciales y datos personales. Este proyecto te ayuda a:

1. **Instalar OpenClaw de forma aislada** — en una máquina separada de tus datos personales
2. **Aprovechar capas gratuitas** — usar servicios cloud sin costo para probarlo
3. **Hacerlo fácil** — scripts automatizados para que no necesites ser experto

---

## ⚠️ Advertencias de Seguridad

OpenClaw puede ejecutar comandos, leer/escribir archivos y acceder a la red. **Úsalo con precaución.**

### 🚫 NO le des acceso a:

| Recurso | Riesgo |
|---------|--------|
| Credenciales de producción | Exposición de secretos |
| Bases de datos reales | Pérdida o corrupción de datos |
| Claves SSH/GPG privadas | Compromiso de identidad |
| Tokens de API con permisos amplios | Costos inesperados |
| Archivos con datos personales | Filtración de información |
| Acceso root/administrador | Control total del sistema |

### ✅ Buenas prácticas

- Ejecuta en un ambiente aislado (VM, contenedor, instancia cloud)
- Usa un usuario sin privilegios de administrador
- Crea API keys con permisos limitados y presupuesto definido
- Revisa los logs y la actividad del agente regularmente
- Ten respaldos antes de permitir escritura en archivos importantes

> 💡 Trata al agente como un desarrollador junior que necesita supervisión constante.

---

## Requisitos de OpenClaw

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| RAM | 4GB (con swap) | 8GB+ |
| CPU | 2 cores | 4 cores |
| Disco | 10GB | 20GB |
| Node.js | 22+ | 22 LTS |
| SO | Linux / macOS | Ubuntu 22.04 |

> ⚠️ La compilación requiere ~8GB de RAM. Si tu máquina tiene menos, necesitarás configurar swap o usar una instancia en la nube con suficiente memoria.

---

## Opciones de Despliegue

Elige la opción que mejor se adapte a tu situación:

| Opción | Costo | Ideal para | Estado |
|--------|-------|------------|--------|
| [☁️ AWS EC2](#️-aws-ec2) | Gratis (Free Tier) | Probar sin riesgo en la nube | ✅ Disponible |
| [☁️ Google Cloud](#️-google-cloud-gcp) | Gratis (Always Free) | Instancia permanente gratis | 🔜 Próximamente |
| [☁️ Azure](#️-microsoft-azure) | Gratis (12 meses) | Usuarios de ecosistema Microsoft | 🔜 Próximamente |
| [🐳 Docker](#-docker) | Gratis | Instalación local aislada | ✅ Disponible |

---

## ☁️ AWS EC2

**Ideal si**: Creaste tu cuenta AWS después del 15 de julio de 2025 y quieres una máquina con 8GB de RAM gratis.

### Capa Gratuita de AWS

| Tipo de cuenta | Instancias elegibles | RAM | Duración |
|----------------|---------------------|-----|----------|
| Nueva (post julio 2025) | t3.micro, t3.small, t4g.micro, t4g.small, c7i-flex.large, **m7i-flex.large** | Hasta 8GB | 6 meses + $200 créditos |
| Anterior (pre julio 2025) | t2.micro | 1GB | 12 meses |

> ⚠️ Las instancias con 1GB de RAM (t2.micro, e2-micro) **no son suficientes** para compilar OpenClaw. Necesitas al menos 4GB + swap, o idealmente 8GB.

### Despliegue automatizado

Usamos [Pulumi](https://www.pulumi.com/) (Python) para crear toda la infraestructura con un solo comando.

```bash
# 1. Clonar este repositorio
git clone https://github.com/nacholee748/openclaw-agent-easy-deploy.git
cd openclaw-agent-easy-deploy/openclaw-infraestructure/iac-aws

# 2. Configurar entorno
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configurar
pulumi stack init dev
pulumi config set myIp $(curl -s https://checkip.amazonaws.com)
pulumi config set awsProfile tu-profile

# 4. Desplegar (un solo comando)
aws sso login --profile tu-profile
AWS_PROFILE=tu-profile PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes

# 5. Guardar clave SSH (queda en openclaw-infraestructure/iac-aws/openclaw-key.pem)
pulumi stack output private_key_pem --show-secrets > openclaw-key.pem
chmod 400 openclaw-key.pem

# 6. Conectar a la instancia
ssh -i openclaw-key.pem ubuntu@$(pulumi stack output public_ip)
```

📖 Instrucciones detalladas en [openclaw-infraestructure/iac-aws/README.md](openclaw-infraestructure/iac-aws/README.md)

---

## 🔧 Configuración Inicial de OpenClaw

Una vez que tengas OpenClaw instalado (ya sea en AWS, Docker o local), sigue estos pasos para configurarlo.

### 1. Ejecutar el wizard de configuración

OpenClaw necesita una configuración inicial interactiva que crea el archivo `openclaw.json`:

```bash
# En la instancia o máquina donde está instalado:
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs configure"
```

El wizard te preguntará:

| Pregunta | Respuesta recomendada |
|----------|----------------------|
| Where will the Gateway run? | **Local (this machine)** |
| Select sections to configure | **Workspace** (primero), luego **Model** |
| Workspace directory | Dejar default: `~/.openclaw/workspace` |
| Model/auth provider | Según tu API key (Google, OpenAI, Anthropic) |
| Auth method | API key |
| API key | Usa la del `.env` o pégala directamente |

Cuando termine de pedir secciones, selecciona salir.

### 2. Iniciar el gateway

```bash
# Si usas systemd (AWS EC2)
sudo systemctl restart openclaw
sudo systemctl status openclaw

# Si ejecutas manualmente
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs gateway"
```

### 3. Usar OpenClaw

```bash
# Chat interactivo (TUI)
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs tui"

# Health check
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs health"

# Cambiar modelo
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs config set model google/gemini-2.0-flash"

# Diagnóstico
sudo su - openclaw -c "cd ~/openclaw && node scripts/run-node.mjs doctor"
```

### Archivos de configuración

| Archivo | Propósito |
|---------|-----------|
| `~/.openclaw/.env` | API keys y variables de entorno |
| `~/.openclaw/openclaw.json` | Config del gateway y modelo (generado por `configure`) |

> ⚠️ El `.env` solo no es suficiente. Debes ejecutar `configure` al menos una vez para generar `openclaw.json`.

---

## ☁️ Google Cloud (GCP)

**Ideal si**: Quieres una instancia gratuita permanente (no expira).

### Capa Gratuita de GCP

| Recurso | Especificación | Duración |
|---------|----------------|----------|
| VM | e2-micro (2 vCPU, 1GB RAM) | ✅ Siempre gratis |
| Disco | 30GB HDD estándar | ✅ Siempre gratis |
| Regiones | us-west1, us-central1, us-east1 | Solo estas regiones |
| Créditos | $300 USD para nuevos usuarios | 90 días |

> ⚠️ La instancia e2-micro (1GB RAM) no es suficiente para compilar OpenClaw directamente. Opciones:
> - Usar los $300 de crédito para una instancia más grande temporalmente
> - Compilar en otra máquina y copiar los binarios
> - Configurar swap de 4GB+ (rendimiento limitado)

🔜 Automatización con Pulumi próximamente en `iac/gcp/`

Referencia: [cloud.google.com/free](https://cloud.google.com/free)

---

## ☁️ Microsoft Azure

**Ideal si**: Ya usas servicios de Microsoft o tienes cuenta de estudiante.

### Capa Gratuita de Azure

| Recurso | Especificación | Duración |
|---------|----------------|----------|
| VM Linux | B1S (1 vCPU, 1GB RAM) | 12 meses, 750 hrs/mes |
| VM ARM | B2pts v2 (2 vCPU, 1GB RAM) | 12 meses, 750 hrs/mes |
| VM AMD | B2ats v2 (2 vCPU, 1GB RAM) | 12 meses, 750 hrs/mes |
| Disco | 2x 64GB SSD (P6) | 12 meses |
| Créditos | $200 USD para nuevos usuarios | 30 días |

> ⚠️ Las VMs gratuitas de Azure tienen solo 1GB de RAM. Mismas limitaciones que GCP para compilar OpenClaw. Usa los $200 de crédito para una instancia más grande o configura swap.

🔜 Automatización con Pulumi próximamente en `iac/azure/`

Referencia: [azure.microsoft.com/free](https://azure.microsoft.com/en-us/pricing/free-services)

---

## 🐳 Docker

**Ideal si**: Quieres ejecutar OpenClaw en tu máquina local de forma aislada, sin instalar nada directamente en tu sistema.

### Requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado
- Al menos 8GB de RAM disponibles para el contenedor

### Ejecutar

```bash
# 1. Clonar este repositorio
git clone https://github.com/nacholee748/openclaw-agent-easy-deploy.git
cd openclaw-agent-easy-deploy

# 2. Copiar y configurar tu archivo de entorno
cp openclaw-config/openclaw.env.example openclaw-config/openclaw.env
nano openclaw-config/openclaw.env  # Agrega tu API key

# 3. Construir y ejecutar
cd openclaw-infraestructure/docker
docker compose up -d

# 4. Ver logs
docker compose logs -f

# 5. Detener
docker compose down
```

---

## 🔑 Obtener API Keys para los Modelos de IA

OpenClaw necesita al menos una API key para funcionar. Aquí te explicamos cómo obtener cada una:

### OpenAI (GPT-4, GPT-4o)

1. Ve a [platform.openai.com](https://platform.openai.com/signup) y crea una cuenta
2. Navega a **API Keys** → [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
3. Click en **"Create new secret key"**
4. Copia la key (empieza con `sk-`)
5. **Importante**: Configura un límite de gasto en **Settings → Billing → Usage limits**

| Plan | Costo aproximado | Notas |
|------|-------------------|-------|
| GPT-4o | ~$2.50 / 1M tokens entrada | Modelo recomendado |
| GPT-4o-mini | ~$0.15 / 1M tokens entrada | Más económico |
| GPT-3.5-turbo | ~$0.50 / 1M tokens entrada | Básico |

### Anthropic (Claude 3, Claude 3.5)

1. Ve a [console.anthropic.com](https://console.anthropic.com/) y crea una cuenta
2. Navega a **API Keys** en el menú lateral
3. Click en **"Create Key"**
4. Copia la key (empieza con `sk-ant-`)
5. **Importante**: Configura límites en **Settings → Spend Limits**

| Plan | Costo aproximado | Notas |
|------|-------------------|-------|
| Claude 3.5 Sonnet | ~$3 / 1M tokens entrada | Mejor relación calidad/precio |
| Claude 3 Haiku | ~$0.25 / 1M tokens entrada | Más económico |
| Claude 3 Opus | ~$15 / 1M tokens entrada | Más capaz |

### Google Gemini

1. Ve a [aistudio.google.com](https://aistudio.google.com/apikey)
2. Inicia sesión con tu cuenta de Google
3. Click en **"Create API Key"**
4. Copia la key
5. **Nota**: Gemini tiene un plan gratuito con límites generosos

| Plan | Costo aproximado | Notas |
|------|-------------------|-------|
| Gemini 1.5 Flash | Gratis (con límites) | Ideal para empezar |
| Gemini 1.5 Pro | ~$1.25 / 1M tokens entrada | Más capaz |

### OpenRouter (Múltiples modelos)

1. Ve a [openrouter.ai](https://openrouter.ai/) y crea una cuenta
2. Navega a **Keys** → [openrouter.ai/keys](https://openrouter.ai/keys)
3. Click en **"Create Key"**
4. Copia la key (empieza con `sk-or-`)
5. **Ventaja**: Una sola key para acceder a GPT-4, Claude, Gemini, Llama, y más

| Ventaja | Detalle |
|---------|---------|
| Múltiples modelos | Accede a 100+ modelos con una sola key |
| Modelos gratuitos | Algunos modelos disponibles sin costo |
| Pago por uso | Solo pagas lo que consumes |

### 💡 Recomendación para empezar

Si es tu primera vez, te recomendamos:

1. **Google Gemini** — Tiene plan gratuito, ideal para probar sin gastar
2. **OpenRouter** — Acceso a modelos gratuitos y de pago con una sola key
3. **OpenAI** — El más popular, configura un límite de $5-10 USD para empezar

> ⚠️ **Siempre configura límites de gasto** en el dashboard del proveedor. Un agente de IA puede hacer muchas llamadas a la API y generar costos inesperados si no hay límites.

---

## Configuración

El archivo `openclaw-config/openclaw.env.example` contiene todas las opciones disponibles. Copia y edita:

```bash
cp openclaw-config/openclaw.env.example openclaw-config/openclaw.env
nano openclaw-config/openclaw.env
```

Configuración mínima — solo necesitas una línea:

```bash
OPENAI_API_KEY=sk-tu-key-aqui
```

Ver [openclaw-config/openclaw.env.example](openclaw-config/openclaw.env.example) para todas las opciones.

---

## Estructura del Proyecto

```
openclaw-agent-easy-deploy/
├── README.md                                    # Esta guía
├── CONTRIBUTING.md                              # Guía de contribución
├── SECURITY.md                                  # Política de seguridad
├── LICENSE                                      # Licencia MIT
├── .gitignore                                   # Archivos excluidos del repo
├── .editorconfig                                # Formato consistente
├── openclaw-config/                             # Configuración de OpenClaw
│   ├── openclaw.env.example                     # Template (se versiona)
│   └── openclaw.env                             # Tu config real (NO se versiona)
└── openclaw-infraestructure/                    # Infraestructura
    ├── docker/                                  # Despliegue con Docker
    │   ├── Dockerfile
    │   └── docker-compose.yml
    └── iac-aws/                                 # AWS con Pulumi (Python) ✅
        ├── __main__.py                          # Código de infraestructura
        ├── Pulumi.yaml                          # Config del proyecto
        ├── Pulumi.dev.yaml.example              # Ejemplo de config del stack
        ├── Pulumi.dev.yaml                      # Tu config del stack (NO se versiona)
        ├── requirements.txt                     # Dependencias Python
        ├── README.md                            # Instrucciones detalladas
        ├── openclaw-key.pem                     # Clave SSH (NO se versiona)
        └── scripts/
            └── install-openclaw.sh              # Script de instalación manual
```

> 📌 Los archivos marcados con "NO se versiona" están en `.gitignore` por seguridad.

---

## Solución de Problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| Error `ENOMEM` al compilar | RAM insuficiente | Agrega swap: `sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile` |
| `Node.js version error` | Versión < 22 | Instala Node.js 22+: `curl -fsSL https://deb.nodesource.com/setup_22.x \| sudo bash -` |
| API key inválida | Key expirada o incorrecta | Verifica en el dashboard del proveedor |
| OpenClaw no inicia | Falta API key | Edita `~/.openclaw/.env` y agrega al menos una key |
| Puerto en uso | Otro servicio en el puerto | Cambia `PORT` en `.env` |

---

## Contribuir

¿Quieres agregar soporte para otro proveedor cloud o mejorar la documentación?

1. Fork este repositorio
2. Crea tu branch: `git checkout -b feature/gcp-support`
3. Haz tus cambios
4. Envía un Pull Request

### Agregar un nuevo proveedor cloud

1. Crea el directorio `iac/<proveedor>/`
2. Implementa la IaC que cree una VM con Ubuntu 22.04
3. Incluye script de instalación de OpenClaw
4. Documenta en un README.md
5. Actualiza la tabla de opciones en este README
