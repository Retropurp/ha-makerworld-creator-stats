"""Bambu API access with fixed destinations and sanitized errors."""

from aiohttp import ClientError, ClientSession, ClientTimeout
import asyncio
import json

from .const import BASE_URL, BOOSTS, CLIENT_NAME, CLIENT_VERSION, EMAIL_CODE, LOGIN, POINTS, PROFILE, USER_AGENT
from .transactions import DAY, TransactionError, parse_transaction
from .errors import (
    ApiError, AuthError, CodeError, CloudflareError, RateLimitError, classify_denial,
)

HISTORY_PATH = "/v1/point-service/point-bill/my"


def history_path(offset):
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset < 5000:
        raise ApiError("Invalid history offset")
    return f"{HISTORY_PATH}?offset={offset}&limit=100&filter=all"


class MakerWorldApi:
    """Read account statistics and authenticate through email verification."""

    def __init__(self, session: ClientSession, token: str = "") -> None:
        self.session = session
        self.token = token

    async def _request(self, path: str, payload: dict | None = None) -> dict:
        history_allowed = path in (history_path(offset) for offset in range(0, 5000, 100))
        if path not in (EMAIL_CODE, LOGIN, PROFILE, POINTS, BOOSTS) and not history_allowed:
            raise ApiError("Unsupported endpoint")
        if (payload is not None) != (path in (EMAIL_CODE, LOGIN)):
            raise ApiError("Unsupported request method")
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-BBL-Client-Name": CLIENT_NAME,
            "X-BBL-Client-Type": "homeautomation",
            "X-BBL-Client-Version": CLIENT_VERSION,
            "X-BBL-Language": "en-US",
        }
        if payload is None:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            async with self.session.request(
                "POST" if payload is not None else "GET",
                BASE_URL + path,
                headers=headers,
                json=payload,
                allow_redirects=False,
                timeout=ClientTimeout(total=20),
            ) as response:
                if response.status == 401:
                    raise AuthError("Authentication required")
                if response.status == 400 and path == LOGIN:
                    raise CodeError("Request a new code or check the code")
                if response.status in (403, 429) or response.headers.get("CF-Mitigated", "").lower() == "challenge":
                    labels = {
                        EMAIL_CODE: "Email code request", LOGIN: "Sign-in",
                        PROFILE: "Account profile", POINTS: "Points", BOOSTS: "Boosts",
                    }
                    try:
                        prefix = await response.content.read(8192)
                    except (TimeoutError, ClientError):
                        prefix = b""
                    raise classify_denial(
                        response.status, response.headers, prefix,
                        labels.get(path, "Transaction history"),
                    )
                if not 200 <= response.status < 300:
                    raise ApiError(f"Bambu Lab returned HTTP {response.status}")
                if path == EMAIL_CODE and not (await response.read()).strip():
                    return {}
                data = await response.json(content_type=None)
        except TimeoutError:
            raise ApiError("Request timed out") from None
        except ClientError:
            raise ApiError("Network or TLS error") from None
        except ValueError:
            raise ApiError("Response is not valid JSON") from None
        if not isinstance(data, dict):
            raise ApiError("Unexpected response format")
        if data.get("code") not in (None, 0, "0"):
            raise ApiError("Bambu rejected the request")
        return data

    async def request_code(self, email: str) -> None:
        await self._request(EMAIL_CODE, {"email": email, "type": "codeLogin"})

    async def login(self, email: str, code: str) -> str:
        data = await self._request(LOGIN, {"account": email, "code": code})
        token = data.get("accessToken")
        if not isinstance(token, str) or not token:
            raise CodeError("Email login did not return an access token")
        self.token = token
        return token

    async def profile(self) -> dict:
        data = await self._request(PROFILE)
        uid = data.get("uid")
        if isinstance(uid, bool) or not str(uid).isdigit():
            raise ApiError("Profile response has no account ID")
        return data

    async def optional_stats(self, path: str) -> dict:
        try:
            return await self._request(path)
        except (AuthError, CloudflareError, RateLimitError):
            raise
        except ApiError:
            # Fresh missing values replace old values on a partial failure.
            return {}

    async def read_stats(self, path: str) -> dict:
        """Read one allowlisted optional endpoint, retaining error details.

        Unlike optional_stats(), HTTP errors are surfaced so a denied request
        can trigger a protective pause rather than silently re-polling.
        """
        if path not in (POINTS, BOOSTS):
            raise ApiError("Unsupported statistics endpoint")
        return await self._request(path)

    async def income_history(self, now):
        """Read all pages needed for 30 days, bounded to fifty requests."""
        events = []
        cutoff = now - 30 * DAY
        previous_time = float("inf")
        expected_totals = None
        seen_pages = set()
        for offset in range(0, 5000, 100):
            data = await self._request(history_path(offset))
            rows, count = data.get("hits"), data.get("total")
            if not isinstance(rows, list) or isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise TransactionError("Unexpected history page format")
            totals = (count, data.get("totalIncome"), data.get("totalExpense"))
            if expected_totals is None:
                expected_totals = totals
            if totals != expected_totals:
                raise TransactionError("History changed during import; retry later")
            if not rows and offset < count:
                raise TransactionError("Incomplete history page")
            fingerprint = json.dumps(rows, sort_keys=True)
            if rows and fingerprint in seen_pages:
                raise TransactionError("History pagination repeated a page")
            seen_pages.add(fingerprint)
            for row in rows:
                event = parse_transaction(row)
                if event["time"] > previous_time:
                    raise TransactionError("History is not ordered by time")
                previous_time = event["time"]
                if event["time"] > cutoff:
                    events.append(event)
            if previous_time <= cutoff or offset + len(rows) >= count:
                return events
            if len(rows) != 100:
                raise TransactionError("Unexpected history page size")
            await asyncio.sleep(0.25)
        raise TransactionError("History import exceeded page limit")
