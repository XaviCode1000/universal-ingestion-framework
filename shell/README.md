# Shell Functions

Funciones de shell para UIF Scraper.

## Fish

### Instalación

```bash
# Copiar la función al directorio de funciones de fish
cp scrape.fish ~/.config/fish/functions/

# Recargar fish
source ~/.config/fish/config.fish
```

### Uso

```bash
# Ver ayuda
scrape --help

# Scrapear un sitio
scrape https://example.com

# Con opciones
scrape https://example.com/blog --workers 10 --scope strict --verbose
```

## Bash/Zsh

Si usás bash o zsh, podés crear un alias en tu `.bashrc` o `.zshrc`:

```bash
alias scrape='uv run --directory ~/Dev/my_apps/universal-ingestion-framework uif-scraper'
```
