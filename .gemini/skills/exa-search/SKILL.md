---
name: exa-search
description: Búsqueda web avanzada con Exa AI. Busca documentación, código, papers, noticias y contenido técnico. Úsalo cuando necesites información actualizada, documentación de librerías, o ejemplos de código.
---

# EXA-SEARCH: Búsqueda Web con Exa AI

> Skill para búsqueda web avanzada usando Exa MCP Server. Ideal para encontrar documentación, código, papers y contenido técnico actualizado.

## Disparadores (Triggers)

- Cuando se necesita documentación de librerías/frameworks
- Cuando se buscan ejemplos de código
- Cuando se necesita información actualizada
- Cuando se investigan tecnologías o herramientas
- Cuando se buscan papers o artículos técnicos

---

## HERRAMIENTAS DISPONIBLES

### web_search_exa
Búsqueda web general. Ideal para encontrar documentación, tutoriales, artículos.

**Parámetros:**
- `query` (string, requerido): Consulta de búsqueda
- `numResults` (number, opcional): Número de resultados (default: 10)
- `useAutoprompt` (boolean, opcional): Usar autoprompt para mejorar la query

### get_code_context_exa
Búsqueda especializada en código. Encuentra ejemplos de GitHub, Stack Overflow, documentación técnica.

**Parámetros:**
- `query` (string, requerido): Consulta de búsqueda de código
- `tokensNum` (number, opcional): Tokens de contexto (default: 5000, rango: 1000-50000)

### company_research_exa
Investigación de empresas. Encuentra información de negocios, noticias, insights.

**Parámetros:**
- `query` (string, requerido): Nombre de la empresa o consulta
- `numResults` (number, opcional): Número de resultados

### web_search_advanced_exa
Búsqueda avanzada con filtros completos.

**Parámetros:**
- `query` (string, requerido): Consulta de búsqueda
- `numResults` (number, opcional): Número de resultados
- `type` (string): "auto", "fast", "deep", "neural"
- `category` (string): "company", "news", "tweet", "people", "research paper", "personal site", "financial report"
- `includeDomains` (array): Dominios específicos
- `excludeDomains` (array): Dominios a excluir
- `startPublishedDate` (string): Fecha inicio (ISO 8601)
- `endPublishedDate` (string): Fecha fin (ISO 8601)
- `livecrawl` (string): "fallback", "preferred"

---

## PATRONES DE USO

### Búsqueda de Documentación Python
```
get_code_context_exa {
  "query": "Python Polars Lazy API examples",
  "tokensNum": 5000
}
```

### Búsqueda de Frameworks
```
web_search_exa {
  "query": "Pydantic V2 frozen model best practices",
  "numResults": 10
}
```

### Búsqueda Avanzada con Filtros
```
web_search_advanced_exa {
  "query": "asyncio TaskGroups Python 3.12",
  "category": "research paper",
  "startPublishedDate": "2024-01-01",
  "numResults": 15
}
```

### Búsqueda en Dominios Específicos
```
web_search_advanced_exa {
  "query": "Scrapling web scraping Python",
  "includeDomains": ["github.com", "docs.scrapling.com"],
  "numResults": 10
}
```

---

## CATEGORÍAS DISPONIBLES

| Categoría | Uso |
|-----------|-----|
| `company` | Homepages, metadata de empresas |
| `news` | Cobertura de prensa, anuncios |
| `tweet` | Twitter/X, discusiones sociales |
| `people` | LinkedIn profiles, bios públicos |
| `research paper` | Papers académicos, arXiv |
| `personal site` | Blogs personales, portfolios |
| `financial report` | SEC filings, earnings reports |

---

## RESTRICCIONES POR CATEGORÍA

### category: "company"
- ❌ `includeDomains` / `excludeDomains`
- ❌ `startPublishedDate` / `endPublishedDate`
- ❌ `includeText` / `excludeText`

### category: "tweet"
- ❌ `includeText` / `excludeText`
- ❌ `includeDomains` / `excludeDomains`
- ✅ `startPublishedDate` / `endPublishedDate`

### category: "people"
- ❌ `startPublishedDate` / `endPublishedDate`
- ❌ `excludeDomains`
- ✅ `includeDomains` (solo LinkedIn)

### category: "research paper"
- ✅ Todos los filtros disponibles

---

## EJEMPLOS PARA UIF

### Buscar patrones Pydantic V2
```
get_code_context_exa {
  "query": "Pydantic V2 frozen model Python 3.12 example",
  "tokensNum": 3000
}
```

### Buscar ejemplos Polars Lazy
```
get_code_context_exa {
  "query": "Polars Lazy API scan_parquet filter collect Python",
  "tokensNum": 5000
}
```

### Buscar asyncio TaskGroups
```
get_code_context_exa {
  "query": "Python asyncio TaskGroup semaphore concurrency example",
  "tokensNum": 4000
}
```

### Buscar Scrapling examples
```
get_code_context_exa {
  "query": "Scrapling Python impersonate chrome web scraping",
  "tokensNum": 3000
}
```

### Buscar aiosqlite WAL
```
get_code_context_exa {
  "query": "aiosqlite WAL mode async Python example",
  "tokensNum": 3000
}
```

---

## TIPS

1. **Incluye el lenguaje**: Siempre incluye "Python" en la query para código
2. **Incluye versión**: Agrega versión cuando sea relevante (ej: "Python 3.12", "Pydantic V2")
3. **Tokens**: Usa 3000-5000 para snippets, 10000+ para documentación completa
4. **Categoría**: Usa `research paper` para papers, `company` para empresas
5. **Dominios**: Usa `includeDomains` para buscar en documentación oficial

---

## FORMATO DE SALIDA

Al usar Exa, devuelve:

1. **Resultados**: Lista estructurada con lo más relevante
2. **Fuentes**: URLs de donde viene la información
3. **Notas**: Versiones, restricciones, o advertencias

---

## CONFIGURACIÓN MCP

```json
{
  "mcpServers": {
    "exa": {
      "httpUrl": "https://mcp.exa.ai/mcp"
    }
  }
}
```

> **Nota**: El servidor remoto de Exa no requiere API key para uso básico. Para uso avanzado, obtener API key en [dashboard.exa.ai](https://dashboard.exa.ai/api-keys).
