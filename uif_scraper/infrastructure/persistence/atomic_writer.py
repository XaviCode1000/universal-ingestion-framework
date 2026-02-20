"""Atomic Writer - Persistencia asíncrona con buffering y validación de esquemas.

Este módulo implementa un writer robusto que:
1. Usa un buffer intermedio para optimizar I/O
2. Valida datos contra esquemas Pydantic antes de escribir
3. Maneja escritura atómica (write → flush → rename)
4. Separa items válidos de inválidos (failed_items.jsonl)

Uso:
    from uif_scraper.infrastructure.persistence import DataWriter, ScrapedItem

    writer = DataWriter(
        output_dir=Path("data/mysite"),
        format="jsonl",
        buffer_size=100,  # Escribir cada 100 items
        flush_interval=5.0,  # O cada 5 segundos
    )

    # Como async context manager
    async with writer:
        item = ScrapedItem(url="https://...", title="...", content="...")
        await writer.write(item)
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from pydantic import BaseModel, Field, ValidationError

from uif_scraper.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ESQUEMAS PYDANTIC
# ═══════════════════════════════════════════════════════════════════════════════


class ScrapedItem(BaseModel):
    """Esquema base para un item extraído.

    Todos los scrapers deben producir datos que cumplan este esquema.
    """

    model_config = {"frozen": True}

    url: str = Field(..., description="URL fuente del contenido")
    title: str | None = Field(default=None, description="Título extraído")
    content: str = Field(..., description="Contenido en markdown")
    content_type: str = Field(default="text", description="Tipo de contenido")
    domain: str = Field(..., description="Dominio origen")
    extracted_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FailedItem(BaseModel):
    """Esquema para items que fallaron la validación."""

    model_config = {"frozen": True}

    original_data: dict[str, Any] = Field(..., description="Datos originales")
    validation_error: str = Field(..., description="Error de validación")
    failed_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════════
# EVENTOS PARA LA TUI
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DataSavedEvent:
    """Evento emitido cuando un bloque de datos se persiste."""

    count: int  # Cantidad de items escritos
    filename: str  # Nombre del archivo
    size_bytes: int  # Tamaño del archivo
    format: str  # jsonl, csv, parquet


# ═══════════════════════════════════════════════════════════════════════════════
# PERSISTENCE WORKER
# ═══════════════════════════════════════════════════════════════════════════════


class DataWriter:
    """Writer asíncrono con buffering y validación de esquemas.

    Características:
    - Buffering: Escribe en bloques de N items o cada T segundos
    - Validación: Verifica esquema Pydantic antes de escribir
    - atomicidad: Escribe a .tmp y renombra a destino final
    - Manejo de errores: Items inválidos van a failed_items.jsonl

    Args:
        output_dir: Directorio de salida
        format: Formato de salida (jsonl, csv, parquet)
        buffer_size: Cantidad de items antes de flush
        flush_interval: Segundos máximos entre flush
        schema: Clase Pydantic para validación
        on_flush: Callback opcional cuando se flush
    """

    def __init__(
        self,
        output_dir: Path,
        format: str = "jsonl",
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        schema: type[BaseModel] = ScrapedItem,
        on_flush: Any = None,
    ) -> None:
        self.output_dir = output_dir
        self.format = format.lower()
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.schema = schema
        self._on_flush = on_flush

        # Buffer de items pendientes
        self._buffer: deque[dict[str, Any]] = deque()
        self._failed_buffer: deque[dict[str, Any]] = deque()

        # Estado
        self._closed = False
        self._flush_task: asyncio.Task[None] | None = None
        self._last_flush_time: float = time.time()

        # Archivos
        self._main_file: Path | None = None
        self._failed_file: Path | None = None
        self._total_written: int = 0

    async def __aenter__(self) -> "DataWriter":
        """Inicializa el writer."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de salida
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._main_file = self.output_dir / f"scraped_{timestamp}.{self.format}"
        self._failed_file = self.output_dir / f"failed_{timestamp}.jsonl"

        # Iniciar tarea de flush periódico
        self._flush_task = asyncio.create_task(self._periodic_flush())

        logger.info(f"DataWriter initialized: {self._main_file}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Finaliza el writer haciendo flush final."""
        await self.close()

    async def write(self, data: dict[str, Any] | BaseModel) -> bool:
        """Escribe un item al buffer (validando contra el esquema).

        Args:
            data: Diccionario o modelo Pydantic

        Returns:
            True si se agregó al buffer, False si falló validación
        """
        if self._closed:
            raise RuntimeError("Writer is closed")

        # Convertir a dict si es Pydantic
        if isinstance(data, BaseModel):
            data_dict = data.model_dump()
        else:
            data_dict = dict(data)

        # Validar contra esquema
        try:
            validated = self.schema(**data_dict)
            self._buffer.append(validated.model_dump())
        except ValidationError as e:
            # Item inválido: guardar en failed
            failed_item = FailedItem(
                original_data=data_dict,
                validation_error=str(e),
            )
            self._failed_buffer.append(failed_item.model_dump())
            logger.warning(f"Item validation failed: {e}")
            return False

        # Flush si buffer lleno
        if len(self._buffer) >= self.buffer_size:
            await self.flush()

        return True

    async def flush(self) -> None:
        """Fuerza escritura del buffer a disco."""
        if not self._buffer and not self._failed_buffer:
            return

        now = time.time()

        # Escribir items válidos
        if self._buffer:
            await self._write_atomic(
                self._main_file,
                self._buffer,
            )
            self._total_written += len(self._buffer)
            count = len(self._buffer)
            self._buffer.clear()

            # Notificar evento
            if self._on_flush:
                size = self._main_file.stat().st_size if self._main_file.exists() else 0
                event = DataSavedEvent(
                    count=count,
                    filename=self._main_file.name,
                    size_bytes=size,
                    format=self.format,
                )
                self._on_flush(event)

        # Escribir items fallidos
        if self._failed_buffer:
            await self._write_atomic(
                self._failed_file,
                self._failed_buffer,
            )
            self._failed_buffer.clear()

        self._last_flush_time = now
        logger.debug(f"Flushed to {self._main_file}")

    async def _write_atomic(
        self,
        path: Path,
        data: deque[dict[str, Any]],
    ) -> None:
        """Escribe datos de forma atómica.

        Proceso:
        1. Escribe a archivo .tmp
        2. Flush del SO
        3. Renombra a destino final
        """
        if not data:
            return

        tmp_path = path.with_suffix(path.suffix + ".tmp")

        try:
            # Escribir a archivo temporal
            async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
                if self.format == "jsonl":
                    for item in data:
                        line = json.dumps(item, ensure_ascii=False, default=str)
                        await f.write(line + "\n")

            # Forzar escritura del SO
            await f.sync()

            # Renombrar atómicamente
            tmp_path.replace(path)

        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            # Limpiar archivo temporal si existe
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    async def _periodic_flush(self) -> None:
        """Tarea de flush periódico."""
        while not self._closed:
            await asyncio.sleep(1.0)

            if self._closed:
                break

            # Verificar si pasó el tiempo desde el último flush
            elapsed = time.time() - self._last_flush_time
            if elapsed >= self.flush_interval and (self._buffer or self._failed_buffer):
                await self.flush()

    async def close(self) -> None:
        """Cierra el writer haciendo flush final."""
        if self._closed:
            return

        self._closed = True

        # Cancelar tarea periódica
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush final
        await self.flush()

        logger.info(f"DataWriter closed. Total written: {self._total_written}")

    @property
    def stats(self) -> dict[str, Any]:
        """Retorna estadísticas del writer."""
        return {
            "total_written": self._total_written,
            "buffered": len(self._buffer),
            "failed_buffered": len(self._failed_buffer),
            "output_file": str(self._main_file),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════


__all__ = [
    "DataWriter",
    "ScrapedItem",
    "FailedItem",
    "DataSavedEvent",
]
