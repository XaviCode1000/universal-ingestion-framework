"""
Sparkline Widget - Mini-gráfico de tendencia con ejes.

Un sparkline es un gráfico compacto de una sola línea que muestra
tendencia sin necesidad de ejes completos. Esta versión incluye
eje Y simplificado (máximo) y eje X implícito (tiempo).
"""

from typing import Any

from textual.reactive import reactive
from textual.widgets import Static


class Sparkline(Static):
    """Mini-gráfico de tendencia en una línea con eje Y.

    Ejemplo de render:
        4.2 ┤ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃
            └──────────────────────────────────
                  last 60s
    """

    # CSS movido a mocha.tcss para usar variables

    # Caracteres para diferentes alturas (8 niveles)
    CHARS = " ▁▂▃▄▅▆▇█"

    # Reactive props
    values: reactive[list[float]] = reactive(list)
    max_value: reactive[float] = reactive(0.0)
    label: reactive[str] = reactive("Speed")
    unit: reactive[str] = reactive("p/s")
    show_axis: reactive[bool] = reactive(True)

    def __init__(
        self,
        values: list[float] | None = None,
        label: str = "Speed",
        unit: str = "p/s",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if values:
            self.values = values
        self.label = label
        self.unit = unit

    def render(self) -> str:
        """Renderiza el sparkline con eje Y."""
        if not self.values:
            return self._render_empty()

        # Calcular máximo
        max_val = (
            self.max_value
            if self.max_value > 0
            else max(self.values)
            if self.values
            else 1
        )

        # Normalizar valores a índices de caracteres
        normalized = []
        for v in self.values:
            if max_val > 0:
                ratio = min(v / max_val, 1.0)
                idx = int(ratio * (len(self.CHARS) - 1))
                normalized.append(self.CHARS[idx])
            else:
                normalized.append(self.CHARS[0])

        chart = "".join(normalized)

        if self.show_axis:
            # Formatear eje Y
            axis_label = f"{max_val:.1f}"
            return f"{axis_label:>5} ┤ [{self._get_chart_color()}]{chart}[/]\n     └{'─' * len(chart)}\n     {self.label} (last 60s)"
        else:
            return f"[{self._get_chart_color()}]{chart}[/]"

    def _render_empty(self) -> str:
        """Renderiza estado vacío."""
        if self.show_axis:
            return (
                f"  0.0 ┤ {'─' * 40}\n      └{'─' * 40}\n      {self.label} (no data)"
            )
        return "─" * 40

    def _get_chart_color(self) -> str:
        """Obtiene color del chart según tendencia."""
        if len(self.values) < 2:
            return "mauve"

        # Calcular tendencia simple (últimos 10 vs anteriores)
        recent = self.values[-10:] if len(self.values) >= 10 else self.values
        older = (
            self.values[-20:-10]
            if len(self.values) >= 20
            else self.values[: len(self.values) // 2]
        )

        if not older:
            return "mauve"

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg * 1.1:
            return "green"  # Subiendo
        elif recent_avg < older_avg * 0.9:
            return "red"  # Bajando
        return "mauve"  # Estable

    def add_value(self, value: float) -> None:
        """Agrega un valor al final, mantiene máximo 60."""
        new_values = list(self.values) + [value]
        # Mantener solo los últimos 60
        if len(new_values) > 60:
            new_values = new_values[-60:]
        self.values = new_values

    def clear(self) -> None:
        """Limpia todos los valores."""
        self.values = []
        self.max_value = 0.0


class MultiSparkline(Static):
    """Múltiples sparklines apilados para comparación.

    Ejemplo:
        Pages ┤ ▁▂▃▄▅▆▇█▇▆▅▄
        Assets┤ ▄▅▆▇█▇▆▅▄▃▂▁
    """

    # CSS movido a mocha.tcss para usar variables

    # Reactive props
    datasets: reactive[dict[str, list[float]]] = reactive(dict)
    line_colors: reactive[dict[str, str]] = reactive(dict)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._default_colors = {
            "pages": "cyan",
            "assets": "magenta",
            "errors": "red",
            "speed": "green",
        }

    def render(self) -> str:
        """Renderiza múltiples sparklines."""
        if not self.datasets:
            return "[dim]No data[/]"

        lines = []
        for name, values in self.datasets.items():
            if not values:
                continue

            max_val = max(values) if values else 1
            color = self.line_colors.get(name, self._default_colors.get(name, "white"))

            # Normalizar
            chart = self._normalize(values, max_val)

            # Formatear línea
            label = f"{name[:6]:>6}"
            lines.append(f"{label} ┤ [{color}]{chart}[/]")

        return "\n".join(lines)

    def _normalize(self, values: list[float], max_val: float) -> str:
        """Normaliza valores a caracteres sparkline."""
        chars = " ▁▂▃▄▅▆▇█"
        normalized = []
        for v in values[-50:]:  # Máximo 50 caracteres
            if max_val > 0:
                ratio = min(v / max_val, 1.0)
                idx = int(ratio * (len(chars) - 1))
                normalized.append(chars[idx])
            else:
                normalized.append(chars[0])
        return "".join(normalized)

    def add_value(self, dataset: str, value: float) -> None:
        """Agrega un valor a un dataset específico."""
        new_datasets = dict(self.datasets)
        if dataset not in new_datasets:
            new_datasets[dataset] = []
        new_datasets[dataset] = (new_datasets[dataset] + [value])[-60:]
        self.datasets = new_datasets


__all__ = ["Sparkline", "MultiSparkline"]
