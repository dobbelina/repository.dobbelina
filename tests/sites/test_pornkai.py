
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from resources.lib.sites import pornkai
from resources.lib import utils

@pytest.fixture
def site_spec_fixture():
    with patch('resources.lib.adultsite.AdultSite.add_dir'), \
         patch('resources.lib.adultsite.AdultSite.add_download_link') as mock_add_download_link, \
         patch('resources.lib.utils.getHtml') as mock_get_html:

        yield pornkai, mock_add_download_link, mock_get_html

def test_list_videos(site_spec_fixture):
    """
    Tests if the List function correctly parses a video listing page.
    """
    site_spec, mock_add_download_link, mock_get_html = site_spec_fixture
    
    # Load the test fixture
    fixture_path = Path(__file__).parent.parent / 'fixtures/sites/pornkai_search_live.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        mock_get_html.return_value = f.read()

    # Call the function to be tested
    site_spec.List("https://pornkai.com/videos?q=sex")

    # Assert that add_download_link was called
    assert mock_add_download_link.called

    # Check the first call to add_download_link
    first_call_args = mock_add_download_link.call_args_list[0][0]
    
    # Title
    assert "Lovely babe fucked in missionary position" in first_call_args[0]
    # URL
    assert "/view?key=xv29201765" in first_call_args[1]
    # Image
    assert "https://thumb-cdn77.others-cdn.com" in first_call_args[3]


def test_playvid(site_spec_fixture):
    """
    Tests if the Playvid function correctly finds the video URL.
    """
    site_spec, _, mock_get_html = site_spec_fixture
    
    # Load the test fixture
    fixture_path = Path(__file__).parent.parent / 'fixtures/sites/pornkai_video_page_live.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        mock_get_html.return_value = f.read()

    with patch('resources.lib.utils.VideoPlayer') as mock_vp_class:
        mock_vp_instance = mock_vp_class.return_value
        site_spec.Playvid("https://pornkai.com/view?key=xv29201765", "Test Video")
        
        # Assert that play_from_link_to_resolve was called with the correct URL
        # We need to find if it was called
        mock_vp_instance.play_from_link_to_resolve.assert_called_once_with('https://www.xvideos.com/embedframe/hbdvopo7d13')

def setup_module():
    # Mock Kodi environment for tests
    utils.addon = MagicMock()
    utils.addon.getAddonInfo.return_value = 'plugin.video.cumination'
    utils.addon_sys = 'plugin://plugin.video.cumination/'
    utils.addon_id = 'plugin.video.cumination'
