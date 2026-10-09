import httpx
import pytest

from workout_coach import truecoach
from workout_coach.truecoach import AuthError, TrueCoachClient


@pytest.fixture(autouse=True)
def fake_keyring(monkeypatch):
    store = {"email": "a@b.c", "password": "pw"}
    monkeypatch.setattr(
        truecoach.keyring, "get_password", lambda service, key: store.get(key)
    )


def make_client(tmp_path, handler):
    return TrueCoachClient(
        transport=httpx.MockTransport(handler), token_cache=tmp_path / "token.json"
    )


def test_login_then_request_sends_both_headers(tmp_path):
    seen = []

    def handler(request):
        seen.append(request)
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(200, json={"ok": True})

    client = make_client(tmp_path, handler)
    assert client.request("GET", "/users/me").json() == {"ok": True}
    assert seen[-1].headers["Authorization"] == "Bearer tok"
    assert seen[-1].headers["Role"] == "Client"
    assert (tmp_path / "token.json").exists()


def test_revoked_token_triggers_exactly_one_relogin(tmp_path):
    (tmp_path / "token.json").write_text('{"access_token": "old"}')

    def handler(request):
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "new"})
        if request.headers["Authorization"] == "Bearer old":
            return httpx.Response(401)
        return httpx.Response(200, json={"ok": True})

    client = make_client(tmp_path, handler)
    assert client.request("GET", "/users/me").status_code == 200
    assert client.logins == 1


def test_persistent_401_fails_after_one_relogin(tmp_path):
    def handler(request):
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json={"access_token": "t"})
        return httpx.Response(401)

    client = make_client(tmp_path, handler)
    with pytest.raises(AuthError):
        client.request("GET", "/users/me")
    assert client.logins == 2  # initial lazy login + exactly one retry


def test_failed_login_raises(tmp_path):
    client = make_client(tmp_path, lambda r: httpx.Response(400))
    with pytest.raises(AuthError):
        client.login()
