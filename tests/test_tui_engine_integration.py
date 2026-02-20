"""Tests para los métodos de configuración y logs del EngineCore.

Tests para:
- get_config()
- update_config()
- get_logs()
- get_queue_status()
- get_error_list()
"""

import pytest
from unittest.mock import MagicMock

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore


@pytest.fixture
def mock_engine(tmp_path):
    """Crear un EngineCore con mocks mínimos para testing."""
    config = ScraperConfig(
        data_dir=tmp_path,
        default_workers=2,
        request_delay=1.0,  # 1000ms
        timeout_seconds=30,
    )

    # Crear mocks para todos los servicios requeridos
    state = MagicMock()
    text_extractor = MagicMock()
    metadata_extractor = MagicMock()
    asset_extractor = MagicMock()
    navigation_service = MagicMock()
    reporter_service = MagicMock()

    engine = EngineCore(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=navigation_service,
        reporter_service=reporter_service,
    )

    return engine


class TestGetConfig:
    """Tests para get_config()."""

    def test_get_config_default(self, mock_engine):
        """get_config retorna valores por defecto."""
        config = mock_engine.get_config()

        assert "workers" in config
        assert "request_delay" in config
        assert "timeout" in config
        assert "mode" in config

    def test_get_config_request_delay_conversion(self, mock_engine):
        """get_config convierte request_delay de segundos a ms."""
        config = mock_engine.get_config()

        # request_delay en config es 1.0 segundos = 1000ms
        assert config["request_delay"] == 1000

    def test_get_config_mode_stealth(self, mock_engine):
        """get_config retorna stealth por defecto."""
        config = mock_engine.get_config()
        assert config["mode"] == "stealth"

    def test_get_config_mode_browser(self, mock_engine):
        """get_config retorna browser cuando está en modo browser."""
        mock_engine.use_browser_mode = True
        config = mock_engine.get_config()
        assert config["mode"] == "browser"


class TestUpdateConfig:
    """Tests para update_config()."""

    def test_update_config_workers(self, mock_engine):
        """update_config puede cambiar workers."""
        result = mock_engine.update_config(workers=5)

        # Verificar que se actualizó
        assert result["workers"] == 5

    def test_update_config_workers_invalid(self, mock_engine):
        """update_config rechaza workers fuera de rango."""
        # Workers = 0 es inválido
        result = mock_engine.update_config(workers=0)
        assert result["workers"] != 0  # No debería cambiar

        # Workers = 11 es inválido
        result = mock_engine.update_config(workers=11)
        assert result["workers"] != 11  # No debería cambiar

    def test_update_config_request_delay(self, mock_engine):
        """update_config puede cambiar request_delay."""
        result = mock_engine.update_config(request_delay=500)

        # Verificar que se convirtió a segundos (0.5)
        assert mock_engine.config.request_delay == 0.5

    def test_update_config_timeout(self, mock_engine):
        """update_config puede cambiar timeout."""
        result = mock_engine.update_config(timeout=60)

        assert mock_engine.config.timeout_seconds == 60

    def test_update_config_timeout_invalid(self, mock_engine):
        """update_config rechaza timeout menor a 5."""
        mock_engine.update_config(timeout=60)
        mock_engine.update_config(timeout=3)

        # No debería cambiar a un valor menor a 5
        assert mock_engine.config.timeout_seconds >= 5

    def test_update_config_mode_stealth(self, mock_engine):
        """update_config puede cambiar a modo stealth."""
        mock_engine.use_browser_mode = True
        mock_engine.update_config(mode="stealth")

        assert mock_engine.use_browser_mode is False

    def test_update_config_mode_browser(self, mock_engine):
        """update_config puede cambiar a modo browser."""
        mock_engine.update_config(mode="browser")

        assert mock_engine.use_browser_mode is True

    def test_update_config_multiple(self, mock_engine):
        """update_config puede cambiar múltiples valores."""
        result = mock_engine.update_config(
            workers=8,
            request_delay=200,
            timeout=45,
            mode="browser",
        )

        assert result["workers"] == 8
        assert mock_engine.config.request_delay == 0.2
        assert mock_engine.config.timeout_seconds == 45
        assert mock_engine.use_browser_mode is True


class TestGetLogs:
    """Tests para get_logs()."""

    def test_get_logs_empty(self, mock_engine):
        """get_logs retorna lista vacía si no hay activity."""
        logs = mock_engine.get_logs()
        assert logs == []

    def test_get_logs_from_activity(self, mock_engine):
        """get_logs retorna logs del activity_log."""
        # Agregar entries al activity_log
        mock_engine.activity_log = [
            {
                "url": "https://example.com/1",
                "title": "Page 1",
                "status": "success",
                "time": 1000.0,
                "engine": "trafilatura",
            },
            {
                "url": "https://example.com/2",
                "title": "Page 2",
                "status": "error",
                "error": "Timeout",
                "time": 1001.0,
                "engine": "worker-1",
            },
            {
                "url": "https://example.com/3",
                "title": "Page 3",
                "status": "warning",
                "time": 1002.0,
                "engine": "worker-2",
            },
        ]

        logs = mock_engine.get_logs()

        assert len(logs) == 3

    def test_get_logs_filter_by_level(self, mock_engine):
        """get_logs puede filtrar por nivel."""
        mock_engine.activity_log = [
            {
                "url": "https://example.com/1",
                "status": "success",
                "time": 1000.0,
                "engine": "trafilatura",
            },
            {
                "url": "https://example.com/2",
                "status": "error",
                "error": "Timeout",
                "time": 1001.0,
                "engine": "worker-1",
            },
            {
                "url": "https://example.com/3",
                "status": "warning",
                "time": 1002.0,
                "engine": "worker-2",
            },
        ]

        # Filtrar solo errors
        logs = mock_engine.get_logs(level="ERROR")
        assert all(log["level"] == "ERROR" for log in logs)

    def test_get_logs_limit(self, mock_engine):
        """get_logs respeta el límite de entradas."""
        # Crear muchas entradas
        mock_engine.activity_log = [
            {
                "url": f"https://example.com/{i}",
                "status": "success",
                "time": 1000.0 + i,
                "engine": "test",
            }
            for i in range(150)
        ]

        logs = mock_engine.get_logs(limit=50)

        assert len(logs) == 50


class TestGetQueueStatus:
    """Tests para get_queue_status()."""

    def test_get_queue_status_empty(self, mock_engine):
        """get_queue_status retorna lista vacía si no hay URLs."""
        status = mock_engine.get_queue_status()
        assert status == []


class TestGetErrorList:
    """Tests para get_error_list()."""

    def test_get_error_list_empty(self, mock_engine):
        """get_error_list retorna lista vacía si no hay errores."""
        errors = mock_engine.get_error_list()
        assert errors == []

    def test_get_error_list_from_activity(self, mock_engine):
        """get_error_list retorna errores del activity_log."""
        mock_engine.activity_log = [
            {"url": "https://example.com/1", "status": "success", "time": 1000.0},
            {
                "url": "https://example.com/2",
                "status": "error",
                "error": "Timeout error",
                "time": 1001.0,
            },
        ]

        errors = mock_engine.get_error_list()

        assert len(errors) == 1
        assert errors[0]["url"] == "https://example.com/2"
        assert errors[0]["error_type"] == "ProcessingError"
