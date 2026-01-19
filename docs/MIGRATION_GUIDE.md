# Guía de Migración: Argelia Scraper v2.2 -> v3.0

Esta versión introduce cambios arquitectónicos significativos para mejorar la escalabilidad y mantenibilidad.

## Cambios Principales

1. **Estructura Modular**: El código ya no es un solo archivo. Ahora es un paquete Python (`argelia_scraper`).
2. **Sistema de Configuración**: Se usa `ScraperConfig` con soporte para archivos YAML y variables de entorno.
3. **Persistencia**: SQLite ahora usa un pool de conexiones y modo WAL.
4. **CLI**: Nuevo comando `argelia-scraper`.

## Pasos para Migrar

1. **Instalar Dependencias**:
   ```bash
   uv sync
   ```

2. **Configuración Inicial**:
   Ejecuta el wizard para crear tu archivo de configuración:
   ```bash
   argelia-scraper --setup
   ```

3. **Actualizar Scripts**:
   Si tenías scripts que llamaban a `engine.py`, ahora puedes usar `argelia-scraper` directamente.

   **Antes:**
   ```bash
   python engine.py https://ejemplo.com --workers 10
   ```

   **Después:**
   ```bash
   argelia-scraper https://ejemplo.com --workers 10
   ```

4. **Variables de Entorno**:
   Puedes configurar el directorio de datos globalmente:
   ```bash
   export SCRAPER_DATA_DIR=/ruta/a/datos
   ```
