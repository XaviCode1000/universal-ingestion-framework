"""Detección de desafíos de seguridad y anti-scraping."""

from __future__ import annotations

from loguru import logger


class CaptchaDetector:
    """Detecta la presencia de CAPTCHAs y desafíos de seguridad en el HTML.

    Identifica firmas comunes de Cloudflare, reCAPTCHA, hCaptcha, etc.
    """

    # Firmas comunes de desafíos de seguridad
    SIGNATURES = {
        "cloudflare_turnstile": [
            "cf-turnstile-wrapper",
            "challenges.cloudflare.com/turnstile",
        ],
        "cloudflare_iuam": [
            "Checking your browser before accessing",
            "cf-browser-verification",
            'id="cf-content"',
        ],
        "recaptcha": [
            "google.com/recaptcha",
            "g-recaptcha",
            "recaptcha-v3-token",
        ],
        "hcaptcha": [
            "hcaptcha.com",
            "h-captcha",
        ],
        "generic_captcha": [
            "captcha",
            "security challenge",
            "verify you are human",
        ],
    }

    def detect(self, html: str) -> tuple[bool, str | None]:
        """Analiza el HTML en busca de desafíos de seguridad.

        Args:
            html: Contenido HTML a analizar

        Returns:
            Tuple con (bool: detectado, str: tipo de desafío o None)
        """
        if not html:
            return False, None

        html_lower = html.lower()

        for challenge_type, markers in self.SIGNATURES.items():
            for marker in markers:
                if marker.lower() in html_lower:
                    logger.warning(
                        f"Detección de anti-scraping: {challenge_type} (marcador: {marker})"
                    )
                    return True, challenge_type

        return False, None
