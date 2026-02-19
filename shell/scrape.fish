# scrape.fish - Wrapper CLI para Universal Ingestion Framework
# Motor de ingesta de conocimiento de alta fidelidad para LLMs y sistemas RAG

function scrape -d "UIF - Transformá contenido web a Markdown"
    # Especificaciones de opciones
    argparse -n scrape \
        'h/help' \
        's/setup' \
        'u/url=' \
        'c/config=' \
        'w/workers=' \
        'd/output-dir=' \
        'scope=' \
        'o/only-text' \
        'v/verbose' \
        'q/quiet' \
        'dry-run' \
        'list-scopes' \
        -- $argv

    # Manejar errores de parseo
    or return 1

    # Directorio del proyecto
    set -l project_dir "$HOME/Dev/my_apps/universal-ingestion-framework"

    # Mostrar ayuda
    if set -ql _flag_help[1]
        _scrape_show_help
        return 0
    end

    # Listar scopes disponibles
    if set -ql _flag_list_scopes[1]
        echo "Scopes disponibles:"
        echo "  smart  - Auto-detectar: dominio raíz = broad, subdirectorio = strict"
        echo "  strict - Solo URLs bajo la ruta de la URL semilla"
        echo "  broad  - Todas las URLs dentro del mismo dominio"
        return 0
    end

    # Construir comando
    set -l cmd uv run uif-scraper

    # Modo setup
    if set -ql _flag_setup[1]
        echo "🛸 Iniciando asistente de configuración de UIF Scraper..."
        cd $project_dir
        eval $cmd --setup
        return $status
    end

    # Archivo de configuración
    if set -ql _flag_config[1]
        set -a cmd --config $_flag_config
    end

    # Workers
    if set -ql _flag_workers[1]
        set -a cmd --workers $_flag_workers
    end

    # Directorio de salida
    if set -ql _flag_output_dir[1]
        set -a cmd --output-dir $_flag_output_dir
    end

    # Scope
    if set -ql _flag_scope[1]
        set -a cmd --scope $_flag_scope
    end

    # Solo texto (sin assets)
    if set -ql _flag_only_text[1]
        set -a cmd --only-text
    end

    # URL desde flag o argumento posicional
    set -l target_url
    if set -ql _flag_url[1]
        set target_url $_flag_url
    else if test (count $argv) -gt 0
        set target_url $argv[1]
    end

    # Validar que se proporcionó URL (salvo en dry-run o setup)
    if not set -ql _flag_dry_run[1]
        if test -z "$target_url"
            echo "Error: La URL es requerida." >&2
            echo "Uso: scrape <URL> [opciones]" >&2
            echo "Ejecutá 'scrape --help' para más información." >&2
            return 1
        end
    end

    # Directorio de salida por defecto
    set -l output_dir (set -ql _flag_output_dir[1] && echo $_flag_output_dir || echo "./data")

    # Dry run - mostrar qué se ejecutaría
    if set -ql _flag_dry_run[1]
        echo "📋 Dry run - comando que se ejecutaría:"
        echo "  cd $project_dir"
        echo "  $cmd $target_url"
        echo ""
        echo "📁 Directorio de salida: $output_dir"
        return 0
    end

    # Modo verbose
    if set -ql _flag_verbose[1]
        echo "🚀 Iniciando UIF Scraper..."
        echo "   URL: $target_url"
        echo "   Directorio de salida: $output_dir"
        echo "   Workers: "(set -ql _flag_workers[1] && echo $_flag_workers || echo "por defecto (5)")
        echo "   Scope: "(set -ql _flag_scope[1] && echo $_flag_scope || echo "smart")
        echo "   Assets: "(set -ql _flag_only_text[1] && echo "desactivados" || echo "activados")
        echo ""
    end

    # Modo quiet
    if set -ql _flag_quiet[1]
        set -a cmd 2>/dev/null
    end

    # Ejecutar
    cd $project_dir
    eval $cmd $target_url

    return $status
end

function _scrape_show_help
    echo ""
    echo "🛸 Universal Ingestion Framework (UIF) v3.0"
    echo ""
    echo "USO"
    echo "    scrape <URL> [OPCIONES]"
    echo "    scrape --setup"
    echo ""
    echo "DESCRIPCIÓN"
    echo "    Motor de ingesta de conocimiento de alta fidelidad que transforma"
    echo "    contenido web y documentos binarios a Markdown optimizado para"
    echo "    LLMs y sistemas RAG."
    echo ""
    echo "OPCIONES"
    echo "    -h, --help              Mostrar este mensaje de ayuda"
    echo "    -s, --setup             Iniciar asistente de configuración interactivo"
    echo "    -u, --url=URL           URL objetivo a scrapear"
    echo "    -d, --output-dir=DIR    Directorio de salida (por defecto: ./data)"
    echo "    -c, --config=ARCH       Usar archivo de configuración custom (YAML)"
    echo "    -w, --workers=N         Número de workers concurrentes (por defecto: 5)"
    echo "    --scope=SCOPE           Alcance del rastreo: smart, strict, broad (defecto: smart)"
    echo "    -o, --only-text         Saltar descarga de assets (imágenes, PDFs)"
    echo "    -v, --verbose           Mostrar información detallada de ejecución"
    echo "    -q, --quiet             Suprimir salida que no sean errores"
    echo "    --dry-run               Mostrar comando sin ejecutarlo"
    echo "    --list-scopes           Mostrar opciones de scope disponibles"
    echo ""
    echo "OPCIONES DE SCOPE"
    echo "    smart   Auto-detectar basado en la URL semilla:"
    echo "            - Dominio raíz (ej: example.com/) → scope broad"
    echo "            - Subdirectorio (ej: example.com/blog/) → scope strict"
    echo ""
    echo "    strict  Solo rastrear URLs que comienzan con la ruta de la URL semilla."
    echo "            Ideal para scrapear secciones específicas de un sitio."
    echo ""
    echo "    broad   Rastrear todas las URLs dentro del mismo dominio."
    echo "            Usar con precaución en sitios grandes."
    echo ""
    echo "EJEMPLOS"
    echo "    # Uso básico (guarda en ./data)"
    echo "    scrape https://example.com"
    echo ""
    echo "    # Especificar directorio de salida personalizado"
    echo "    scrape https://example.com -d ~/Documentos/scraping"
    echo ""
    echo "    # Usar archivo de configuración personalizado"
    echo "    scrape https://example.com -c ~/.config/uif-scraper/config.yaml"
    echo ""
    echo "    # Con workers y scope personalizados"
    echo "    scrape https://example.com/blog --workers 10 --scope strict"
    echo ""
    echo "    # Solo texto, sin assets"
    echo "    scrape https://docs.python.org/3/ --only-text"
    echo ""
    echo "    # Configuración interactiva (genera config.yaml)"
    echo "    scrape --setup"
    echo ""
    echo "    # Dry run para previsualizar el comando"
    echo "    scrape https://example.com --dry-run"
    echo ""
    echo "ARCHIVO DE CONFIGURACIÓN"
    echo "    Ubicaciones buscadas (en orden):"
    echo "    1. Ruta especificada con --config"
    echo "    2. \$XDG_CONFIG_HOME/uif-scraper/config.yaml"
    echo "    3. ~/.config/uif-scraper/config.yaml"
    echo "    4. /etc/uif-scraper/config.yaml"
    echo ""
    echo "    Opciones disponibles en config.yaml:"
    echo "    data_dir: ~/scraping-data          # Directorio de salida"
    echo "    default_workers: 5                 # Workers para páginas"
    echo "    asset_workers: 8                   # Workers para assets"
    echo "    max_retries: 3                     # Reintentos máximos"
    echo "    timeout_seconds: 30                # Timeout por request"
    echo "    log_level: INFO                    # DEBUG, INFO, WARNING, ERROR"
    echo "    db_pool_size: 5                    # Pool de conexiones SQLite"
    echo ""
    echo "    Ver config.example.yaml en el proyecto para ejemplo completo."
    echo ""
    echo "ESTRUCTURA DE SALIDA"
    echo "    <output-dir>/"
    echo "    └── example_com/"
    echo "        ├── content/              # Archivos Markdown (.md.zst comprimidos)"
    echo "        ├── media/"
    echo "        │   ├── images/           # Imágenes descargadas"
    echo "        │   └── docs/             # PDFs + .md convertidos"
    echo "        └── state.db              # Estado SQLite (modo WAL, batched)"
    echo ""
    echo "FEATURES"
    echo "    - Extracción de texto con 4 niveles de fallback (Trafilatura → MarkItDown → BS4)"
    echo "    - Compresión Zstandard para markdown (30-40% más chico)"
    echo "    - Procesamiento batch async con connection pooling"
    echo "    - SQLite en modo WAL con reintento automático en locks"
    echo ""
    echo "DOCUMENTACIÓN"
    echo "    Proyecto: ~/Dev/my_apps/universal-ingestion-framework"
    echo "    Changelog: docs/CHANGELOG.md"
    echo ""
    echo "AUTOR"
    echo "    UIF Scraper - Universal Ingestion Framework"
    echo ""
end
