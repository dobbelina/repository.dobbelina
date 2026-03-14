from unittest.mock import MagicMock
from resources.lib.sites import javseen
from tests.conftest import fixture_mapped_get_html

def test_javseen_playvid_recursive(monkeypatch):
    url = "https://javseen.tv/274282/higr-077-is-it-okay-to-do-it-at-the-hospital-marina-asakura/"
    name = "Test Video"
    
    # Mock getHtml to return our fixtures
    fixture_map = {
        "javseen.tv/274282/": "sites/javseen_embed.html",
        "javseen.tv/embed/": "sites/javseen_embed.html",
        "javseen_play/": "sites/javseen_play.html",
        "turbovid.vip/t/": "sites/javseen_turbovid.html"
    }
    
    from tests.conftest import read_fixture
    def _fake_get_html(url, *args, **kwargs):
        for key, fixture_name in fixture_map.items():
            if key in url:
                return read_fixture(fixture_name)
        return None
    
    monkeypatch.setattr(javseen.utils, "getHtml", _fake_get_html)
    
    # Mock VideoPlayer
    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    mock_vp_instance = mock_vp_class.return_value
    
    # Mock resolveurl
    mock_resolveurl = MagicMock()
    mock_vp_instance.resolveurl = mock_resolveurl
    
    javseen.Playvid(url, name)
    
    # Check if play_from_direct_link was called with the m3u8
    args, _ = mock_vp_instance.play_from_direct_link.call_args
    captured_url = args[0]
    
    assert "turboviplay.com" in captured_url
    assert ".m3u8" in captured_url
    assert "Referer=https://turbovid.vip/t/" in captured_url
