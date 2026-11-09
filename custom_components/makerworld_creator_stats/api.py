"""Bambu API access with fixed destinations and sanitized errors."""

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import BASE_URL, BOOSTS, EMAIL_CODE, LOGIN, POINTS, PROFILE


class ApiError(Exception):
    """An API request failed. Never include response bodies or credentials."""


class AuthError(ApiError):
    """The access token has expired or was rejected."""


class CodeError(ApiError):
    """The email code was rejected or expired."""


class MakerWorldApi:
    """Read account statistics and authenticate through email verification."""

    def __init__(self, session: ClientSession, token: str = "") -> None:
        self.session = session
        self.token = token

    async def _request(self, path: str, payload: dict | None = None) -> dict:
        if path not in (EMAIL_CODE, LOGIN, PROFILE, POINTS, BOOSTS):
            raise ApiError("Unsupported endpoint")
        if (payload is not None) != (path in (EMAIL_CODE, LOGIN)):
            raise ApiError("Unsupported request method")
        headers = {
            "Accept": "application/json",
            "User-Agent": "bambu_network_agent/01.09.05.01",
            "X-BBL-Client-Name": "OrcaSlicer",
            "X-BBL-Client-Type": "slicer",
            "X-BBL-Client-Version": "01.09.05.51",
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
                if response.status == 429:
                    raise ApiError("Request limit reached. Try again later")
                if not 200 <= response.status < 300:
                    raise ApiError(f"Bambu returned HTTP {response.status}")
                if response.status == 204 and path == EMAIL_CODE:
                    return {}
                data = await response.json()
        except (ClientError, TimeoutError, ValueError):
            raise ApiError("Connection or response error") from None
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
        except AuthError:
            raise
        except ApiError:
            # Fresh missing values replace old values on a partial failure.
            return {}
