"""Tests for FlareSolverr manager."""

import types


from resources.lib import flaresolverr
from resources.lib.flaresolverr import FlareSolverrManager


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self._payload


def test_init_clears_old_sessions(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append((url, json, timeout))
        cmd = (json or {}).get("cmd")
        if cmd == "sessions.list":
            return _FakeResponse(
                {"sessions": ["cumination_session_old", "other_session"]}
            )
        if cmd == "sessions.destroy":
            return _FakeResponse({"status": "ok"})
        if cmd == "sessions.create":
            return _FakeResponse({"status": "ok", "session": "cumination_session_new"})
        return _FakeResponse({})

    class _FakeSession:
        def post(self, *args, **kwargs):
            return _FakeResponse({"status": "ok"})

    monkeypatch.setattr(flaresolverr.requests, "post", fake_post)
    monkeypatch.setattr(
        flaresolverr.requests, "session", lambda: _FakeSession(), raising=False
    )
    monkeypatch.setattr(
        flaresolverr.requests,
        "exceptions",
        types.SimpleNamespace(Timeout=TimeoutError, ConnectionError=ConnectionError),
        raising=False,
    )

    manager = FlareSolverrManager(
        flaresolverr_url="http://fake:8191/v1", session_id="cumination_session_new"
    )

    assert manager.flaresolverr_session == "cumination_session_new"
    destroy_calls = [call for call in calls if call[1].get("cmd") == "sessions.destroy"]
    assert destroy_calls


def test_request_retries_on_timeout(monkeypatch):
    calls = []

    class _FakeSession:
        def __init__(self):
            self.fail_once = True

        def post(self, url, json=None, timeout=None):
            calls.append((url, json, timeout))
            if self.fail_once:
                self.fail_once = False
                raise TimeoutError("timeout")
            return _FakeResponse({"status": "ok", "solution": {"response": "ok"}})

    def fake_post(url, json=None, timeout=None):
        if json and json.get("cmd") == "sessions.list":
            return _FakeResponse({"sessions": []})
        if json and json.get("cmd") == "sessions.create":
            return _FakeResponse({"status": "ok", "session": "cumination_session_new"})
        if json and json.get("cmd") == "sessions.destroy":
            return _FakeResponse({"status": "ok"})
        return _FakeResponse({})

    monkeypatch.setattr(flaresolverr.requests, "post", fake_post)
    monkeypatch.setattr(
        flaresolverr.requests, "session", lambda: _FakeSession(), raising=False
    )
    monkeypatch.setattr(
        flaresolverr.requests,
        "exceptions",
        types.SimpleNamespace(Timeout=TimeoutError, ConnectionError=ConnectionError),
        raising=False,
    )
    monkeypatch.setattr(flaresolverr.time, "sleep", lambda *a, **k: None)

    manager = FlareSolverrManager(
        flaresolverr_url="http://fake:8191/v1", session_id="cumination_session_new"
    )
    response = manager.request("http://example.com", tries=2, max_timeout=1000)

    assert response.json()["status"] == "ok"
    assert len(calls) == 2


def test_close_can_destroy_session_once(monkeypatch):
    calls = []

    class _FakeSession:
        def post(self, url, json=None, timeout=None):
            return _FakeResponse({"status": "ok", "solution": {"response": "ok"}})

        def close(self):
            calls.append(("session.close", None, None))

    def fake_post(url, json=None, timeout=None):
        calls.append((url, json, timeout))
        if json and json.get("cmd") == "sessions.list":
            return _FakeResponse({"sessions": []})
        if json and json.get("cmd") == "sessions.create":
            return _FakeResponse({"status": "ok", "session": "cumination_session_new"})
        if json and json.get("cmd") == "sessions.destroy":
            return _FakeResponse({"status": "ok"})
        return _FakeResponse({})

    monkeypatch.setattr(flaresolverr.requests, "post", fake_post)
    monkeypatch.setattr(
        flaresolverr.requests, "session", lambda: _FakeSession(), raising=False
    )
    monkeypatch.setattr(
        flaresolverr.requests,
        "exceptions",
        types.SimpleNamespace(Timeout=TimeoutError, ConnectionError=ConnectionError),
        raising=False,
    )

    manager = FlareSolverrManager(
        flaresolverr_url="http://fake:8191/v1", session_id="cumination_session_new"
    )
    manager.close(destroy_session=True)
    manager.close(destroy_session=True)

    destroy_calls = [
        c for c in calls if isinstance(c[1], dict) and c[1].get("cmd") == "sessions.destroy"
    ]
    assert len(destroy_calls) == 1
