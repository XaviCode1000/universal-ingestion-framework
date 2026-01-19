import shutil
from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel

console = Console()

TARGETS: List[Path] = [
    Path("data"),
    Path(".pytest_cache"),
    Path(".mypy_cache"),
    Path(".ruff_cache"),
    Path(".coverage"),
    Path("__pycache__"),
]


def get_path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


def purge_system() -> None:
    console.print(
        Panel.fit(
            "[bold red]☢ MODO PURGA ACTIVADO ☢[/bold red]",
            subtitle="Saneamiento de Infraestructura de Datos",
            border_style="red",
        )
    )

    total_freed: int = 0
    found_anything: bool = False

    for target in TARGETS:
        if target.name == "__pycache__":
            pycache_dirs = list(Path(".").glob("**/__pycache__"))
            for pdir in pycache_dirs:
                found_anything = True
                size = get_path_size(pdir)
                total_freed += size
                try:
                    shutil.rmtree(pdir)
                    console.print(
                        f"[yellow]  - Purgando cache:[/] [dim]{pdir}[/] [bold cyan]({format_size(size)})[/]"
                    )
                except Exception as e:
                    console.print(f"[red]  - Error en {pdir}: {e}[/]")
            continue

        if target.exists():
            found_anything = True
            size = get_path_size(target)
            total_freed += size

            try:
                if target.is_dir():
                    shutil.rmtree(target)
                    console.print(
                        f"[yellow]  - Eliminando directorio:[/] [bold] {target}[/] [dim]({format_size(size)})[/]"
                    )
                else:
                    target.unlink()
                    console.print(
                        f"[yellow]  - Eliminando archivo:[/] [bold] {target}[/] [dim]({format_size(size)})[/]"
                    )
            except Exception as e:
                console.print(f"[red]  - Error fatal eliminando {target}: {e}[/]")

    if not found_anything:
        console.print(
            "\n[green]✨ Entorno nominal. No se detectaron residuos de datos.[/]"
        )
    else:
        console.print(
            Panel(
                f"[bold green]✅ PURGA COMPLETADA[/]\n\n"
                f"Espacio total recuperado: [bold cyan]{format_size(total_freed)}[/]\n"
                f"[dim]Estado del sistema: LISTO PARA MIGRACIÓN LIMPIA[/dim]",
                border_style="green",
            )
        )


if __name__ == "__main__":
    purge_system()
