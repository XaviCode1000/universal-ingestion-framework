import asyncio
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import (
    parse_qsl,
    quote,
    quote_plus,
    unquote,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

import aiofiles
import aiosqlite
import polars as pl
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession
import re
import unicodedata
import json
import io
from markitdown import MarkItDown

import argparse
import sys
import questionary
from questionary import Style

# Nuevas dependencias para el pipeline "Elite Optimized"
import ftfy
import trafilatura
import yaml
import nh3
from selectolax.parser import HTMLParser


# --- Configuración Estática ---
BASE_DATA_DIR = Path("data")
MAX_RETRIES = 3
console = Console()


# --- Utilidades de Limpieza y Procesamiento ---
def smart_url_normalize(url: str) -> str:
    """
    Normaliza una URL siguiendo estándares industriales (RFC 3986).
    Maneja automáticamente caracteres especiales, espacios y queries complejas.
    Evita el doble encoding y repara URLs mal formadas.
    Compatible con servidores Legacy (PHP/ASP) convirtiendo espacios a '+' en la query.
    """
    if not url:
        return ""

    # 1. Parsear la URL en sus componentes
    parsed = urlparse(url)

    # 2. Limpiar la RUTA (Path)
    # Primero decodificamos (unquote) para evitar "doble encoding"
    # Luego codificamos (quote) permitiendo solo las barras '/'
    clean_path = quote(unquote(parsed.path), safe="/")

    # 3. Limpiar la QUERY (Parámetros)
    # parse_qsl convierte "?a=1&b=café" en [('a', '1'), ('b', 'café')]
    query_params = parse_qsl(parsed.query, keep_blank_values=True)

    # urlencode reconstruye la string codificando SOLO los valores y claves
    # Usamos quote_plus para compatibilidad con PHP Legacy (Espacio -> +)
    clean_query = urlencode(query_params, quote_via=quote_plus)

    # 4. Reconstruir la URL final
    clean_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            clean_path,
            parsed.params,
            clean_query,
            parsed.fragment,
        )
    )

    return clean_url


def pre_clean_html(raw_html: str) -> str:
    """Elimina ruido que MarkItDown/Trafilatura no necesitan procesar."""
    if not raw_html:
        return ""

    tree = HTMLParser(raw_html)
    # Eliminar elementos irrelevantes para el contenido principal
    tags_to_remove = [
        "script",
        "style",
        "iframe",
        "svg",
        "meta",
        "link",
        "noscript",
        "form",
        "footer",
        "header",
        "nav",
        ".cookie-consent",
        ".ads",
        ".sidebar",
    ]
    for tag in tags_to_remove:
        for node in tree.css(tag):
            node.decompose()

    # Sanitización con nh3 (librería Rust ultra-rápida)
    # Solo permitimos un subconjunto seguro de etiquetas si quisiéramos visualizar,
    # pero aquí lo usamos para asegurar que no hay inyecciones.
    return nh3.clean(tree.html or "")


# --- Modelos ---
class ScrapingScope(str, Enum):
    STRICT = "strict"  # Solo lo que empiece por la URL base (Ideal Docs/Blogs)
    BROAD = "broad"  # Todo el dominio (Ideal Sitios Corporativos)
    SMART = "smart"  # Decisión automática basada en profundidad


class MigrationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCOVERED = "discovered"


class WebPage(BaseModel):
    url: str
    title: str = Field(default="Sin Título")
    content_md_path: str
    assets: List[str] = Field(default_factory=list)
    status: MigrationStatus = MigrationStatus.COMPLETED


def slugify(value: str) -> str:
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


# --- Gestión de Rutas del Proyecto ---
class ProjectPaths(BaseModel):
    domain: str
    root: Path
    content: Path
    images: Path
    docs: Path
    db: Path
    report: Path

    @classmethod
    def create(cls, url: str) -> "ProjectPaths":
        domain = urlparse(url).netloc.replace(".", "_")
        root = BASE_DATA_DIR / domain
        return cls(
            domain=domain,
            root=root,
            content=root / "content",
            images=root / "media" / "images",
            docs=root / "media" / "docs",
            db=root / f"state_{domain}.db",
            report=root / "migration_audit.jsonl",
        )

    def ensure_exists(self) -> None:
        for d in [self.content, self.images, self.docs]:
            d.mkdir(parents=True, exist_ok=True)


async def ensure_dirs() -> None:
    # Esta función ya no es necesaria globalmente, se maneja por policy.paths.ensure_exists()
    pass


# --- Persistencia Mejorada ---
class StateManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            # Habilitar modo WAL para mejor concurrencia
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    url TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    type TEXT,
                    retries INTEGER DEFAULT 0,
                    last_error TEXT,
                    last_try TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Índice para consultas rápidas de reintentos
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_status_type ON urls(status, type)"
            )
            await db.commit()

    async def add_url(
        self, url: str, status: MigrationStatus, m_type: str = "webpage"
    ) -> None:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "INSERT OR IGNORE INTO urls (url, status, type) VALUES (?, ?, ?)",
                (url, status.value, m_type),
            )
            await db.commit()

    async def update_status(
        self, url: str, status: MigrationStatus, error_msg: Optional[str] = None
    ) -> None:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            if error_msg:
                await db.execute(
                    "UPDATE urls SET status = ?, last_error = ?, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                    (status.value, error_msg[:500], url),  # Truncar error para DB
                )
            else:
                await db.execute(
                    "UPDATE urls SET status = ?, last_error = NULL, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                    (status.value, url),
                )
            await db.commit()

    async def increment_retry(self, url: str) -> int:
        """Incrementa el contador de reintentos y devuelve el nuevo valor."""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE urls SET retries = retries + 1, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                (url,),
            )
            await db.commit()
            async with db.execute(
                "SELECT retries FROM urls WHERE url = ?", (url,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_pending_urls(self, m_type: str = "webpage") -> List[str]:
        """
        Obtiene URLs pendientes Y URLs fallidas que aún tienen reintentos disponibles.
        Esto implementa la autocuración.
        """
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            # Lógica: (Status es PENDING) OR (Status es FAILED y retries < MAX_RETRIES)
            query = """
                SELECT url FROM urls 
                WHERE type = ? AND (
                    status = ? 
                    OR (status = ? AND retries < ?)
                )
            """
            async with db.execute(
                query,
                (
                    m_type,
                    MigrationStatus.PENDING.value,
                    MigrationStatus.FAILED.value,
                    MAX_RETRIES,
                ),
            ) as cursor:
                rows = await cursor.fetchall()
                return [str(row[0]) for row in rows]


# --- Configuración Dinámica ---
class ScrapingPolicy(BaseModel):
    url: str
    scope: ScrapingScope = ScrapingScope.SMART
    max_workers: int = 5
    only_text: bool = False
    only_images: bool = False
    only_docs: bool = False
    paths: ProjectPaths

    @classmethod
    def create_simple(
        cls, url: str, workers: int, text: bool, images: bool, docs: bool, scope: str
    ) -> "ScrapingPolicy":
        return cls(
            url=url,
            scope=ScrapingScope(scope),
            max_workers=workers,
            only_text=text,
            only_images=images,
            only_docs=docs,
            paths=ProjectPaths.create(url),
        )


# --- Motor Principal ---
class ArgeliaMigrationEngine:
    def __init__(self, policy: ScrapingPolicy):
        self.policy = policy
        self.base_url = policy.url
        self.domain = urlparse(policy.url).netloc
        self.state = StateManager(policy.paths.db)

        # Colas
        self.url_queue: asyncio.Queue[str] = asyncio.Queue()
        self.asset_queue: asyncio.Queue[str] = asyncio.Queue()

        # Filtros de memoria
        self.seen_urls: Set[str] = set()
        self.seen_assets: Set[str] = set()

        # Contadores
        self.pages_completed = 0
        self.assets_completed = 0

        self.max_workers = policy.max_workers
        self.semaphore = asyncio.Semaphore(self.max_workers)
        self.report_lock = asyncio.Lock()

        self.progress: Optional[Progress] = None
        self.page_task: Optional[TaskID] = None
        self.asset_task: Optional[TaskID] = None
        self.use_browser_mode = False

        # Conversor universal para documentos complejos (PDF, Office) y HTML
        self.md_converter = MarkItDown()

    async def log_event(self, data: dict) -> None:
        """Log en JSONL solo para auditoría profunda."""
        async with self.report_lock:
            async with aiofiles.open(
                self.policy.paths.report, "a", encoding="utf-8"
            ) as f:
                await f.write(json.dumps(data) + "\n")

    async def setup(self) -> None:
        self.policy.paths.ensure_exists()
        await self.state.initialize()

        console.print("[cyan][*][/cyan] Cargando estado y recuperando fallos...")

        # Cargar todo en memoria para deduplicación rápida
        async with aiosqlite.connect(self.state.db_path) as db:
            async with db.execute("SELECT url, type, status FROM urls") as cursor:
                async for row in cursor:
                    url, m_type, status = row
                    if m_type == "asset":
                        self.seen_assets.add(url)
                        if status == MigrationStatus.COMPLETED.value:
                            self.assets_completed += 1
                    else:
                        self.seen_urls.add(url)
                        if status == MigrationStatus.COMPLETED.value:
                            self.pages_completed += 1

        # Poblar colas con URLs pendientes y URLs fallidas recuperables
        pending = await self.state.get_pending_urls()
        if not pending and not self.seen_urls:
            await self.state.add_url(self.base_url, MigrationStatus.PENDING)
            self.seen_urls.add(self.base_url)
            pending = [self.base_url]

        for url in pending:
            await self.url_queue.put(url)

        pending_assets = await self.state.get_pending_urls(m_type="asset")
        for asset in pending_assets:
            await self.asset_queue.put(asset)

        console.print(
            f"[green]✓[/green] Colas cargadas: {len(pending)} Páginas, {len(pending_assets)} Assets."
        )

    async def download_asset(self, asset_url: str) -> None:
        # Aplicar política de filtrado
        if self.policy.only_text:
            return

        parsed = urlparse(asset_url)
        ext = Path(parsed.path).suffix.lower()
        is_pdf = ext == ".pdf"
        is_image = ext in [".jpg", ".png", ".jpeg", ".gif", ".svg", ".webp"]

        if self.policy.only_images and not is_image:
            return
        if self.policy.only_docs and not is_pdf:
            return

        async with self.semaphore:
            try:
                folder = self.policy.paths.docs if is_pdf else self.policy.paths.images
                filename = slugify(Path(parsed.path).stem or "asset") + ext
                local_path = folder / filename

                if not local_path.exists():
                    response = await AsyncFetcher.get(
                        asset_url, impersonate="chrome", timeout=30
                    )
                    if response.status == 200:
                        body_bytes = (
                            response.body
                            if isinstance(response.body, bytes)
                            else response.body.encode()
                        )
                        async with aiofiles.open(local_path, "wb") as f:
                            await f.write(body_bytes)

                        # --- CONVERSIÓN PROACTIVA A MARKDOWN ---
                        if ext in [".pdf", ".docx", ".pptx", ".xlsx"]:
                            try:
                                # MarkItDown procesa el archivo localmente
                                conversion_result = self.md_converter.convert(
                                    str(local_path)
                                )
                                md_path = local_path.with_suffix(".md")

                                # Normalización y Enriquecimiento
                                asset_md = ftfy.fix_text(conversion_result.text_content)
                                asset_metadata = {
                                    "url": asset_url,
                                    "filename": filename,
                                    "format": ext.upper().replace(".", ""),
                                    "ingestion_engine": "UIF v2.0 (Elite Optimized)",
                                }
                                asset_frontmatter = yaml.dump(
                                    asset_metadata, allow_unicode=True, sort_keys=False
                                )

                                async with aiofiles.open(
                                    md_path, "w", encoding="utf-8"
                                ) as f_md:
                                    await f_md.write(
                                        f"---\n{asset_frontmatter}---\n\n{asset_md}"
                                    )
                            except Exception as conv_err:
                                console.print(
                                    f"[dim red]      ! Error convirtiendo {filename}: {str(conv_err)[:100]}[/]"
                                )

                    else:
                        raise Exception(f"HTTP {response.status}")

                await self.state.update_status(asset_url, MigrationStatus.COMPLETED)
                self.assets_completed += 1
                if self.progress and self.asset_task:
                    self.progress.update(
                        self.asset_task, completed=self.assets_completed
                    )

            except Exception as e:
                # Los assets no se reintentan en esta versión para priorizar páginas,
                # pero se registran.
                await self.state.update_status(
                    asset_url, MigrationStatus.FAILED, str(e)
                )

    async def process_page(self, session: AsyncStealthySession, url: str) -> None:
        try:
            # --- CONSTRUCCIÓN DE URL ROBUSTA (INDUSTRIAL STANDARD) ---
            # 1. Unir la URL relativa con la base (resuelve ../ etc.)
            full_absolute_url = urljoin(self.base_url, url)

            # 2. Normalizar y Sanitizar la URL resultante
            # Esto arregla espacios, tildes, símbolos raros y el famoso %3D
            encoded_url = smart_url_normalize(full_absolute_url)
            # ---------------------------------------------------------

            page = None
            if self.use_browser_mode:
                page = await session.fetch(encoded_url, timeout=45000)
            else:
                resp = await AsyncFetcher.get(
                    encoded_url,
                    impersonate="chrome",
                    timeout=20,
                    headers={"Referer": self.base_url, "Origin": self.base_url},
                )

                # --- MANEJO INTELIGENTE DE ERRORES DE SERVIDOR ---
                if resp.status == 500:
                    console.print(
                        f"[dim red]      Server Error (500) en {url}. Saltando...[/]"
                    )
                    await self.state.update_status(
                        url, MigrationStatus.FAILED, "Server Side Error (500)"
                    )
                    return

                if resp.status in [403, 401, 429]:
                    console.print(
                        "[yellow][SWITCH][/] Activando modo navegador global..."
                    )
                    self.use_browser_mode = True
                    page = await session.fetch(encoded_url, timeout=45000)
                elif resp.status == 200:
                    page = resp
                else:
                    raise Exception(f"HTTP {resp.status}")

            if not page:
                raise Exception("Contenido vacío")

            # --- PIPELINE "ELITE OPTIMIZED" (Trafilatura + MarkItDown + FTFY) ---
            # Obtenemos el HTML crudo para el pipeline de refinamiento
            raw_html = getattr(page, "raw_content", "") or getattr(page, "body", "")
            if not isinstance(raw_html, str):
                raw_html = raw_html.decode("utf-8", errors="replace")

            # 1. Extracción de Metadatos Semánticos
            try:
                metadata = trafilatura.extract_metadata(raw_html)
            except Exception:
                metadata = None

            metadata_dict = {
                "url": url,
                "title": getattr(metadata, "title", None) or "Documento",
                "author": getattr(metadata, "author", "Desconocido"),
                "date": getattr(metadata, "date", "N/A"),
                "sitename": getattr(metadata, "sitename", self.domain),
                "ingestion_engine": "UIF v2.0 (Elite Optimized)",
            }

            # 2. Pre-Poda de Alta Velocidad (Selectolax + nh3)
            clean_html = pre_clean_html(raw_html)

            # 3. Motor Híbrido: Trafilatura (Semántico) -> MarkItDown (Literal/Fallback)
            extracted_md = trafilatura.extract(
                clean_html,
                include_tables=True,
                include_comments=False,
                output_format="markdown",
            )

            # Si Trafilatura no devuelve suficiente contenido, usamos MarkItDown como motor de respaldo
            if not extracted_md or len(extracted_md) < 250:
                try:
                    html_stream = io.BytesIO(clean_html.encode("utf-8"))
                    conversion_result = self.md_converter.convert_stream(
                        html_stream, extension=".html"
                    )
                    extracted_md = conversion_result.text_content
                except Exception as e:
                    console.print(
                        f"[dim yellow]      ! Fallback fallido en {url}: {str(e)[:30]}[/]"
                    )
                    extracted_md = extracted_md or "_[Contenido no extraíble]_"

            # 4. Normalización de Texto y Arreglo de Mojibake (FTFY)
            final_md = ftfy.fix_text(extracted_md)
            final_md = re.sub(r"\n{3,}", "\n\n", final_md).strip()

            # 5. Inyección de Contexto (YAML Frontmatter)
            frontmatter = yaml.dump(metadata_dict, allow_unicode=True, sort_keys=False)
            full_content = f"---\n{frontmatter}---\n\n{final_md}"

            # 6. Persistencia Atomizada
            path_slug = slugify(
                url.replace(self.base_url, "").replace(".php", "") or "index"
            )
            md_path = self.policy.paths.content / f"{path_slug}.md"

            async with aiofiles.open(md_path, "w", encoding="utf-8") as f:
                await f.write(full_content)

            title = metadata_dict["title"]

            # Discovery
            new_assets = []
            new_pages = []

            links = [str(node) for node in page.css("a::attr(href)")]
            images = [str(node) for node in page.css("img::attr(src)")]

            for link in links + images:
                if not link:
                    continue
                full_url = urljoin(url, str(link)).split("#")[0]
                parsed_link = urlparse(full_url)

                if parsed_link.netloc != self.domain:
                    continue

                # --- 🛡️ CONTROL DE ALCANCE (SCOPE CONTROL) ---
                should_follow = False

                if self.policy.scope == ScrapingScope.BROAD:
                    # Modo "Todo el sitio": Si es el mismo dominio, entra.
                    should_follow = True

                elif self.policy.scope == ScrapingScope.STRICT:
                    # Modo "Carpeta": Solo si empieza con la URL base.
                    if full_url.startswith(self.base_url):
                        should_follow = True

                elif self.policy.scope == ScrapingScope.SMART:
                    # Modo "Inteligente":
                    # Si la URL base es profunda (ej: /en/latest/), actúa como STRICT.
                    # Si la URL base es la raíz (ej: .com/), actúa como BROAD.
                    path_parts = urlparse(self.base_url).path.strip("/").split("/")
                    path_depth = len([p for p in path_parts if p])
                    is_deep_start = path_depth >= 1

                    if is_deep_start:
                        if full_url.startswith(self.base_url):
                            should_follow = True
                    else:
                        should_follow = True

                if not should_follow:
                    continue
                # ---------------------------------------------

                is_asset = any(
                    full_url.lower().endswith(ext)
                    for ext in [
                        ".pdf",
                        ".jpg",
                        ".png",
                        ".jpeg",
                        ".gif",
                        ".svg",
                        ".webp",
                    ]
                )

                if is_asset:
                    if full_url not in self.seen_assets:
                        self.seen_assets.add(full_url)
                        new_assets.append(full_url)
                else:
                    if not any(
                        full_url.lower().endswith(x)
                        for x in [".css", ".js", ".json", ".xml", ".ico"]
                    ):
                        if full_url not in self.seen_urls:
                            self.seen_urls.add(full_url)
                            new_pages.append(full_url)

            # Batch Insert
            for asset in new_assets:
                await self.state.add_url(asset, MigrationStatus.PENDING, m_type="asset")
                await self.asset_queue.put(asset)

            for p_url in new_pages:
                await self.state.add_url(p_url, MigrationStatus.PENDING)
                await self.url_queue.put(p_url)

            await self.state.update_status(url, MigrationStatus.COMPLETED)
            self.pages_completed += 1

            if self.progress:
                if self.page_task:
                    self.progress.update(
                        self.page_task,
                        completed=self.pages_completed,
                        total=len(self.seen_urls),
                    )
                if self.asset_task:
                    self.progress.update(self.asset_task, total=len(self.seen_assets))

            await self.log_event(
                WebPage(
                    url=url,
                    title=title,
                    content_md_path=str(md_path),
                    assets=new_assets,
                ).model_dump()
            )

        except Exception as e:
            # --- LÓGICA DE AUTOCURACIÓN (SELF-HEALING) ---
            current_retries = await self.state.increment_retry(url)

            console.print(
                f"[yellow][RETRY {current_retries}/{MAX_RETRIES}][/yellow] Error en {url}: {str(e)[:50]}..."
            )

            if current_retries < MAX_RETRIES:
                # Aún tenemos vidas. Re-encolar para intentarlo más tarde.
                # No marcamos como FAILED, sino que dejamos que el worker lo vuelva a tomar.
                await self.url_queue.put(url)
            else:
                # Game Over para esta URL
                await self.state.update_status(url, MigrationStatus.FAILED, str(e))
                await self.log_event(
                    {
                        "url": url,
                        "status": "failed",
                        "error": str(e),
                        "retries": current_retries,
                    }
                )

    async def page_worker(self, session: AsyncStealthySession) -> None:
        while True:
            url = await self.url_queue.get()
            try:
                await self.process_page(session, url)
            finally:
                self.url_queue.task_done()

    async def asset_worker(self) -> None:
        while True:
            url = await self.asset_queue.get()
            try:
                await self.download_asset(url)
            finally:
                self.asset_queue.task_done()

    async def generate_summary(self) -> None:
        console.print("\n[bold cyan]📊 Reporte Final de Migración (Fuente: SQLite)[/]")

        async with aiosqlite.connect(self.state.db_path) as db:
            # 1. Resumen General
            # Ejecutamos la query y esperamos el resultado (cursor)
            cursor = await db.execute(
                "SELECT status, COUNT(*) as count FROM urls GROUP BY status"
            )
            rows = await cursor.fetchall()  # Obtenemos las filas como lista de tuplas

            # Convertimos directamente a DataFrame (Más portable, no requiere PyArrow)
            if rows:
                schema_gen = {"status": pl.String, "count": pl.Int64}
                df = pl.DataFrame(rows, schema=schema_gen, orient="row")
                df_sorted = df.sort("count", descending=True)
                console.print(df_sorted)
            else:
                console.print("[dim]No hay datos en la base de datos.[/dim]")

            # 2. Análisis de Fallos (Granularidad de Errores)
            console.print("\n[bold red]⚠️  Análisis de Fallos Críticos:[/]")

            cursor_fail = await db.execute(
                "SELECT COALESCE(last_error, 'Unknown Error') as error_type, COUNT(*) as count FROM urls WHERE status='failed' GROUP BY last_error ORDER BY count DESC LIMIT 5"
            )
            rows_fail = await cursor_fail.fetchall()

            if rows_fail:
                # Especificamos tipos exactos para evitar conflictos con Rust/Polars
                schema_fail = {"error_type": pl.String, "count": pl.Int64}
                df_failures = pl.DataFrame(rows_fail, schema=schema_fail, orient="row")
                console.print(df_failures)
            else:
                console.print("[green]¡No se detectaron fallos críticos![/green]")

    async def run(self) -> None:
        await self.setup()

        dns_args = {
            "args": [
                "--host-resolver-rules=MAP apointflammebleue-dz.com 51.79.21.111, MAP www.apointflammebleue-dz.com 51.79.21.111",
                "--disable-gpu",
                "--no-sandbox",
            ]
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=console,
        ) as progress:
            self.progress = progress

            self.page_task = progress.add_task(
                "[cyan]Páginas",
                total=len(self.seen_urls),
                completed=self.pages_completed,
            )
            self.asset_task = progress.add_task(
                "[magenta]Assets",
                total=len(self.seen_assets),
                completed=self.assets_completed,
            )

            async with AsyncStealthySession(
                headless=True,
                max_pages=self.policy.max_workers,
                solve_cloudflare=True,
                additional_args=dns_args,
            ) as session:
                page_workers = [
                    asyncio.create_task(self.page_worker(session))
                    for _ in range(self.policy.max_workers)
                ]
                asset_workers = [
                    asyncio.create_task(self.asset_worker()) for _ in range(8)
                ]

                await self.url_queue.join()
                console.print("[yellow]Páginas completadas. Esperando assets...[/]")
                await self.asset_queue.join()

                for w in page_workers + asset_workers:
                    w.cancel()

        await self.generate_summary()


async def main() -> None:
    # Si no hay argumentos, entramos en modo interactivo "Wizard"
    if len(sys.argv) == 1:
        custom_style = Style(
            [
                ("qmark", "fg:#ffff00 bold"),  # Amarillo para la pregunta
                ("question", "bold"),  # Pregunta en negrita
                ("answer", "fg:#00ffff bold"),  # Cian para la respuesta dada
                ("pointer", "fg:#ffff00 bold"),  # Flecha en amarillo
                ("highlighted", "fg:#ffff00 bold"),  # Opción actual en amarillo
                ("selected", "fg:#ffff00"),  # Checkbox marcado en amarillo
                ("separator", "fg:#666666"),
                ("instruction", "fg:#858585 italic"),
                ("text", ""),
                ("disabled", "fg:#858585 italic"),
            ]
        )

        console.print(
            Panel.fit(
                "[bold yellow]🛸 ASISTENTE DE INGESTA UNIVERSAL[/]\n"
                "[dim]Configuración guiada para el motor de migración de élite[/]",
                border_style="yellow",
            )
        )

        url = await questionary.text(
            "¿Cuál es la URL base del sitio?",
            placeholder="https://ejemplo.com/",
            style=custom_style,
            instruction="(Escribe la URL y presiona Enter)",
        ).ask_async()

        if url is None:
            return

        if not url.strip():
            console.print("[bold red]Error: Se requiere una URL para continuar.[/]")
            return

        scope_choice = await questionary.select(
            "¿Cómo debe comportarse el motor de navegación?",
            choices=[
                questionary.Choice(
                    "🧠 Auto (Recomendado)",
                    value="smart",
                    description="Detecta automáticamente si es un sub-sitio o un portal completo.",
                ),
                questionary.Choice(
                    "🎯 Estricto (Solo esta sección)",
                    value="strict",
                    description=f"Solo descargará enlaces que empiecen por: {url}",
                ),
                questionary.Choice(
                    "🌍 Global (Todo el dominio)",
                    value="broad",
                    description="Descargará cualquier enlace dentro del dominio, sin importar la carpeta.",
                ),
            ],
            style=custom_style,
            instruction="(Usa flechas para elegir la estrategia)",
        ).ask_async()

        if not scope_choice:
            return

        choices = await questionary.checkbox(
            "¿Qué elementos deseas extraer?",
            choices=[
                questionary.Choice(
                    "Texto (Markdown de alta fidelidad)", value="text", checked=True
                ),
                questionary.Choice(
                    "Imágenes (Galería local)", value="images", checked=True
                ),
                questionary.Choice(
                    "Documentos (PDF, Word, etc.)", value="docs", checked=True
                ),
            ],
            style=custom_style,
            instruction="(Espacio para marcar, Enter para confirmar)",
        ).ask_async()

        if choices is None:
            return

        if not choices:
            console.print("[bold red]Error: Debes seleccionar al menos un elemento.[/]")
            return

        workers = await questionary.select(
            "¿Cuántos procesos simultáneos (workers) deseas usar?",
            choices=[
                "1 (Modo Seguro - Lento)",
                "5 (Equilibrado - Recomendado)",
                "10 (Agresivo - Rápido)",
                "20 (Modo Bestia - Riesgo de bloqueo)",
            ],
            default="5 (Equilibrado - Recomendado)",
            style=custom_style,
            instruction="(Usa las flechas y presiona Enter)",
        ).ask_async()

        if workers is None:
            return

        num_workers = int(workers.split()[0])

        policy = ScrapingPolicy.create_simple(
            url=url,
            workers=num_workers,
            text="text" in choices,
            images="images" in choices,
            docs="docs" in choices,
            scope=scope_choice,
        )

    else:
        # Modo CLI tradicional para automatización
        parser = argparse.ArgumentParser(description="Multi-site Scraper de Élite")
        parser.add_argument("url", help="URL base del sitio a procesar")
        parser.add_argument(
            "--scope",
            choices=["smart", "strict", "broad"],
            default="smart",
            help="Define el alcance de la navegación",
        )
        parser.add_argument(
            "--workers", type=int, default=5, help="Número de workers concurrentes"
        )
        parser.add_argument(
            "--only-text", action="store_true", help="Solo guardar contenido Markdown"
        )
        parser.add_argument(
            "--only-images", action="store_true", help="Solo descargar imágenes"
        )
        parser.add_argument(
            "--only-docs",
            action="store_true",
            help="Solo descargar documentos (PDF, etc.)",
        )

        args = parser.parse_args()

        policy = ScrapingPolicy.create_simple(
            url=args.url,
            workers=args.workers,
            text=args.only_text,
            images=args.only_images,
            docs=args.only_docs,
            scope=args.scope,
        )

    engine = ArgeliaMigrationEngine(policy)
    await engine.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupción recibida.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Error fatal: {e}[/]")
