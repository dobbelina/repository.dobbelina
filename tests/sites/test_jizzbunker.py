from resources.lib.sites import jizzbunker
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_site():
    with patch("resources.lib.sites.jizzbunker.site") as mock:
        mock.url = "https://jizzbunker.com/"
        yield mock


def test_list_videos(mock_site):
    with open("tests/fixtures/sites/jizzbunker_list.html", "r", encoding="utf-8") as f:
        html = f.read()

    with (
        patch("resources.lib.utils.getHtml", return_value=html),
        patch("resources.lib.utils.eod"),
    ):
        jizzbunker.List("https://jizzbunker.com/trending")

        # Verify some videos were added
        assert mock_site.add_download_link.called
        # Check details from fixture
        args, kwargs = mock_site.add_download_link.call_args_list[0]
        assert "Bigtitted babe" in args[0]
        assert "/6064426/" in args[1]
        assert "08:00" in kwargs.get("duration", "")


def test_playvid(mock_site):
    with open("tests/fixtures/sites/jizzbunker_video.html", "r", encoding="utf-8") as f:
        html = f.read()

    mock_vp = MagicMock()
    with (
        patch("resources.lib.utils.getHtml", return_value=html),
        patch("resources.lib.utils.VideoPlayer", return_value=mock_vp),
    ):
        jizzbunker.Playvid("https://jizzbunker.com/5847832/video", "Test Video")

        # Verify attempt to play
        assert (
            mock_vp.play_from_direct_link.called
            or mock_vp.play_from_link_to_resolve.called
        )
