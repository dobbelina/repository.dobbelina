import pytest
from unittest.mock import MagicMock, patch
import io
import gzip
from resources.lib import utils

# Test the real getHtml logic by mocking the underlying urlopen
class TestGetHtmlLogic:
    @patch("resources.lib.utils.urlopen")
    def test_get_html_basic(self, mock_urlopen):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>Test</html>"
        mock_response.info.return_value = {}
        mock_response.geturl.return_value = "http://example.com"
        mock_urlopen.return_value = mock_response
        
        # We need to bypass the cache for this test to actually call _getHtml
        with patch("resources.lib.utils.cache.cacheFunction", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            result = utils.getHtml("http://example.com")
            assert result == "<html>Test</html>"
            assert mock_urlopen.called

    @patch("resources.lib.utils.urlopen")
    def test_get_html_gzip(self, mock_urlopen):
        # Mock gzipped response
        content = b"<html>Gzip Content</html>"
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(content)
        gzipped_content = out.getvalue()
        
        mock_response = MagicMock()
        mock_response.read.return_value = gzipped_content
        mock_response.info.return_value = {"Content-Encoding": "gzip"}
        mock_response.geturl.return_value = "http://example.com"
        mock_urlopen.return_value = mock_response
        
        with patch("resources.lib.utils.cache.cacheFunction", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            result = utils.getHtml("http://example.com")
            assert "Gzip Content" in result

class TestPostHtmlLogic:
    @patch("resources.lib.utils.urllib_request.urlopen")
    def test_post_html_basic(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"POST Success"
        mock_response.info.return_value = {}
        mock_response.geturl.return_value = "http://example.com"
        mock_urlopen.return_value = mock_response
        
        with patch("resources.lib.utils.cache.cacheFunction", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            # Correct argument name is form_data
            result = utils.postHtml("http://example.com", form_data={"key": "value"})
            assert result == "POST Success"
            assert mock_urlopen.called

class TestSucuriCookie:
    @patch("resources.lib.utils.urlopen")
    @patch("resources.lib.utils.get_sucuri_cookie")
    def test_get_html_sucuri_handling(self, mock_get_sucuri, mock_urlopen):
        # Initial response with Sucuri JS
        mock_response1 = MagicMock()
        mock_response1.read.return_value = b"<html>sucuri_cloudproxy_js content</html>"
        mock_response1.info.return_value = {}
        mock_response1.geturl.return_value = "http://example.com"
        
        # Second response after cookie is set
        mock_response2 = MagicMock()
        mock_response2.read.return_value = b"<html>Real Content</html>"
        mock_response2.info.return_value = {}
        mock_response2.geturl.return_value = "http://example.com"
        
        mock_urlopen.side_effect = [mock_response1, mock_response2]
        mock_get_sucuri.return_value = "sucuri_cookie=123"
        
        with patch("resources.lib.utils.cache.cacheFunction", side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)):
            result = utils.getHtml("http://example.com")
            assert result == "<html>Real Content</html>"
            assert mock_get_sucuri.called

class TestAdditionalHelpers:
    @patch("resources.lib.utils.xbmc.getCondVisibility")
    @patch("resources.lib.utils.addon.getSetting")
    def test_inputstream_check(self, mock_get_setting, mock_get_cond):
        mock_get_cond.return_value = True
        mock_get_setting.return_value = "false"
        
        mock_listitem = MagicMock()
        url = "http://example.com/video.mpd"
        
        # mpd should trigger inputstream
        utils.inputstream_check(url, mock_listitem, "auto")
        
        mock_listitem.setProperty.assert_any_call("inputstream", "inputstream.adaptive")
        mock_listitem.setProperty.assert_any_call("inputstream.adaptive.manifest_type", "mpd")

    def test_get_kodi_url_format(self):
        # This function appends headers to a URL
        url = "http://video.com/file.mp4"
        res = utils.get_kodi_url(url, referer="http://ref.com")
        assert "http://video.com/file.mp4|" in res
        # urllib.parse.quote by default does NOT encode /
        assert "Referer=http%3A//ref.com" in res

    def test_parse_query_with_default_mode(self):
        q = "a=1&b=2"
        res = utils.parse_query(q)
        assert res["a"] == "1"
        assert res["b"] == "2"
        assert res["mode"] == "main.INDEX"

class TestDownloadVideo:
    @patch("resources.lib.utils.xbmcgui.Dialog")
    @patch("resources.lib.utils.xbmcvfs")
    @patch("resources.lib.utils.xbmc")
    @patch("resources.lib.utils.addon.getSetting")
    def test_download_video_simple(self, mock_get_setting, mock_xbmc, mock_vfs, mock_dialog):
        mock_get_setting.return_value = "/downloads"
        mock_vfs.exists.return_value = True
        mock_vfs.makeLegalFilename.side_effect = lambda x: x
        mock_xbmc.makeLegalFilename.side_effect = lambda x: x
        
        # Mock dialog to select directory or cancel
        mock_dialog.return_value.browse.return_value = None # Cancel browse
        
        # This function is very complex, let's just hit the entry point
        # and test that it handles missing settings/cancelations.
        with patch("resources.lib.utils.kodilog"):
            utils.downloadVideo("http://test.com/video.mp4", "Test Video")
