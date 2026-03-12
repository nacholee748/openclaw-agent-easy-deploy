# Política de Seguridad

## Reportar vulnerabilidades

Si encuentras una vulnerabilidad de seguridad en este proyecto, por favor **no la reportes como un issue público**.

En su lugar, envía un correo a los mantenedores del proyecto describiendo:
- Descripción de la vulnerabilidad
- Pasos para reproducirla
- Impacto potencial

## Archivos sensibles

Este proyecto maneja archivos que pueden contener información sensible. **Nunca deben subirse al repositorio:**

| Archivo | Contenido sensible |
|---------|-------------------|
| `*.pem` | Claves privadas SSH |
| `openclaw-config/openclaw.env` | API keys y tokens |
| `Pulumi.*.yaml` (excepto Pulumi.yaml) | IPs, profiles, encryption salts |
| `venv/` | Entorno virtual local |

El `.gitignore` está configurado para excluir estos archivos. **Verifica antes de cada commit** que no estés incluyendo información sensible:

```bash
git status
git diff --cached --name-only
```

## Buenas prácticas para usuarios

1. **API Keys**: Usa keys con permisos mínimos y límites de gasto
2. **SSH Keys**: Genera nuevas keys para cada despliegue, no reutilices keys personales
3. **Pulumi State**: Usa un backend remoto (Pulumi Cloud, S3) en lugar de local para equipos
4. **Rotación**: Rota API keys y tokens periódicamente
5. **Limpieza**: Ejecuta `pulumi destroy` cuando ya no necesites la infraestructura
