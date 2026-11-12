"""Classify failures without retaining server bodies or credentials."""

import json
import time

from .backoff import retry_after_seconds


class ApiError(Exception):
    """A safe, locally generated error message."""

    def __init__(self, message, *, retry_after=0):
        super().__init__(message)
        self.retry_after = retry_after


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
            f"{endpoint}: Rate limit reached (HTTP 429). Try again later.",
            retry_after=retry_after_seconds(headers.get("retry-after"), time.time()),
        )
    if cloudflare:
        return CloudflareError(
            f"{endpoint}: Cloudflare challenge or access restriction detected "
            "(HTTP 403). Try again later; this does not imply an incorrect password.",
            retry_after=retry_after_seconds(headers.get("retry-after"), time.time()),
        )
    try:
        data = json.loads(text)
    except (ValueError, TypeError, RecursionError):
        data = None
    if isinstance(data, dict) and (
        data.get("reason") == "missing_cookie"
        or data.get("error") == "csrf error: missing_cookie"
    ):
        return ApiError(f"{endpoint}: Bambu Lab requires a CSRF cookie (HTTP 403).")
    return ApiError(
        f"{endpoint}: Access denied by Bambu Lab (HTTP 403). "
        "The cause is unknown; neither a Cloudflare challenge nor an authentication error is confirmed."
    )
