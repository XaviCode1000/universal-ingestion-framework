"""UIF Reporter Service with Catppuccin theme."""

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from uif_scraper.db_manager import StateManager


class ReporterService:
    """Service for generating execution summaries with Catppuccin styling."""

    # Catppuccin Mocha colors
    COLORS = {
        "mauve": "#cba6f7",
        "green": "#a6e3a1",
        "red": "#f38ba8",
        "yellow": "#f9e2af",
        "blue": "#89b4fa",
        "lavender": "#b4befe",
        "text": "#cdd6f4",
        "subtext0": "#a6adc8",
        "surface1": "#45475a",
    }

    def __init__(self, console: Console, state_manager: StateManager):
        self.console = console
        self.state = state_manager

    async def generate_summary(self) -> None:
        """Generate and display execution summary."""
        self.console.print("\n")
        self.console.print(
            Rule(
                title=f"[bold {self.COLORS['mauve']}]🚀 INGESTIÓN FINALIZADA[/]",
                style=self.COLORS["mauve"],
            )
        )
        self.console.print("\n")

        async with self.state.pool.acquire() as db:
            cursor = await db.execute(
                "SELECT status, COUNT(*) as count FROM urls GROUP BY status"
            )
            rows = await cursor.fetchall()

            if rows:
                status_table = Table(
                    title=f"[bold {self.COLORS['lavender']}]📊 Resumen de Ejecución[/]",
                    box=None,
                    header_style=f"bold {self.COLORS['mauve']}",
                    expand=False,
                )
                status_table.add_column(
                    "Estado", justify="left", style=self.COLORS["text"]
                )
                status_table.add_column(
                    "Cantidad", justify="right", style=f"bold {self.COLORS['lavender']}"
                )

                total = 0
                for status_val, count in rows:
                    total += count
                    color = (
                        self.COLORS["green"]
                        if status_val == "completed"
                        else self.COLORS["yellow"]
                    )
                    if status_val == "failed":
                        color = self.COLORS["red"]
                    icon = "✅" if status_val == "completed" else "⏳"
                    if status_val == "failed":
                        icon = "❌"
                    status_table.add_row(
                        f"{icon} {status_val.capitalize()}", str(count), style=color
                    )

                status_table.add_section()
                status_table.add_row(
                    "Total Procesado",
                    str(total),
                    style=f"bold {self.COLORS['blue']}",
                )
                self.console.print(status_table)

            self.console.print("\n")
            cursor_fail = await db.execute(
                "SELECT COALESCE(last_error, 'Unknown') as error, COUNT(*) as count "
                "FROM urls WHERE status='failed' GROUP BY last_error ORDER BY count DESC LIMIT 5"
            )
            rows_fail = await cursor_fail.fetchall()

            if rows_fail:
                fail_table = Table(
                    title=f"[bold {self.COLORS['red']}]⚠️ Diagnóstico de Errores (Top 5)[/]",
                    box=None,
                    header_style=f"bold {self.COLORS['red']}",
                    expand=True,
                    border_style=self.COLORS["red"],
                )
                fail_table.add_column(
                    "Mensaje de Error",
                    ratio=3,
                    style=self.COLORS["subtext0"],
                )
                fail_table.add_column(
                    "Ocurrencias",
                    justify="right",
                    ratio=1,
                    style=f"bold {self.COLORS['text']}",
                )
                for err, count in rows_fail:
                    fail_table.add_row(
                        f"[dim]{err[:80]}{'...' if len(err) > 80 else ''}[/]",
                        f"[bold]{count}[/]",
                    )
                self.console.print(
                    Panel(
                        fail_table,
                        border_style=self.COLORS["red"],
                        title=f"[bold {self.COLORS['text']}]ALERTA DE SISTEMA[/]",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        f"[bold {self.COLORS['green']}]✨ ¡Felicidades! Ingesta completada con 0 errores críticos.[/]",
                        border_style=self.COLORS["green"],
                        padding=(1, 2),
                    )
                )

        self.console.print("\n")
        self.console.print(Rule(style=self.COLORS["mauve"]))
        self.console.print("\n")
