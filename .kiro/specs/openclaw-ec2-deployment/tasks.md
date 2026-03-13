# Implementation Plan: OpenClaw EC2 Deployment

## Overview

Implementación de infraestructura AWS usando Pulumi con Python para desplegar un agente OpenClaw en EC2. OpenClaw es un proyecto Node.js que requiere Node.js 22+ y ~8GB RAM para compilar, por lo que usamos `m7i-flex.large` (Free Tier para cuentas nuevas post julio 2025).

## Tasks

- [x] 1. Inicializar proyecto Pulumi (Python)
  - [x] 1.1 Crear estructura de directorios y archivos base del proyecto Pulumi
    - Crear directorio `openclaw-infra-py/`
    - Configurar `Pulumi.yaml` con nombre del proyecto
    - Crear `requirements.txt` con dependencias (pulumi, pulumi-aws, pulumi-tls)
    - _Requirements: 1.1, 4.1_

  - [x] 1.2 Configurar entorno virtual Python
    - Crear venv y activar
    - Instalar dependencias con pip
    - _Requirements: 1.1_

- [x] 2. Implementar generación de Key Pair
  - [x] 2.1 Crear recurso TLS Private Key y AWS Key Pair en `__main__.py`
    - Implementar `tls.PrivateKey` con algoritmo RSA 4096 bits
    - Implementar `aws.ec2.KeyPair` usando la clave pública generada
    - Nombre del key pair: "openclaw-key"
    - _Requirements: 1.1, 1.2_

- [x] 3. Implementar IAM Role e Instance Profile
  - [x] 3.1 Crear IAM Role con trust policy para EC2
    - Implementar `aws.iam.Role` con assume role policy para servicio EC2
    - Nombre del rol: "openclaw-ec2-role"
    - _Requirements: 2.1, 2.3_

  - [x] 3.2 Crear política de CloudWatch Logs
    - Implementar `aws.iam.RolePolicy` con permisos mínimos
    - Acciones permitidas: CreateLogGroup, CreateLogStream, PutLogEvents
    - _Requirements: 2.1, 2.5_

  - [x] 3.3 Agregar política SSM para Session Manager
    - Implementar `aws.iam.RolePolicyAttachment` con AmazonSSMManagedInstanceCore
    - Permite acceso a la instancia desde la consola AWS
    - _Requirements: 2.2_

  - [x] 3.4 Crear Instance Profile
    - Implementar `aws.iam.InstanceProfile` asociado al rol
    - Nombre: "openclaw-ec2-profile"
    - _Requirements: 2.4_

- [x] 4. Implementar Security Group
  - [x] 4.1 Crear Security Group con reglas de red
    - Implementar `aws.ec2.SecurityGroup` con nombre "openclaw-sg"
    - Regla ingress: SSH (puerto 22) desde IP configurada via `pulumi.Config`
    - Regla egress: HTTPS (puerto 443) hacia 0.0.0.0/0 para APIs y SSM
    - Regla egress: HTTP (puerto 80) hacia 0.0.0.0/0 para apt-get
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Implementar EC2 Instance
  - [x] 5.1 Obtener AMI de Ubuntu 22.04
    - Usar `aws.ec2.get_ami` para buscar Ubuntu 22.04 LTS de Canonical
    - Filtrar por nombre y tipo de virtualización HVM
    - _Requirements: 4.2_

  - [x] 5.2 Crear user-data script para instalación de OpenClaw
    - Script bash que actualiza sistema
    - Instala Node.js 22 desde NodeSource
    - Instala pnpm globalmente
    - Crea usuario `openclaw`
    - Clona repositorio OpenClaw
    - Ejecuta `pnpm install` y `pnpm build`
    - Crea archivo de configuración en `~/.openclaw/.env`
    - Crea servicio systemd (habilitado pero no iniciado)
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4_

  - [x] 5.3 Crear recurso EC2 Instance
    - Implementar `aws.ec2.Instance` tipo m7i-flex.large (8GB RAM)
    - Asociar Key Pair, Security Group e Instance Profile
    - Configurar volumen root: 30GB gp3
    - Incluir user-data script
    - Tag Name: "openclaw-agent"
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

- [x] 6. Implementar Outputs
  - [x] 6.1 Exportar outputs del stack
    - Export `instance_id`: ID de la instancia EC2
    - Export `public_ip`: IP pública de la instancia
    - Export `private_key_pem`: Clave privada SSH (secreto)
    - Export `ssh_command`: Comando SSH completo para conexión
    - Export `save_key_command`: Comando para guardar la clave privada
    - Export `aws_profile_used`: Profile de AWS usado
    - _Requirements: 1.2, 4.5, 5.1_

- [x] 7. Documentar comandos de operación
  - [x] 7.1 Crear README con instrucciones de uso
    - Documentar configuración de AWS profile
    - Documentar comando para configurar IP: `pulumi config set myIp`
    - Documentar comando de despliegue con variables de entorno
    - Documentar cómo guardar la clave privada
    - Documentar comando SSH de conexión
    - _Requirements: 3.5, 5.1_

  - [x] 7.2 Documentar comandos de limpieza
    - Documentar `pulumi destroy` para eliminar recursos
    - Documentar eliminación de archivo de clave local
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 7.3 Crear script de instalación standalone
    - Script `scripts/install-openclaw.sh` para instalación manual
    - Incluye verificaciones y mensajes de progreso
    - Puede usarse para reinstalar o actualizar OpenClaw
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 8. Desplegar infraestructura
  - [x] 8.1 Ejecutar `pulumi up` para crear recursos
    - Verificar creación de todos los recursos
    - Obtener IP pública de la instancia
    - _Requirements: 4.4, 4.5_

  - [x] 8.2 Verificar instalación de OpenClaw en la instancia
    - Conectar por SSH y verificar logs de instalación
    - Confirmar que Node.js, pnpm y OpenClaw están instalados
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

## Pending User Actions

- [ ] Configurar API key en `/home/openclaw/.openclaw/.env`
- [ ] Iniciar servicio: `sudo systemctl start openclaw`
- [ ] Verificar funcionamiento: `sudo systemctl status openclaw`

## Notes

- El proyecto usa Python como lenguaje de implementación con Pulumi
- La configuración del AWS profile se hace via variable de entorno `AWS_PROFILE`
- La clave privada SSH se exporta como output secreto y debe guardarse localmente
- OpenClaw es un proyecto Node.js (no Python) que requiere Node.js 22+ y ~8GB RAM
- El tipo de instancia m7i-flex.large está cubierto por Free Tier para cuentas nuevas (post julio 2025)
- El servicio systemd está habilitado pero NO iniciado - requiere configurar API key primero

## File Paths

- `openclaw-infraestructure/iac-aws/__main__.py` - Código Pulumi (infraestructura)
- `openclaw-infraestructure/iac-aws/scripts/install-openclaw.sh` - Script de instalación manual
- `openclaw-infraestructure/iac-aws/README.md` - Instrucciones detalladas de despliegue AWS
- `openclaw-config/openclaw.env.example` - Template de variables de entorno
- `openclaw-config/openclaw.json.example` - Template de config del gateway
