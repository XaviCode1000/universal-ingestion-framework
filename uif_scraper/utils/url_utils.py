import re
import unicodedata
from urllib.parse import (
    urlparse,
    urlunparse,
    quote,
    unquote,
    parse_qsl,
    urlencode,
    quote_plus,
)


def slugify(value: str) -> str:
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def smart_url_normalize(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    clean_path = quote(unquote(parsed.path), safe="/")
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    clean_query = urlencode(query_params, quote_via=quote_plus)

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
