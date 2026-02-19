#!/usr/bin/env node
/**
 * Hook: AfterTool (*)
 * Log de operaciones para auditoría
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Leer input desde stdin
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    try {
        const data = JSON.parse(input);
        const toolName = data.tool_name || 'unknown';
        const toolInput = data.tool_input || {};
        const toolResponse = data.tool_response || {};
        
        // Crear directorio de logs si no existe
        const logDir = path.join(process.env.GEMINI_PROJECT_DIR || process.cwd(), '.gemini', 'logs');
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
        
        // Archivo de log
        const logFile = path.join(logDir, 'operations.jsonl');
        
        // Crear entrada de log
        const logEntry = {
            timestamp: new Date().toISOString(),
            tool: toolName,
            file: toolInput.file_path || toolInput.path || null,
            success: !toolResponse.error,
            error: toolResponse.error ? String(toolResponse.error).substring(0, 200) : null
        };
        
        // Escribir log
        fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
        
        // Log en stderr para debugging
        const status = logEntry.success ? '✅' : '❌';
        console.error(`${status} ${toolName}${logEntry.file ? ': ' + path.basename(logEntry.file) : ''}`);
        
        // Continuar normalmente
        console.log(JSON.stringify({}));
        
    } catch (e) {
        console.error('Error en log-operations:', e.message);
        console.log(JSON.stringify({}));
    }
});
