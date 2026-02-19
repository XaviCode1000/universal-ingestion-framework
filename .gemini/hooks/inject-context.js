#!/usr/bin/env node
/**
 * Hook: BeforeAgent
 * Inyecta contexto del stack UIF
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Leer input desde stdin
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    try {
        const data = JSON.parse(input);
        
        // Obtener contexto del proyecto
        let gitContext = '';
        try {
            const branch = execSync('git branch --show-current 2>/dev/null', { encoding: 'utf8' }).trim();
            const status = execSync('git status --short 2>/dev/null', { encoding: 'utf8' }).trim();
            const recentCommits = execSync('git log -3 --oneline 2>/dev/null', { encoding: 'utf8' }).trim();
            
            gitContext = `
### Git Context
- **Branch**: ${branch || 'unknown'}
- **Status**: ${status || 'clean'}
- **Recent commits**:
${recentCommits.split('\n').map(c => '  - ' + c).join('\n')}
`;
        } catch (e) {
            gitContext = '\n### Git Context\n- No disponible\n';
        }
        
        // Contexto del stack UIF
        const uifContext = `
## 🏗️ UIF Stack Context

### Reglas Obligatorias
1. **Pydantic V2**: \`model_config = {"frozen": True}\` en todos los modelos
2. **Seguridad**: Usar \`slugify()\` para sanitizar rutas
3. **Logs**: Truncar errores a 500 caracteres
4. **Imports**: Orden stdlib → third-party → local (Ruff)
5. **Type Hints**: Sintaxis Python 3.12+ (\`list[str]\`, \`dict[str, Any]\`)

### Comandos Rápidos
\`\`\`bash
uv run python script.py  # Ejecutar
uv run ruff check .      # Linting
uv run mypy --strict src/ # Type check
uv run pytest tests/ -v  # Tests
\`\`\`

${gitContext}

### Recordatorios
- Responder SIEMPRE en español (Rioplatense con voseo)
- Usar Polars Lazy API para datasets grandes
- Usar asyncio.TaskGroups para concurrencia
- Verificar que el código pase \`mypy --strict\`
`;
        
        console.log(JSON.stringify({
            hookEventName: 'BeforeAgent',
            additionalContext: uifContext
        }));
        
    } catch (e) {
        console.error('Error en inject-context:', e.message);
        console.log(JSON.stringify({}));
    }
});
