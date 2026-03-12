# Requirements Document

## Introduction

Este documento define los requisitos para el despliegue de un agente OpenClaw en una instancia EC2 de AWS. El objetivo es establecer una infraestructura mínima y segura que permita ejecutar el agente dentro del Free Tier de AWS (extendido para cuentas nuevas creadas después de julio 2025).

## Glossary

- **EC2_Instance**: Instancia de Amazon Elastic Compute Cloud que ejecuta el agente OpenClaw
- **Security_Group**: Firewall virtual que controla el tráfico de red hacia y desde la instancia EC2
- **IAM_Role**: Rol de AWS Identity and Access Management que define los permisos de la instancia
- **Key_Pair**: Par de claves criptográficas para autenticación SSH
- **OpenClaw_Agent**: Aplicación de agente de IA basada en Node.js que se ejecuta en la instancia EC2
- **Instance_Profile**: Contenedor de IAM Role que permite asociar permisos a una instancia EC2
- **SSM_Session_Manager**: Servicio de AWS que permite acceso a instancias EC2 desde la consola AWS sin SSH

## Requirements

### Requirement 1: Gestión de Key Pair

**User Story:** Como administrador, quiero crear un par de claves SSH, para poder acceder de forma segura a la instancia EC2.

#### Acceptance Criteria

1. WHEN el usuario ejecuta el comando de creación de Key Pair, THE Sistema SHALL generar un par de claves con nombre "openclaw-key"
2. WHEN el Key Pair es creado, THE Sistema SHALL guardar la clave privada en un archivo local con permisos 400
3. IF el Key Pair ya existe con el mismo nombre, THEN THE Sistema SHALL reportar un error descriptivo

### Requirement 2: Configuración de IAM Role

**User Story:** Como administrador, quiero configurar un IAM Role con permisos mínimos, para que la instancia EC2 pueda escribir logs en CloudWatch y ser accesible via SSM.

#### Acceptance Criteria

1. THE IAM_Role SHALL incluir permisos para CloudWatch Logs (CreateLogGroup, CreateLogStream, PutLogEvents)
2. THE IAM_Role SHALL incluir la política AmazonSSMManagedInstanceCore para acceso via Session Manager
3. WHEN el IAM Role es creado, THE Sistema SHALL configurar una trust policy que permita a EC2 asumir el rol
4. WHEN el IAM Role es creado, THE Sistema SHALL crear un Instance Profile asociado
5. THE IAM_Role SHALL seguir el principio de mínimo privilegio

### Requirement 3: Configuración de Security Group

**User Story:** Como administrador, quiero configurar un Security Group restrictivo, para proteger la instancia EC2 de accesos no autorizados.

#### Acceptance Criteria

1. WHEN el Security Group es creado, THE Security_Group SHALL permitir tráfico SSH entrante (puerto 22) únicamente desde la IP del administrador
2. THE Security_Group SHALL permitir tráfico HTTPS saliente (puerto 443) hacia cualquier destino para comunicación con APIs y SSM
3. THE Security_Group SHALL permitir tráfico HTTP saliente (puerto 80) para actualizaciones de paquetes (apt-get)
4. THE Security_Group SHALL denegar todo otro tráfico por defecto
5. IF la IP del administrador cambia, THEN THE Sistema SHALL permitir actualizar la regla de ingreso SSH

### Requirement 4: Aprovisionamiento de Instancia EC2

**User Story:** Como administrador, quiero lanzar una instancia EC2 con la configuración correcta, para ejecutar el agente OpenClaw.

#### Acceptance Criteria

1. THE EC2_Instance SHALL ser de tipo m7i-flex.large (8GB RAM) para cuentas nuevas dentro del Free Tier extendido
2. THE EC2_Instance SHALL usar Ubuntu 22.04 LTS como sistema operativo
3. THE EC2_Instance SHALL tener un volumen EBS de 30GB tipo gp3
4. WHEN la instancia es lanzada, THE EC2_Instance SHALL asociarse con el Security Group y IAM Role creados previamente
5. WHEN la instancia está en estado "running", THE Sistema SHALL proporcionar la IP pública para conexión SSH
6. THE EC2_Instance SHALL tener un tag "Name" con valor "openclaw-agent"

### Requirement 5: Instalación del Agente OpenClaw

**User Story:** Como administrador, quiero instalar y configurar el agente OpenClaw, para que esté operativo en la instancia EC2.

#### Acceptance Criteria

1. WHEN el usuario se conecta por SSH, THE Sistema SHALL permitir acceso usando la clave privada generada
2. THE Sistema SHALL instalar Node.js versión 22 o superior (requerido por OpenClaw)
3. THE Sistema SHALL instalar pnpm como gestor de paquetes
4. THE OpenClaw_Agent SHALL clonarse desde el repositorio oficial de GitHub
5. THE Sistema SHALL ejecutar `pnpm install` y `pnpm build` para compilar OpenClaw
6. WHEN el agente es configurado, THE Sistema SHALL crear archivo de configuración en `~/.openclaw/.env`
7. THE Sistema SHALL requerir la configuración de al menos una API key (OpenAI, Anthropic, etc.)
8. WHEN el agente es iniciado, THE OpenClaw_Agent SHALL poder comunicarse con APIs externas vía HTTPS

### Requirement 6: Configuración como Servicio

**User Story:** Como administrador, quiero configurar el agente como servicio systemd, para que se inicie automáticamente con el sistema.

#### Acceptance Criteria

1. THE Sistema SHALL crear un archivo de unidad systemd para OpenClaw
2. THE OpenClaw_Agent SHALL reiniciarse automáticamente si falla (RestartSec=10)
3. THE Sistema SHALL habilitar el servicio para inicio automático al arrancar la instancia
4. THE Sistema SHALL NO iniciar el servicio automáticamente hasta que se configure una API key

### Requirement 7: Limpieza de Recursos

**User Story:** Como administrador, quiero poder eliminar todos los recursos creados, para evitar costos innecesarios cuando ya no necesite el agente.

#### Acceptance Criteria

1. WHEN el usuario ejecuta `pulumi destroy`, THE Sistema SHALL terminar la instancia EC2
2. WHEN la instancia EC2 está terminada, THE Sistema SHALL eliminar el Security Group
3. THE Sistema SHALL eliminar el Key Pair y el archivo de clave privada local
4. THE Sistema SHALL eliminar el IAM Role y el Instance Profile asociado
5. WHEN todos los recursos son eliminados, THE Sistema SHALL no dejar recursos huérfanos en la cuenta AWS
