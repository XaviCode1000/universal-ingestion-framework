#!/usr/bin/env node
/**
 * Hook: SessionStart
 * Inicializa contexto UIF al iniciar sesión
 */

const fs = require('fs');
const path = require('path');

// Leer input desde stdin
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    try {
        const data = JSON.parse(input);
        const source = data.source || 'startup';
        
        // Mensaje de bienvenida
        console.error(`🚀 UIF-ARE iniciado (${source})`);
        
        // Contexto adicional
        const context = `
## 📋 Contexto UIF Cargado

- **Stack**: Python 3.12+, Pydantic V2, Polars Lazy, asyncio
- **Reglas**: frozen=True, slugify(), errores 500 chars
- **Comandos**: uv run, ruff check, mypy --strict

### Skills Activos:
- uif-expert: Patrones del framework
- python-strict: Validación de tipos

### Hooks Activos:
- block-secrets: Protección de secrets
- validate-python: Validación de código
- log-operations: Auditoría de operaciones
`;
        
        console.log(JSON.stringify({
            hookEventName: 'SessionStart',
            additionalContext: context,
            systemMessage: '🧠 UIF-ARE listo para trabajar'
        }));
        
    } catch (e) {
        console.error('Error en session-start:', e.message);
        console.log(JSON.stringify({}));
    }
});
