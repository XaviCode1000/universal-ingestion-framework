#!/usr/bin/env node
/**
 * Hook: BeforeTool (write_file *.py)
 * Valida código Python antes de escribir
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
        const filePath = toolInput.file_path || '';
        const content = toolInput.content || '';
        
        // Solo validar archivos Python
        if (!filePath.endsWith('.py')) {
            console.log(JSON.stringify({ decision: 'allow' }));
            return;
        }
        
        const warnings = [];
        
        // Verificar type hints legacy
        if (content.includes('from typing import List') || 
            content.includes('from typing import Dict') ||
            content.includes('from typing import Set') ||
            content.includes('from typing import Tuple')) {
            warnings.push('⚠️ Usa type hints modernos: list[], dict[], set[], tuple[] (Python 3.12+)');
        }
        
        // Verificar Union/Optional legacy
        if (content.includes('Union[') || content.includes('Optional[')) {
            warnings.push('⚠️ Usa | en lugar de Union/Optional (Python 3.10+)');
        }
        
        // Verificar BaseModel sin frozen
        if (content.includes('class ') && content.includes('BaseModel')) {
            if (!content.includes('model_config') && !content.includes('frozen')) {
                warnings.push('⚠️ Los modelos Pydantic deben tener model_config = {"frozen": True}');
            }
        }
        
        // Verificar imports desordenados (básico)
        const lines = content.split('\n');
        let inImports = false;
        let lastImportType = 0; // 0: none, 1: stdlib, 2: third-party, 3: local
        
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('import ') || trimmed.startsWith('from ')) {
                inImports = true;
                // Detectar tipo de import (simplificado)
                if (trimmed.includes('from uif') || trimmed.includes('from .')) {
                    if (lastImportType < 3) lastImportType = 3;
                } else if (trimmed.startsWith('import asyncio') || 
                           trimmed.startsWith('import os') ||
                           trimmed.startsWith('import sys') ||
                           trimmed.startsWith('from pathlib') ||
                           trimmed.startsWith('from typing')) {
                    if (lastImportType < 1) lastImportType = 1;
                } else {
                    if (lastImportType < 2) lastImportType = 2;
                }
            } else if (inImports && trimmed && !trimmed.startsWith('#')) {
                inImports = false;
            }
        }
        
        // Verificar uso de pip/poetry
        if (content.includes('pip install') || content.includes('poetry ')) {
            warnings.push('⚠️ Usa "uv add" en lugar de pip/poetry');
        }
        
        // Verificar path injection
        if (content.includes('f"data/{') || content.includes("f'data/{")) {
            if (!content.includes('slugify')) {
                warnings.push('⚠️ Posible path injection. Usa slugify() para sanitizar rutas');
            }
        }
        
        // Si hay warnings, mostrarlos pero permitir
        if (warnings.length > 0) {
            console.error('📋 Validación Python:');
            warnings.forEach(w => console.error('  ' + w));
            
            console.log(JSON.stringify({
                decision: 'allow',
                systemMessage: '⚠️ ' + warnings.length + ' advertencia(s) de estilo UIF'
            }));
        } else {
            console.log(JSON.stringify({ decision: 'allow' }));
        }
        
    } catch (e) {
        console.error('Error en validate-python:', e.message);
        console.log(JSON.stringify({ decision: 'allow' }));
    }
});
