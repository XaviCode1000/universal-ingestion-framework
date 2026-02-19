# EXA SEARCH - Web & Code Search MCP

> Skill para búsqueda web, código y research de compañías usando Exa MCP Server.

## Descripción

Exa es un motor de búsqueda diseñado para AIs. Proporciona:
- **Web Search**: Búsqueda web con contenido limpio
- **Code Search**: Ejemplos de código, docs, StackOverflow, GitHub
- **Company Research**: Información de empresas, noticias, insights

## Requisitos

**⚠️ IMPORTANTE**: Exa requiere API Key.

1. Obtené tu API key en: https://dashboard.exa.ai/api-keys
2. Configurala como variable de entorno:
   ```bash
   export EXA_API_KEY="tu-api-key-aqui"
   ```

---

## Herramientas Disponibles

### Por Defecto (habilitadas)

| Herramienta | Descripción |
|-------------|-------------|
| `web_search_exa` | Búsqueda web general con contenido limpio |
| `get_code_context_exa` | Ejemplos de código, docs, soluciones de GitHub/StackOverflow |
| `company_research_exa` | Research de empresas, noticias, insights |

### Avanzadas (requieren habilitación)

| Herramienta | Descripción |
|-------------|-------------|
| `web_search_advanced_exa` | Búsqueda avanzada con filtros completos |
| `crawling_exa` | Obtener contenido completo de una URL específica |
| `people_search_exa` | Búsqueda de perfiles profesionales |
| `deep_researcher_start` | Iniciar agente de investigación profunda |
| `deep_researcher_check` | Verificar estado de investigación |

---

## Ejemplos de Uso

### Búsqueda Web Simple
```json
{
  "query": "Python asyncio best practices 2024",
  "numResults": 10
}
```

### Búsqueda de Código
```json
{
  "query": "Python Pydantic V2 frozen model example",
  "tokensNum": 3000
}
```

### Research de Compañía
```json
{
  "query": "Anthropic AI company funding valuation"
}
```

### Búsqueda Avanzada con Filtros
```json
{
  "query": "machine learning engineering",
  "category": "company",
  "numResults": 20,
  "startPublishedDate": "2024-01-01",
  "includeDomains": ["techcrunch.com", "bloomberg.com"]
}
```

---

## Categorías Disponibles

| Categoría | Uso |
|-----------|-----|
| `company` | Homepages, metadata (headcount, funding, revenue) |
| `news` | Cobertura de prensa, anuncios |
| `tweet` | Presencia social, comentarios públicos |
| `people` | Perfiles LinkedIn (datos públicos) |
| `research paper` | Papers académicos, arXiv |
| `personal site` | Blogs personales, portfolios |
| `financial report` | SEC filings, earnings reports |

---

## Restricciones por Categoría

### `category: "company"`
- ❌ `includeDomains` / `excludeDomains`
- ❌ `startPublishedDate` / `endPublishedDate`
- ❌ Filtros de fecha

### `category: "tweet"`
- ❌ `includeText` / `excludeText`
- ❌ `includeDomains` / `excludeDomains`
- ✅ Filtros de fecha funcionan

### `includeText` / `excludeText`
- ⚠️ Solo soportan **arrays de un solo item**
- Multi-item causa error 400

---

## Tips de Uso

1. **Incluí el lenguaje** en queries de código: `"Python Polars lazy API"` no solo `"lazy API"`

2. **Usá `tokensNum`** para controlar contexto:
   - Snippet enfocado: 1000-3000
   - Normal: 5000
   - Integración compleja: 10000-20000

3. **Variaciones de query** para mejor cobertura:
   - Exa devuelve diferentes resultados con diferentes frases
   - Ejecutá 2-3 variaciones en paralelo

4. **`livecrawl: "fallback"`** para contenido fresco o páginas dinámicas

---

## Configuración MCP

```json
{
  "mcpServers": {
    "exa": {
      "url": "https://mcp.exa.ai/mcp",
      "description": "Exa Search - Web search, code search, company research"
    }
  }
}
```
