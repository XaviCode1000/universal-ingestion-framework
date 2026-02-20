from urllib.parse import (
    urlparse,
    urlunparse,
    quote,
    unquote,
    parse_qsl,
    urlencode,
    quote_plus,
)

from slugify import slugify as python_slugify


def slugify(value: str) -> str:
    """Sanitiza string para nombre de archivo seguro.

    Usa python-slugify para manejo robusto de Unicode y edge cases.
    Ejemplos:
        "Español" → "espanol"
        "Mi Blog" → "mi-blog"
        "archivo.php" → "archivo-php"
    """
    return python_slugify(value)


def smart_url_normalize(url: str, force_https: bool = False) -> str:
    """Normaliza URL con encoding consistente y opcionalmente fuerza HTTPS.

    Args:
        url: URL a normalizar
        force_https: Si True, convierte http:// a https://

    Returns:
        URL normalizada
    """
    if not url:
        return ""

    parsed = urlparse(url)
    clean_path = quote(unquote(parsed.path), safe="/")
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    clean_query = urlencode(query_params, quote_via=quote_plus)

    # Forzar HTTPS si se solicita
    scheme = "https" if force_https and parsed.scheme == "http" else parsed.scheme

    clean_url = urlunparse(
        (
            scheme,
            parsed.netloc,
            clean_path,
            parsed.params,
            clean_query,
            parsed.fragment,
        )
    )

    return clean_url
