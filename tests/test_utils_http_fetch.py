"""Focused HTTP utility tests for utils."""

import gzip
import io
import ssl

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


def test_ssl_defaults_remain_verified():
    assert ssl._create_default_https_context is not ssl._create_unverified_context


def test_create_ssl_context_is_verified_by_default():
    context = utils._create_ssl_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    if hasattr(context, "minimum_version") and hasattr(ssl, "TLSVersion"):
        assert context.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_gethtml_only_uses_unverified_context_when_requested(monkeypatch):
    calls = []

    class ContextAwareResponse(FakeResponse):
        pass

    def fake_urlopen(req, timeout=30, context=None):
        calls.append(context)
        return ContextAwareResponse(
            b"<html>ok</html>",
            headers={"content-type": "text/html; charset=utf-8"},
        )

    monkeypatch.setattr(utils, "urlopen", fake_urlopen)

    result = utils._getHtml("https://example.com")
    assert result == "<html>ok</html>"
    assert calls[-1] is None

    result = utils._getHtml(
        "https://example.com", ignoreCertificateErrors=True
    )
    assert result == "<html>ok</html>"
    assert calls[-1] is not None
    assert calls[-1].verify_mode == ssl.CERT_NONE
    assert calls[-1].check_hostname is False
