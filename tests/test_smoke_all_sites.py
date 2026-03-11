"""Smoke test all sites - using real pytest fixtures for accurate Kodi simulation

This test imports each site and tries to call its Main function to see if it works.
Uses the same Kodi mocks as all other tests, so results should match real addon behavior.
"""

import pytest
import importlib
from pathlib import Path

# Get all site modules
SITES_DIR = Path(__file__).parent.parent / 'plugin.video.cumination' / 'resources' / 'lib' / 'sites'


def discover_sites():
    """Discover all site modules"""
    sites = []
    for file_path in sorted(SITES_DIR.glob('*.py')):
        name = file_path.stem
        if name not in {'__init__', 'soup_spec'}:
            sites.append(name)
    return sites


@pytest.fixture
def captured_items():
    """Capture addDir and addDownLink calls"""
    class Capture:
        def __init__(self):
            self.dirs = []
            self.downloads = []
            self.errors = []

    return Capture()


@pytest.fixture(autouse=True)
def patch_addon_functions(monkeypatch, captured_items):
    """Patch addon functions to capture calls instead of calling Kodi"""
    from resources.lib import utils
    from resources.lib import basics

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        captured_items.dirs.append({
            'name': str(name or ''),
            'url': str(url or ''),
            'mode': str(mode or ''),
        })
        return True

    def fake_add_down(name, url, mode, iconimage, *args, **kwargs):
        captured_items.downloads.append({
            'name': str(name or ''),
            'url': str(url or ''),
            'mode': str(mode or ''),
        })
        return True

    def fake_notify(header=None, msg="", duration=5000, icon=None, *args, **kwargs):
        """Capture error notifications"""
        captured_items.errors.append(f"{header}: {msg}")

    # Patch basics module (where addDir and addDownLink are)
    monkeypatch.setattr(basics, 'addDir', fake_add_dir)
    monkeypatch.setattr(basics, 'addDownLink', fake_add_down)

    # Patch utils module functions
    if hasattr(utils, 'notify'):
        monkeypatch.setattr(utils, 'notify', fake_notify)
    monkeypatch.setattr(utils, 'eod', lambda *a, **k: None)

    # Mock getHtml and postHtml to return minimal HTML instead of making real requests
    def fake_gethtml(url, *args, **kwargs):
        url_lower = url.lower()
        
        # JSON-only responses
        if any(x in url_lower for x in ['ajax', 'externulls.com', 'load_more', 'api/', 'htv', 'hanime']):
            # Special case for beeg BGCat which expects a dict
            if 'externulls.com/tag/facts/tags' in url:
                return '{}'
            # Special case for beeg BGList which expects a list
            if 'externulls.com/facts/tag' in url:
                return '[]'
            # Special case for porndig which expects {"data": {"content": "..."}}
            if 'porndig.com' in url:
                return '{"data": {"content": "<html><body>Video content</body></html>"}}'
            # Special case for hanime which expects hits and hits[hits]
            if 'hanime.tv' in url or 'htv-services.com' in url:
                return '{"hits": "[]", "nbPages": 0}'
            return '{}'

        # Mixed HTML responses (containing JSON blocks)
        return """
        <html><body>
            <script id="initials">window.initials={"layoutPage":{"videoListProps":{"videoThumbProps":[]},"paginationProps":{"currentPageNumber":1,"lastPageNumber":2,"pageLinkTemplate":"/page/{#}"}}};</script>
            <script>window.player_args = []; window.player_args.push({"src":[{"codec":"h264","src":"https://test.com/video.mp4"}]});</script>
            <div class="video"><a href="/video/1" title="Test Video 1">
                <img src="/thumb1.jpg" alt="Test 1">
            </a></div>
            <div class="video"><a href="/video/2" title="Test Video 2">
                <img src="/thumb2.jpg" alt="Test 2">
            </a></div>
            <div class="pagination"><span class="current"><a href="/page/2/">2</a></span></div>
            <a href="/next" class="next">Next</a>
            <select name="category_slug"><option value="cat1">Category 1</option></select>
            <iframe src="https://player.test/1" data-url="https://player.test/1"></iframe>
            <article><a href="/v1" title="Vid 1"><img src="t1.jpg"></a><h3 class="title">Vid 1</h3></article>
        </body></html>
        """

    monkeypatch.setattr(utils, 'getHtml', fake_gethtml)
    monkeypatch.setattr(utils, 'postHtml', fake_gethtml)
    if hasattr(utils, '_getHtml'):
        monkeypatch.setattr(utils, '_getHtml', fake_gethtml)
    if hasattr(utils, '_postHtml'):
        monkeypatch.setattr(utils, '_postHtml', fake_gethtml)


@pytest.mark.parametrize('site_name', discover_sites())
def test_site_can_import(site_name):
    """Test that site module can be imported without errors"""
    try:
        module = importlib.import_module(f'resources.lib.sites.{site_name}')
        assert hasattr(module, 'site'), f"{site_name} has no 'site' object"
        assert module.site is not None, f"{site_name}.site is None"
    except Exception as e:
        pytest.fail(f"Failed to import {site_name}: {type(e).__name__}: {e}")


@pytest.mark.parametrize('site_name', discover_sites())
def test_site_has_default_mode(site_name):
    """Test that site has a default entry point"""
    try:
        module = importlib.import_module(f'resources.lib.sites.{site_name}')
        site = module.site

        # Check for default_mode
        assert hasattr(site, 'default_mode'), f"{site_name} has no default_mode"
        if not site.default_mode:
             pytest.skip(f"{site_name} is disabled (default_mode is empty)")

        # Verify the function exists in the registry
        from resources.lib.url_dispatcher import URL_Dispatcher
        assert site.default_mode in URL_Dispatcher.func_registry, \
            f"{site_name}.default_mode '{site.default_mode}' not in registry"

    except Exception as e:
        pytest.fail(f"{site_name} default_mode check failed: {type(e).__name__}: {e}")


@pytest.mark.parametrize('site_name', discover_sites())
def test_site_main_function_runs(site_name, captured_items, monkeypatch):
    """Test that calling the site's Main function doesn't crash"""
    try:
        module = importlib.import_module(f'resources.lib.sites.{site_name}')
        site = module.site

        if not hasattr(site, 'default_mode') or not site.default_mode:
            pytest.skip(f"{site_name} has no default_mode")

        # Reset captured items
        captured_items.dirs.clear()
        captured_items.downloads.clear()
        captured_items.errors.clear()

        # Try to call the default mode function
        from resources.lib.url_dispatcher import URL_Dispatcher

        try:
            # Provide some default arguments that are commonly required
            args = {
                'url': site.url,
                'name': getattr(site, 'display_name', site.name),
                'mode': site.default_mode,
                'page': 1,
            }
            URL_Dispatcher.dispatch(site.default_mode, args)
        except Exception as e:
            # Some exceptions are expected (like network errors in mock environment)
            # But we can still check if the function exists and is callable
            error_type = type(e).__name__
            error_msg = str(e)

            # Expected errors in test environment (not real bugs)
            expected_errors = [
                'special://',  # Path handling
                'resolveurl',  # External dependency
                'websocket',   # Webcam sites
                'inputstream', # Streaming
            ]

            if any(expected in error_msg.lower() for expected in expected_errors):
                pytest.skip(f"{site_name} skipped: test environment limitation ({error_type})")
            else:
                # This is likely a real bug
                pytest.fail(f"{site_name} crashed: {error_type}: {error_msg}")

        # Check that function produced some output or didn't crash

        # Webcam sites may not produce items in test environment
        if hasattr(site, 'webcam') and site.webcam:
            pytest.skip(f"{site_name} is a webcam site - can't fully test in mock environment")

        # At least it should have tried to do something (not necessarily succeed with mocked HTML)
        # We're mainly checking it doesn't crash with syntax/import errors

    except Exception as e:
        pytest.fail(f"{site_name} Main function test failed: {type(e).__name__}: {e}")


@pytest.mark.parametrize('site_name', discover_sites())
def test_site_has_play_function(site_name):
    """Test that site has some kind of play/video function"""
    try:
        module = importlib.import_module(f'resources.lib.sites.{site_name}')
        site = module.site

        from resources.lib.url_dispatcher import URL_Dispatcher

        # Look for functions associated with this site instance's name
        # (site.name might differ from site_name/filename)
        site_functions = [
            mode for mode in URL_Dispatcher.func_registry.keys()
            if mode.startswith(f"{site.name}.")
        ]

        # Check for play-related functions
        play_functions = [
            f for f in site_functions
            if any(x in f.lower() for x in ['play', 'vid', 'video', 'watch'])
        ]

        # Webcam sites might not have traditional play functions
        if hasattr(site, 'webcam') and site.webcam:
            pytest.skip(f"{site_name} is a webcam site")

        # Special case: some sites might have a dedicated play mode in their AdultSite object
        if not play_functions and hasattr(site, 'play_mode') and site.play_mode:
            play_functions = [site.play_mode]

        assert len(play_functions) > 0, \
            f"{site_name} has no play function. Functions: {site_functions}"

    except Exception as e:
        pytest.fail(f"{site_name} play function check failed: {type(e).__name__}: {e}")


def test_all_sites_summary(capsys):
    """Print summary of all sites (run this last)"""
    sites = discover_sites()
    print(f"\n\nTotal sites tested: {len(sites)}")
    print("\nTo see detailed results for a specific site:")
    print("  python run_tests.py tests/test_smoke_all_sites.py::test_site_main_function_runs[sitename] -v")
