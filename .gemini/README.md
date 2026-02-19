# Configuración de Gemini CLI para UIF

Este documento describe la configuración óptima de Gemini CLI para el proyecto Universal Ingestion Framework.

---

## 📁 Estructura de Archivos

```
.gemini/
├── settings.json          # Configuración principal
├── GEMINI.md              # Contexto del proyecto
├── AGENTS.md              # Protocolo del agente
├── .env                   # Variables de entorno (no secrets)
├── .geminiignore          # Archivos ignorados
├── skills/
│   ├── uif-expert/
│   │   └── SKILL.md       # Skill de patrones UIF
│   └── python-strict/
│       └── SKILL.md       # Skill de validación Python
├── hooks/
│   ├── session-start.js   # Inicialización de sesión
│   ├── block-secrets.js   # Protección de secrets
│   ├── validate-python.js # Validación de código
│   ├── log-operations.js  # Auditoría de operaciones
│   ├── inject-context.js  # Inyección de contexto
│   └── validate-response.js # Validación de respuestas
└── logs/
    └── operations.jsonl   # Log de operaciones (auto-generado)
```

---

## ⚙️ Configuración Principal (settings.json)

### General
- **Editor**: VS Code (`code`)
- **Vim Mode**: Deshabilitado
- **Checkpointing**: Habilitado para recuperación de sesiones
- **Session Retention**: 30 días, máximo 50 sesiones

### UI
- **Tema**: GitHub
- **Auto Theme Switching**: Habilitado
- **Memory Usage**: Visible
- **Custom Phrases**: Frases personalizadas del proyecto

### Modelo
- **Default**: `gemini-2.5-pro`
- **Compression Threshold**: 0.5 (50% del contexto)
- **Custom Aliases**:
  - `uif-code`: Para desarrollo con thinking
  - `uif-fast`: Para respuestas rápidas

### Contexto
- **Archivos de contexto**: `AGENTS.md`, `GEMINI.md`
- **Directory Tree**: Incluido
- **Fuzzy Search**: Habilitado
- **Git Ignore**: Respetado

### Herramientas
- **Sandbox**: Deshabilitado (confianza en el proyecto)
- **Ripgrep**: Habilitado para búsquedas rápidas
- **Truncate Threshold**: 40,000 caracteres
- **Auto-approved**: Comandos uv, git, ruff, mypy, pytest

---

## 🪝 Hooks

### SessionStart
**Archivo**: `session-start.js`

Inicializa el contexto UIF al iniciar una sesión. Muestra mensaje de bienvenida y lista los skills y hooks activos.

### BeforeTool: block-secrets
**Archivo**: `block-secrets.js`

Bloquea la escritura de archivos que contengan:
- API keys
- Secrets
- Passwords
- Tokens
- Private keys
- Patrones conocidos (OpenAI, GitHub, Slack)

### BeforeTool: validate-python
**Archivo**: `validate-python.js`

Valida código Python antes de escribir:
- Type hints modernos (Python 3.12+)
- Modelos Pydantic con `frozen=True`
- Imports ordenados según Ruff
- Uso de `uv` en lugar de pip/poetry
- Sanitización de rutas con `slugify()`

### AfterTool: log-operations
**Archivo**: `log-operations.js`

Registra todas las operaciones en `.gemini/logs/operations.jsonl`:
- Timestamp
- Herramienta utilizada
- Archivo afectado
- Estado (éxito/error)

### BeforeAgent: inject-context
**Archivo**: `inject-context.js`

Inyecta contexto antes de cada interacción:
- Reglas obligatorias del stack
- Comandos rápidos
- Estado de Git (branch, status, commits recientes)

### AfterModel: validate-response
**Archivo**: `validate-response.js`

Valida las respuestas del modelo:
- Estructura UIF recomendada
- Idioma español (Rioplatense)

---

## 🎯 Skills

### uif-expert
**Ubicación**: `skills/uif-expert/SKILL.md`

Patrones avanzados del framework:
- Stack técnico obligatorio
- Patrones de diseño (Factory, Strategy)
- Ejemplos de código Pydantic, Polars, asyncio
- Comandos de verificación
- Checklist pre-commit

### python-strict
**Ubicación**: `skills/python-strict/SKILL.md`

Validación estricta de Python:
- Type hints Python 3.12+
- Compliance con `mypy --strict`
- Patrones de tipado (Callable, Protocol, TypeGuard)
- Errores comunes y soluciones

### exa-search
**Ubicación**: `skills/exa-search/SKILL.md`

Búsqueda web con Exa AI:
- Búsqueda de documentación y código
- Papers y artículos técnicos
- Ejemplos específicos para el stack UIF
- Patrones de uso por categoría

---

## 🔌 MCP Servers

### Exa AI Search
**Endpoint**: `https://mcp.exa.ai/mcp`

Herramientas disponibles:
- `web_search_exa`: Búsqueda web general
- `get_code_context_exa`: Búsqueda de código y documentación
- `company_research_exa`: Investigación de empresas
- `web_search_advanced_exa`: Búsqueda avanzada con filtros

**Configuración:**
```json
{
  "mcpServers": {
    "exa": {
      "httpUrl": "https://mcp.exa.ai/mcp"
    }
  }
}
```

> **Nota**: El servidor remoto no requiere API key para uso básico. Para uso avanzado, obtener key en [dashboard.exa.ai](https://dashboard.exa.ai/api-keys).

---

## 🚀 Uso

### Iniciar Gemini CLI
```bash
cd /path/to/universal-ingestion-framework
gemini
```

### Verificar configuración
```bash
# Ver settings efectivos
gemini --help

# Ver logs de operaciones
cat .gemini/logs/operations.jsonl | tail -10
```

### Comandos rápidos (auto-aprobados)
```bash
# Dentro de Gemini CLI, estos comandos no requieren confirmación:
uv run python script.py
uv add requests
uv sync
git status
git diff
ruff check .
mypy --strict src/
pytest tests/ -v
```

---

## 🔒 Seguridad

### Variables de Entorno
- **Redacción habilitada**: API_KEY, SECRET, PASSWORD, TOKEN, CREDENTIAL
- **Permitidas**: PATH, HOME, USER, SHELL, TERM, LANG

### Folder Trust
- Habilitado por defecto
- Requiere confirmación para operaciones en carpetas no confiables

### YOLO Mode
- Disponible pero no recomendado
- Deshabilitar con `security.disableYoloMode: true` si es necesario

---

## 📝 Personalización

### Agregar nuevo skill
1. Crear directorio: `.gemini/skills/mi-skill/`
2. Crear archivo: `SKILL.md` con frontmatter YAML
3. Reiniciar Gemini CLI

### Agregar nuevo hook
1. Crear archivo: `.gemini/hooks/mi-hook.js`
2. Agregar entrada en `settings.json` bajo el evento correspondiente
3. Hacer ejecutable: `chmod +x .gemini/hooks/mi-hook.js`
4. Reiniciar Gemini CLI

### Cambiar modelo
```json
{
  "model": {
    "name": "gemini-2.5-flash"
  }
}
```

---

## 🐛 Troubleshooting

### Los hooks no se ejecutan
```bash
# Verificar permisos
ls -la .gemini/hooks/

# Hacer ejecutables
chmod +x .gemini/hooks/*.js
```

### El contexto no se carga
```bash
# Verificar que AGENTS.md existe
ls -la AGENTS.md .gemini/GEMINI.md

# Verificar configuración de contexto
grep -A5 '"context"' .gemini/settings.json
```

### Los secrets se filtran
```bash
# Verificar que el hook está activo
grep "block-secrets" .gemini/settings.json

# Verificar redacción de env vars
grep -A5 '"environmentVariableRedaction"' .gemini/settings.json
```

---

## 📚 Referencias

- [Gemini CLI Documentation](https://geminicli.com/docs)
- [AGENTS.md](../AGENTS.md) - Protocolo completo del proyecto
- [GEMINI.md](GEMINI.md) - Contexto del proyecto
