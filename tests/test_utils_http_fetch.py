"""Focused HTTP utility tests for utils."""

import gzip
import io

import pytest

from resources.lib import utils


class FakeResponse:
    def __init__(self, payload, headers=None, code=200):
        self._payload = payload
        self._headers = headers or {}
        self.code = code
        self.headers = self._headers

    def read(self, *args, **kwargs):
        return self._payload

    def info(self):
        return self._headers

    def close(self):
        pass


def test_posthtml_returns_decoded_response(monkeypatch):
    content = b"<html>ok</html>"
    gzipped = io.BytesIO()
    with gzip.GzipFile(fileobj=gzipped, mode="wb") as handle:
        handle.write(content)

    response = FakeResponse(
        gzipped.getvalue(),
        headers={
            "Content-Encoding": "gzip",
            "content-type": "text/html; charset=utf-8",
        },
    )

    monkeypatch.setattr(
        utils.urllib_request, "urlopen", lambda req, timeout=30: response
    )

    result = utils._postHtml("https://example.com", form_data={"a": "b"})

    assert "ok" in result


def test_posthtml_raises_on_404(monkeypatch):
    error_body = b"not found"
    error = utils.urllib_error.HTTPError(
        "https://example.com",
        404,
        "Not Found",
        {"Content-Encoding": ""},
        io.BytesIO(error_body),
    )

    def _raise_error(_req, timeout=30):
        raise error

    monkeypatch.setattr(utils.urllib_request, "urlopen", _raise_error)

    with pytest.raises(utils.urllib_error.HTTPError):
        utils._postHtml("https://example.com", form_data={"a": "b"})


def test_checkurl_and_gethtml2(monkeypatch):
    response = FakeResponse(b"hello", headers={}, code=200)
    monkeypatch.setattr(utils, "urlopen", lambda req, timeout=60: response)

    assert utils.checkUrl("https://example.com") is True
    assert utils._getHtml2("https://example.com") == "hello"


def test_getvideolink_uses_redirect_location(monkeypatch):
    class FakeOpener:
        def open(self, req, timeout=30):
            return FakeResponse(b"", headers={"location": "https://cdn.example.com"})

    monkeypatch.setattr(
        utils.urllib_request, "build_opener", lambda *a, **k: FakeOpener()
    )

    result = utils.getVideoLink("https://example.com/video")
    assert result == "https://cdn.example.com"
