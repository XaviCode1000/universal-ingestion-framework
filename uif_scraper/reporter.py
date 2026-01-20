from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich.console import Console
from uif_scraper.db_manager import StateManager


class ReporterService:
    def __init__(self, console: Console, state_manager: StateManager):
        self.console = console
        self.state = state_manager

    async def generate_summary(self) -> None:
        self.console.print("\n")
        self.console.print(
            Rule(title="[bold blue]🚀 INGESTIÓN FINALIZADA[/]", style="blue")
        )
        self.console.print("\n")

        async with self.state.pool.acquire() as db:
            cursor = await db.execute(
                "SELECT status, COUNT(*) as count FROM urls GROUP BY status"
            )
            rows = await cursor.fetchall()

            if rows:
                status_table = Table(
                    title="[bold cyan]📊 Resumen de Ejecución[/]",
                    box=None,
                    header_style="bold magenta",
                    expand=False,
                )
                status_table.add_column("Estado", justify="left")
                status_table.add_column("Cantidad", justify="right", style="bold")

                total = 0
                for status_val, count in rows:
                    total += count
                    color = "green" if status_val == "completed" else "yellow"
                    if status_val == "failed":
                        color = "red"
                    icon = "✅" if status_val == "completed" else "⏳"
                    if status_val == "failed":
                        icon = "❌"
                    status_table.add_row(
                        f"{icon} {status_val.capitalize()}", str(count), style=color
                    )

                status_table.add_section()
                status_table.add_row("Total Procesado", str(total), style="bold blue")
                self.console.print(status_table)

            self.console.print("\n")
            cursor_fail = await db.execute(
                "SELECT COALESCE(last_error, 'Unknown') as error, COUNT(*) as count FROM urls WHERE status='failed' GROUP BY last_error ORDER BY count DESC LIMIT 5"
            )
            rows_fail = await cursor_fail.fetchall()

            if rows_fail:
                fail_table = Table(
                    title="[bold red]⚠️ Diagnóstico de Errores (Top 5)[/]",
                    box=None,
                    header_style="bold red",
                    expand=True,
                    border_style="red",
                )
                fail_table.add_column("Mensaje de Error", ratio=3)
                fail_table.add_column("Ocurrencias", justify="right", ratio=1)
                for err, count in rows_fail:
                    fail_table.add_row(f"[dim]{err}[/]", f"[bold]{count}[/]")
                self.console.print(
                    Panel(
                        fail_table,
                        border_style="red",
                        title="[bold white]ALERTA DE SISTEMA[/]",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        "[bold green]✨ ¡Felicidades! Ingesta completada con 0 errores críticos.[/]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )

        self.console.print("\n")
        self.console.print(Rule(style="blue"))
        self.console.print("\n")
