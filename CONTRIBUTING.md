# Contribuir a OpenClaw Agent Easy Deploy

¡Gracias por tu interés en contribuir! Este proyecto busca hacer accesible el despliegue de OpenClaw para personas con conocimiento técnico básico.

## ¿Cómo contribuir?

### Reportar problemas

1. Verifica que el problema no haya sido reportado antes en [Issues](../../issues)
2. Crea un nuevo issue describiendo:
   - Qué intentaste hacer
   - Qué esperabas que pasara
   - Qué pasó realmente
   - Tu sistema operativo y versiones relevantes

### Agregar soporte para un proveedor cloud

1. Crea el directorio `openclaw-infraestructure/iac-<proveedor>/`
2. Implementa la IaC que cree:
   - Una VM con Ubuntu 22.04 (o equivalente)
   - Reglas de firewall (SSH entrada, HTTPS/HTTP salida)
   - User-data o script que instale OpenClaw automáticamente
3. Incluye un `README.md` con instrucciones paso a paso
4. Actualiza la tabla de opciones en el README principal

### Mejorar documentación

La documentación está en español. Si quieres mejorarla:
- Mantén un lenguaje sencillo y accesible
- Incluye ejemplos concretos
- Piensa en alguien que nunca ha usado la terminal

## Reglas

- **No incluyas secretos**: Nunca subas API keys, contraseñas, IPs reales o claves privadas
- **Usa el .gitignore**: Verifica que archivos sensibles estén excluidos antes de hacer commit
- **Prueba tus cambios**: Asegúrate de que los scripts y la IaC funcionan antes de enviar un PR
- **Documenta**: Todo cambio debe incluir documentación actualizada

## Estructura del proyecto

```
openclaw-agent-easy-deploy/
├── README.md                          # Guía principal
├── openclaw-config/                   # Configuración de OpenClaw
│   └── openclaw.env.example           # Template (solo este se versiona)
├── openclaw-infraestructure/          # Infraestructura
│   ├── docker/                        # Docker
│   └── iac-aws/                       # AWS (Pulumi + Python)
└── .kiro/specs/                       # Especificaciones del proyecto
```
