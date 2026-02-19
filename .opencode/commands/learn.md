---
description: Extract learnings from session to AGENTS.md
model: opencode/kimi-k2.5-free
---

Analiza esta sesión y extrae aprendizajes no obvios para agregar a archivos AGENTS.md.

Los archivos AGENTS.md pueden existir en cualquier nivel de directorio, no solo en la raíz del proyecto. Colocá los aprendizajes lo más cerca posible del código relevante.

Qué cuenta como aprendizaje (solo descubrimientos no obvios):

- Relaciones ocultas entre archivos o módulos
- Rutas de ejecución que difieren de cómo aparece el código
- Configuraciones no obvias, env vars, o flags
- Breakthroughs de debugging cuando los mensajes de error eran engañosos
- Quirks y workarounds de APIs/tools
- Comandos de build/test que no están en README
- Decisiones arquitectónicas y restricciones

Qué NO incluir:

- Hechos obvios de documentación
- Comportamiento estándar de lenguaje/framework
- Cosas ya en un AGENTS.md
- Explicaciones verbosas

Proceso:

1. Revisar sesión por descubrimientos, errores que tomaron múltiples intentos
2. Determinar alcance - a qué directorio aplica cada aprendizaje
3. Leer AGENTS.md existentes en niveles relevantes
4. Crear o actualizar AGENTS.md al nivel apropiado
5. Mantener entradas a 1-3 líneas por insight

$ARGUMENTS
