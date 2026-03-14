from unittest.mock import MagicMock
from resources.lib.sites import thepornarea
from tests.conftest import fixture_mapped_get_html

def test_thepornarea_playvid(monkeypatch):
    url = "https://thepornarea.com/videos/1161120/car-dildo-orgasm/"
    name = "Test Video"
    
    # Mock getHtml to return our fixtures
    fixture_map = {
        "thepornarea.com/videos/": "sites/thepornarea_embed.html",
        "thepornarea.com/embed/": "sites/thepornarea_embed.html"
    }
    fixture_mapped_get_html(monkeypatch, thepornarea, fixture_map)
    
    # Mock VideoPlayer
    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    mock_vp_instance = mock_vp_class.return_value
    
    thepornarea.Playvid(url, name)
    
    # Check if play_from_direct_link was called with the CORRECT (decoded) URL
    args, _ = mock_vp_instance.play_from_direct_link.call_args
    captured_url = args[0]
    
    assert "get_file" in captured_url
    assert "94292012b9c57a4104f6b65e19c810428474ce7221" in captured_url # The decoded token
    assert "contents/videos" not in captured_url
