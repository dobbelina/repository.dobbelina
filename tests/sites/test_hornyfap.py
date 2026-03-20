
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from resources.lib.sites import hornyfap
from resources.lib import utils

@pytest.fixture
def site_spec_fixture():
    with patch('resources.lib.adultsite.AdultSite.add_dir') as mock_add_dir, \
         patch('resources.lib.adultsite.AdultSite.add_download_link') as mock_add_download_link, \
         patch('resources.lib.utils.getHtml') as mock_get_html:

        yield hornyfap, mock_add_dir, mock_add_download_link, mock_get_html

def test_main_menu(site_spec_fixture):
    site_spec, mock_add_dir, _, _ = site_spec_fixture
    site_spec.Main("https://hornyfap.tv/")
    
    mock_add_dir.assert_any_call("Latest Videos", "https://hornyfap.tv/latest-updates/", "List", "")
    mock_add_dir.assert_any_call("Search", "https://hornyfap.tv/search/", "Search", site_spec.site.img_search)

def test_list_videos(site_spec_fixture):
    site_spec, mock_add_dir, mock_add_download_link, mock_get_html = site_spec_fixture
    
    fixture_path = Path(__file__).parent.parent / 'fixtures/sites/hornyfap_home.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        mock_get_html.return_value = f.read()

    site_spec.List("https://hornyfap.tv/")

    assert mock_add_download_link.called
    assert mock_add_download_link.call_count >= 20

    first_call = mock_add_download_link.call_args_list[0]
    args = first_call[0]
    kwargs = first_call[1]
    
    assert "Leah Wilde" in args[0]
    assert "https://hornyfap.tv/video/14023/" in args[1]
    assert kwargs.get("duration") == "18:50"

    # Check Next Page
    mock_add_dir.assert_any_call("Next Page (2)", "https://hornyfap.tv/latest-updates/2/", "List", site_spec.site.img_next, page='2')

def test_playvid(site_spec_fixture):
    site_spec, _, _, mock_get_html = site_spec_fixture
    
    fixture_path = Path(__file__).parent.parent / 'fixtures/sites/hornyfap_video.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        mock_get_html.return_value = f.read()

    with patch('resources.lib.utils.VideoPlayer') as mock_vp_class:
        mock_vp_instance = mock_vp_class.return_value
        site_spec.Playvid("https://hornyfap.tv/video/14023/", "Test Video")
        
        # Now uses play_from_kt_player
        assert mock_vp_instance.play_from_kt_player.called
        args = mock_vp_instance.play_from_kt_player.call_args[0]
        assert args[0] == mock_get_html.return_value
        assert args[1] == "https://hornyfap.tv/video/14023/"


