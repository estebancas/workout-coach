import json
from pathlib import Path

import httpx
import keyring

BASE_URL = "https://pr4mathletics.truecoach.co"
API = "/proxy/api"
KEYRING_SERVICE = "workout-coach"
TOKEN_CACHE = Path.home() / ".cache" / "workout-coach" / "token.json"


class AuthError(Exception):
    pass


def save_credentials(email: str, password: str) -> None:
    keyring.set_password(KEYRING_SERVICE, "email", email)
    keyring.set_password(KEYRING_SERVICE, "password", password)


def load_credentials() -> tuple[str, str]:
    email = keyring.get_password(KEYRING_SERVICE, "email")
    password = keyring.get_password(KEYRING_SERVICE, "password")
    if not email or not password:
        raise AuthError("No credentials stored. Run `workout-coach auth set` first.")
    return email, password


class TrueCoachClient:
    """HTTP client that logs in lazily and re-logs in once on a 401."""

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        token_cache: Path = TOKEN_CACHE,
    ) -> None:
        self._http = httpx.Client(base_url=BASE_URL, transport=transport, timeout=30)
        self._token_cache = token_cache
        self._token = self._read_cached_token()
        self.logins = 0

    def _read_cached_token(self) -> str | None:
        try:
            return json.loads(self._token_cache.read_text())["access_token"]
        except (OSError, ValueError, KeyError):
            return None

    def _write_cached_token(self, token: str) -> None:
        self._token_cache.parent.mkdir(parents=True, exist_ok=True)
        self._token_cache.write_text(json.dumps({"access_token": token}))
        self._token_cache.chmod(0o600)

    def login(self) -> str:
        email, password = load_credentials()
        response = self._http.post(
            f"{API}/oauth/token",
            data={"grant_type": "password", "username": email, "password": password},
        )
        if response.status_code != 200:
            raise AuthError(f"Login failed with status {response.status_code}.")
        self._token = response.json()["access_token"]
        self._write_cached_token(self._token)
        self.logins += 1
        return self._token

    def _send(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self._token}", "Role": "Client"}
        return self._http.request(method, f"{API}{path}", headers=headers, **kwargs)

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if self._token is None:
            self.login()
        response = self._send(method, path, **kwargs)
        if response.status_code == 401:
            self.login()
            response = self._send(method, path, **kwargs)
            if response.status_code == 401:
                raise AuthError("Still unauthorized after logging in again.")
        response.raise_for_status()
        return response

    def me(self) -> dict:
        return self.request("GET", "/users/me").json()
