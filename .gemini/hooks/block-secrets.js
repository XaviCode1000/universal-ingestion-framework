#!/usr/bin/env node
/**
 * Hook: BeforeTool (write_file, replace)
 * Bloquea escritura de secrets/API keys
 */

const fs = require('fs');

// Leer input desde stdin
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    try {
        const data = JSON.parse(input);
        const toolName = data.tool_name || '';
        const toolInput = data.tool_input || {};
        
        // Extraer contenido a verificar
        const content = toolInput.content || toolInput.new_string || '';
        
        // Patrones de secrets
        const secretPatterns = [
            /api[_-]?key\s*[=:]\s*['"][^'"]+['"]/gi,
            /secret[_-]?key\s*[=:]\s*['"][^'"]+['"]/gi,
            /password\s*[=:]\s*['"][^'"]+['"]/gi,
            /token\s*[=:]\s*['"][^'"]+['"]/gi,
            /credential\s*[=:]\s*['"][^'"]+['"]/gi,
            /private[_-]?key\s*[=:]\s*['"][^'"]+['"]/gi,
            /-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----/g,
            /sk-[a-zA-Z0-9]{20,}/g,  // OpenAI keys
            /ghp_[a-zA-Z0-9]{36}/g,  // GitHub tokens
            /xox[baprs]-[a-zA-Z0-9-]+/g,  // Slack tokens
        ];
        
        // Verificar cada patrón
        for (const pattern of secretPatterns) {
            const matches = content.match(pattern);
            if (matches && matches.length > 0) {
                console.error(`🚨 Secret detectado: ${pattern.source.substring(0, 30)}...`);
                console.log(JSON.stringify({
                    decision: 'deny',
                    reason: `🔒 SECURITY: Se detectó un posible secret/credential en el código. Por favor, usa variables de entorno en su lugar.\n\nPatrón detectado: ${matches[0].substring(0, 20)}...`,
                    systemMessage: '🚨 Bloqueado: posible secret detectado'
                }));
                process.exit(0);
            }
        }
        
        // No se encontraron secrets
        console.log(JSON.stringify({ decision: 'allow' }));
        
    } catch (e) {
        console.error('Error en block-secrets:', e.message);
        console.log(JSON.stringify({ decision: 'allow' }));
    }
});
