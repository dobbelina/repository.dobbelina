# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Kodi addon repository for adult content. The primary addon is **Cumination** (`plugin.video.cumination`), providing access to ~163 adult video sites through Kodi's plugin system. This is a fork that tracks upstream (dobbelina/repository.dobbelina).

Other addons in the repo: `plugin.video.uwc` (legacy fork), `repository.dobbelina` (repo installer), `script.video.F4mProxy` (HLS/F4M helper).

## Commands

```bash
# Setup (or run ./setup.sh which handles system deps + venv)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-test.txt

# Tests
python run_tests.py                              # All tests (recommended - cross-platform)
python run_tests.py --site pornhub -v            # Single site test
python run_tests.py --coverage                   # With coverage
pytest tests/sites/test_pornhub.py -v            # Direct pytest
pytest tests/test_utils.py::test_parse_html -v   # Single test function

# Lint
ruff check plugin.video.cumination/resources/lib/
ruff check --fix plugin.video.cumination/resources/lib/

# Build
python build_repo_addons.py --addons plugin.video.cumination
python build_repo_addons.py --update-index       # Also regenerates addons.xml + md5

# Upstream sync
./scripts/check_upstream_sync.sh
./scripts/cherry_pick_with_tracking.sh <hash>    # Cherry-pick with tracking
```

## Architecture

### Request Flow

Kodi calls `plugin://plugin.video.cumination/?mode=sitename.Function&url=...` → `default.py` parses the URL → `URL_Dispatcher` looks up the registered function → calls it with extracted params.

### Core Components

- **`basics.py`** - Loaded first; defines global addon constants and paths (`addon`, `addon_handle`, `cookiePath`, `favoritesdb`, `profileDir`, `imgDir`, etc.). Imported by both `utils.py` and `adultsite.py`.
- **`url_dispatcher.py`** - Routes mode strings to decorated functions. Registry is class-level (shared across instances).
- **`adultsite.py`** - `AdultSite` base class. Maintains a `WeakSet` of all instances for auto-discovery. Each site gets an isolated mode namespace.
- **`default.py`** - Entry point. Imports `resources.lib.sites.*` which triggers module-level `AdultSite(...)` instantiation, auto-registering each site.
- **`utils.py`** - HTTP (`getHtml`), BeautifulSoup helpers (`parse_html`, `safe_get_attr`, `safe_get_text`, `soup_videos_list`), Kodi UI utilities.
- **`sites/__init__.py`** - `__all__` list controls which site modules are loaded. New sites must be added here.
- **`sites/soup_spec.py`** - `SoupSiteSpec` dataclass for declarative selector-based video listing.
- **`favorites.py`** - SQLite-backed favorites and custom site management.
- **`http_timeouts.py`** - Named timeout constants (`HTTP_TIMEOUT_SHORT`, `HTTP_TIMEOUT_MEDIUM`, `HTTP_TIMEOUT_LONG`). Use these instead of magic numbers in site modules.
- **`decrypters/`** / **`jscrypto/`** - Custom video player decryption (KVS, Uppod, etc.)
- **`playwright_helper.py`** (in lib/) - Dev/debug tool only; same restriction as Playwright — never use in site modules. For test-time Playwright use `tests/utils/playwright_helper.py` instead.

### Site Module Pattern

Every site in `resources/lib/sites/` follows this structure:

```python
from resources.lib.adultsite import AdultSite
from resources.lib import utils

site = AdultSite('sitename', '[COLOR hotpink]Display Name[/COLOR]',
                 'https://site.url/', 'icon.png', 'about_file')

@site.register(default_mode=True)
def Main():
    site.add_dir('Categories', site.url, 'Categories', site.img_cat)
    List(site.url)
    utils.eod()

@site.register()
def List(url):
    soup = utils.parse_html(utils.getHtml(url))
    for item in soup.select('.video-item'):
        link = item.select_one('a')
        site.add_download_link(
            utils.safe_get_attr(link, 'title'),
            utils.safe_get_attr(link, 'href'),
            'Playvid',
            utils.safe_get_attr(item.select_one('img'), 'src', ['data-src', 'data-lazy']))
    utils.eod()

@site.register()
def Playvid(url, name):
    return videourl  # Kodi handles playback
```

For declarative selector-based sites, see `SoupSiteSpec` in `sites/soup_spec.py` (reference: `sites/anybunny.py`).

### Test Structure

- `tests/conftest.py` - Kodi mocks (xbmc, xbmcaddon, xbmcvfs, xbmcplugin) and sys.path setup
- `tests/fixtures/sites/` - Saved HTML from real sites for regression testing
- `tests/sites/test_*.py` - Site-specific parsing tests
- `tests/test_utils.py` - BeautifulSoup helper tests

## Creating a New Site

1. Create `plugin.video.cumination/resources/lib/sites/[sitename].py` using the pattern above
2. Add `'sitename'` to `__all__` in `resources/lib/sites/__init__.py`
3. Add icon PNG to `resources/media/` (optional)
4. Save HTML fixtures to `tests/fixtures/sites/`
5. Write tests in `tests/sites/test_[sitename].py`
6. Run: `pytest tests/sites/test_[sitename].py -v`

If the site doesn't appear in Kodi: verify `AdultSite(...)` is at module level, a function has `@site.register(default_mode=True)`, and the module is in `__init__.py`'s `__all__`.

## BeautifulSoup Migration

Migration from regex to BeautifulSoup4 is **complete** (163/163 sites). Tracked in `docs/development/MODERNIZATION.md`. All new sites should use BeautifulSoup exclusively — use `parse_html()`, `safe_get_attr()`, `safe_get_text()`, and `soup_videos_list()` from utils. Reference implementation: `sites/pornhub.py`.

Find sites needing tests:
```bash
comm -23 <(grep -l "parse_html" plugin.video.cumination/resources/lib/sites/*.py | xargs -n1 basename | sed 's/.py//' | sort) <(ls tests/sites/test_*.py | xargs -n1 basename | sed 's/test_//' | sed 's/.py//' | sort)
```

## Version Updates

1. Edit version in `plugin.video.cumination/addon.xml` line 1
2. Run `python build_repo_addons.py --addons plugin.video.cumination --update-index`
3. Commit the modified `addon.xml`, new ZIP, updated `addons.xml` and `addons.xml.md5`

## Git Conventions

- Branch: `master`
- Commit prefixes: `feat:`, `fix:`, `chore:`
- Cherry-picks from upstream: always use `-x` flag, update `docs/development/UPSTREAM_SYNC.md`

## Custom Agents

A `site-debugger` agent is available in `.claude/agents/site-debugger.md`. Use it when investigating new sites, fixing broken site modules, or reverse-engineering video player encryption. It uses Playwright for browser-based exploration and produces a final module using only `getHtml()`/BeautifulSoup (no Playwright in output).

## Common Issues

- **Cloudflare**: Use `flaresolverr.py` or `cloudflare.py` integration
- **HLS/M3U8**: Requires `inputstream.adaptive` (not always bundled on Linux)
- **Kodi import errors in tests**: Run from repo root with `python run_tests.py`; check `conftest.py` mocks
- **Lazy-loading images**: Check `data-src`, `data-lazy`, `data-original` attributes via `safe_get_attr` fallbacks
- **Playwright**: Only for tests and development-time site exploration. Never use Playwright in site modules — it is not available in the Kodi runtime environment
