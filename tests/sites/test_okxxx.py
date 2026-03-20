from resources.lib.sites import okxxx
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_site():
    with patch("resources.lib.sites.okxxx.site") as mock:
        mock.url = "https://ok.xxx/"
        yield mock


def test_list_videos(mock_site):
    with open("tests/fixtures/sites/okxxx_list.html", "r", encoding="utf-8") as f:
        html = f.read()

    with (
        patch("resources.lib.utils.getHtml", return_value=html),
        patch("resources.lib.utils.eod"),
    ):
        okxxx.List("https://ok.xxx/trending/")

        # Verify some videos were added
        assert mock_site.add_download_link.called
        # Check details from fixture
        args, kwargs = mock_site.add_download_link.call_args_list[0]
        assert "Awesome Samantha Sin" in args[0]
        assert "/video/693873/" in args[1]
        assert "16:35" in kwargs.get("duration", "")


def test_playvid(mock_site):
    with open("tests/fixtures/sites/okxxx_video.html", "r", encoding="utf-8") as f:
        html = f.read()

    mock_vp = MagicMock()
    with (
        patch("resources.lib.utils.getHtml", return_value=html),
        patch("resources.lib.utils.VideoPlayer", return_value=mock_vp),
    ):
        okxxx.Playvid("https://ok.xxx/video/691478/", "Test Video")

        # Verify attempt to play
        assert (
            mock_vp.play_from_direct_link.called
            or mock_vp.play_from_link_to_resolve.called
        )
