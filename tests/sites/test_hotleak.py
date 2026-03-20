
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from resources.lib.sites import hotleak
from resources.lib import utils

@pytest.fixture
def site_spec_fixture():
    with patch('resources.lib.adultsite.AdultSite.add_dir') as mock_add_dir, \
         patch('resources.lib.adultsite.AdultSite.add_download_link') as mock_add_download_link, \
         patch('resources.lib.utils.getHtml') as mock_get_html:

        yield hotleak, mock_add_dir, mock_add_download_link, mock_get_html

def test_main_menu(site_spec_fixture):
    """
    Tests if the Main function correctly adds the Videos and Search directories.
    """
    site_spec, mock_add_dir, _, _ = site_spec_fixture
    site_spec.Main("https://hotleak.vip/")
    
    # Check Videos link
    mock_add_dir.assert_any_call("[COLOR hotpink]Videos[/COLOR]", "https://hotleak.vip/videos", "List", "")
    # Check Search link
    mock_add_dir.assert_any_call("[COLOR hotpink]Search[/COLOR]", "https://hotleak.vip/search", "Search", site_spec.site.img_search)

def test_list_videos(site_spec_fixture):
    """
    Tests if the List function correctly parses a video listing page and pagination.
    """
    site_spec, mock_add_dir, mock_add_download_link, mock_get_html = site_spec_fixture
    
    # Load the test fixture
    fixture_path = Path(__file__).parent.parent / 'fixtures/sites/hotleak_videos_live.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        mock_get_html.return_value = f.read()

    # Call the function to be tested
    site_spec.List("https://hotleak.vip/videos")

    # Assert that add_download_link was called (should be many videos)
    assert mock_add_download_link.called
    assert mock_add_download_link.call_count > 10

    # Check the first call to add_download_link
    first_call_args = mock_add_download_link.call_args_list[0][0]
    # URL should contain video path
    assert "/video/" in first_call_args[1]

    # Check for "Next Page"
    mock_add_dir.assert_any_call("Next Page (2)", "https://hotleak.vip/videos?page=2", "List", site_spec.site.img_next, page='2')


def test_playvid(site_spec_fixture):
    """
    Tests if the Playvid function correctly finds and decrypts the video URL.
    """
    site_spec, _, _, mock_get_html = site_spec_fixture
    
    # Load the test fixture
    fixture_path = Path(__file__).parent.parent / 'fixtures/sites/hotleak_video_page_live.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        mock_get_html.return_value = f.read()

    with patch('resources.lib.utils.VideoPlayer') as mock_vp_class:
        mock_vp_instance = mock_vp_class.return_value
        site_spec.Playvid("https://hotleak.vip/eth0t.666/video/11939112", "Test Video")
        
        # Assert that play_from_direct_link was called with a decrypted M3U8 URL and headers
        assert mock_vp_instance.play_from_direct_link.called
        call_args = mock_vp_instance.play_from_direct_link.call_args[0][0]
        assert "m3u8" in call_args
        assert "|User-Agent=" in call_args
        assert "Referer=https%3A//hotleak.vip/" in call_args


