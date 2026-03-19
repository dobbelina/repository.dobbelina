from unittest.mock import MagicMock
from resources.lib.sites import someporn
from tests.conftest import fixture_mapped_get_html


def test_someporn_playvid_get_playlist(monkeypatch):
    url = "https://some.porn/videos/274226/test-video/"
    name = "Test Video"

    fixture_map = {
        "some.porn/videos/": "sites/someporn_video.html",
    }
    fixture_mapped_get_html(monkeypatch, someporn, fixture_map)

    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    mock_vp_instance = mock_vp_class.return_value

    someporn.Playvid(url, name)

    args, _ = mock_vp_instance.play_from_direct_link.call_args
    captured_url = args[0]

    assert "cdn3x.com" in captured_url
    assert "get-playlist" in captured_url
    assert "Referer=" in captured_url
