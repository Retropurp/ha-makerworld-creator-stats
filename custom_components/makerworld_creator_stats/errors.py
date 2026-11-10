"""Classify failures without retaining server bodies or credentials."""

import json


class ApiError(Exception):
    """A safe, locally generated error message."""


class AuthError(ApiError):
    """The access token has expired or was rejected."""


class CodeError(ApiError):
    """The email code was rejected or expired."""


class CloudflareError(ApiError):
    """A challenge or block page explicitly identifies Cloudflare."""


class RateLimitError(ApiError):
    """The server explicitly reports request throttling."""


def classify_denial(status, headers, body, endpoint):
    """Inspect only a bounded response prefix; never echo untrusted text."""
    # Cloudflare headers alone (Server, CF-Ray) also occur on normal API replies.
    headers = {str(key).lower(): str(value).lower() for key, value in headers.items()}
    text = body[:8192].decode("utf-8", errors="replace").lower()
    challenge = headers.get("cf-mitigated") == "challenge"
    html = "<html" in text or "<!doctype html" in text
    cloudflare = challenge or (html and any(marker in text for marker in (
        "cloudflare", "/cdn-cgi/challenge-platform/", "cf-chl-",
    )))
    # endpoint is supplied by our fixed allowlist, never by the response.
    if status == 429:
        return RateLimitError(
            f"{endpoint}: Anfragebegrenzung (HTTP 429). Später erneut versuchen."
        )
    if cloudflare:
        return CloudflareError(
            f"{endpoint}: Cloudflare-Schutzprüfung oder Zugriffssperre erkannt "
            "(HTTP 403). Später erneut versuchen; ein neues Passwort ist dadurch nicht erforderlich."
        )
    try:
        data = json.loads(text)
    except (ValueError, TypeError, RecursionError):
        data = None
    if isinstance(data, dict) and (
        data.get("reason") == "missing_cookie"
        or data.get("error") == "csrf error: missing_cookie"
    ):
        return ApiError(f"{endpoint}: Bambu verlangt ein CSRF-Cookie (HTTP 403).")
    return ApiError(
        f"{endpoint}: Zugriff von Bambu abgewiesen (HTTP 403). "
        "Ursache nicht eindeutig; keine bestätigte Cloudflare- oder Anmeldediagnose."
    )
