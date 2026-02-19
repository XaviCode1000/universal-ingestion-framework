#!/usr/bin/env node
/**
 * Hook: AfterModel
 * Valida formato de respuesta según AGENTS.md
 */

const fs = require('fs');

// Leer input desde stdin
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    try {
        const data = JSON.parse(input);
        const response = data.prompt_response || '';
        const prompt = data.prompt || '';
        
        // Verificar si es una respuesta de código
        const isCodeResponse = response.includes('```python') || 
                                response.includes('```bash') ||
                                response.includes('<code_output>');
        
        // Verificar estructura esperada para respuestas de código
        if (isCodeResponse) {
            const hasThoughtProcess = response.includes('<thought_process>');
            const hasAuditReport = response.includes('<uif_audit_report>');
            const hasOptimizationLog = response.includes('<optimization_log>');
            
            // Si falta la estructura, sugerir (no bloquear)
            if (!hasThoughtProcess && !hasAuditReport) {
                console.error('💡 Sugerencia: Considera usar la estructura UIF:');
                console.error('   <thought_process> → <uif_audit_report> → <code_output> → <optimization_log>');
            }
        }
        
        // Verificar idioma (debe ser español)
        const englishIndicators = [
            'Here is', 'Here\'s', 'I will', 'I\'ll', 'Let me', 
            'The code', 'This will', 'You can', 'Note that'
        ];
        
        let hasEnglish = false;
        for (const indicator of englishIndicators) {
            if (response.includes(indicator)) {
                hasEnglish = true;
                break;
            }
        }
        
        if (hasEnglish) {
            console.error('⚠️ Recuerda responder en español (Rioplatense con voseo)');
        }
        
        // Permitir siempre
        console.log(JSON.stringify({ decision: 'allow' }));
        
    } catch (e) {
        console.error('Error en validate-response:', e.message);
        console.log(JSON.stringify({ decision: 'allow' }));
    }
});
