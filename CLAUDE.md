# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Kodi addon repository for adult content addons. The primary addon is **Cumination** (plugin.video.cumination), which provides access to various adult video sites through Kodi's plugin system.

## Repository Structure

- **plugin.video.cumination/** - Main Cumination addon (current version: 1.1.164)
- **plugin.video.uwc/** - Ultimate Whitecream addon (legacy, superseded by Cumination)
- **repository.dobbelina/** - Repository addon files
- **build_repo_addons.py** - Build script for packaging addons
- **addons.xml** - Repository index of available addons
- **addons.xml.md5** - MD5 checksum of addons.xml

## Building and Packaging

### Build Addon Packages

```bash
# Build all addons
python build_repo_addons.py

# Build specific addon
python build_repo_addons.py --addons plugin.video.cumination

# Build and update repository index
python build_repo_addons.py --update-index
```

The build script:
- Creates ZIP files with proper Kodi folder structure
- Excludes `.git`, `.github`, `__pycache__`, and `*.zip` files
- Uses forward-slash paths (POSIX) as required by Kodi
- Outputs to current directory by default
- Can update `addons.xml` and `addons.xml.md5` with `--update-index`

### Version Updates

When updating addon version:
1. Edit `plugin.video.cumination/addon.xml` and change version attribute
2. Run `python build_repo_addons.py --addons plugin.video.cumination --update-index`
3. Commit changes including the new ZIP and updated `addons.xml`/`addons.xml.md5`

## Cumination Addon Architecture

### Core Framework

**URL Dispatcher Pattern**: The addon uses a custom URL dispatcher system (`url_dispatcher.py`) for routing:
- Functions are registered with `@site.register()` or `@url_dispatcher.register()` decorators
- Modes are strings like `"sitename.functionname"` that route to specific functions
- The dispatcher introspects function signatures to extract and validate parameters

**AdultSite Base Class** (`adultsite.py`):
- Inherits from `URL_Dispatcher`
- Base class for all site implementations
- Maintains WeakSet of all site instances
- Provides registration decorators for site-specific functions
- Each site gets its own isolated namespace for mode routing

**CustomSite Class** (`customsite.py`):
- Extends AdultSite for user-added custom sites
- Stores metadata in SQLite database
- Dynamically loads from filesystem at runtime

### Site Implementation Pattern

Sites are implemented in `plugin.video.cumination/resources/lib/sites/`:

```python
from resources.lib.adultsite import AdultSite
from resources.lib import utils

site = AdultSite('sitename', '[COLOR hotpink]Display Name[/COLOR]',
                 'https://site.url/', 'icon.png', 'about_file')

@site.register(default_mode=True)
def Main():
    # Entry point for the site
    site.add_dir('Categories', url, 'Categories', site.img_cat)
    site.add_dir('Search', url, 'Search', site.img_search)
    List(site.url)
    utils.eod()

@site.register()
def List(url):
    # Parse and list videos
    listhtml = utils.getHtml(url)
    # Extract videos with regex
    site.add_download_link(name, url, 'Playvid', img, desc)
    # Handle pagination
    utils.eod()

@site.register()
def Playvid(url, name):
    # Extract video stream URL
    return videourl
```

### Key Components

**Entry Point** (`default.py`):
- Initializes URL dispatcher
- Loads all site modules from `resources/lib/sites/`
- Handles custom site loading
- Implements main menu and age verification

**Utilities** (`utils.py`):
- HTTP requests with caching (`getHtml`)
- Cookie management
- Dialog and progress UI helpers
- Cloudflare bypass integration
- Video URL extraction helpers

**Favorites System** (`favorites.py`):
- SQLite database for storing favorite videos
- Custom lists functionality
- Integration with Kodi's context menu

**Video Resolution** (`resolveurl` integration):
- Uses `script.module.resolveurl` for supported hosts
- Custom decrypters in `resources/lib/decrypters/` for proprietary players

### Adding a New Site

1. Create `plugin.video.cumination/resources/lib/sites/newsite.py`
2. Define site instance and implement Main, List, and Playvid functions
3. Site auto-registers on import through `from resources.lib.sites import *` in `default.py`
4. Add icon to `plugin.video.cumination/resources/media/`
5. Create about file in `plugin.video.cumination/resources/about/`

### Testing Sites

There's no automated test suite. Testing is done manually:
1. Install addon in Kodi test environment
2. Navigate to the site in the addon UI
3. Test video playback, search, pagination, categories

## Dependencies

Cumination addon requires these Kodi modules:
- `script.module.six` - Python 2/3 compatibility
- `script.module.kodi-six` - Kodi Python compatibility layer
- `script.module.resolveurl` - Video host URL resolver
- `script.module.resolveurl.xxx` - Adult site URL resolvers
- `script.common.plugin.cache` - Caching system
- `script.module.websocket` - WebSocket support (for live cams)
- `script.module.inputstreamhelper` - HLS/DASH stream support
- `script.module.requests` - HTTP library

## Code Style Notes

- Python 2/3 compatible (uses `six` library)
- Heavy use of regex for HTML parsing (no BeautifulSoup/lxml)
- URL dispatcher pattern instead of traditional routing
- Decorator-based function registration
- SQLite for persistence (favorites, custom sites)
- Kodi-specific UI via `xbmcgui`, `xbmcplugin`, `xbmcaddon`

## Common Patterns

**HTML Fetching**:
```python
listhtml = utils.getHtml(url, headers=hdr)
```

**Video Extraction**:
```python
match = re.compile(r'pattern', re.DOTALL | re.IGNORECASE).findall(html)
for url, img, title in match:
    site.add_download_link(title, url, 'Playvid', img)
```

**Pagination**:
```python
nextpage = re.compile(r'<a href="([^"]+)"[^>]*>Next').findall(html)
if nextpage:
    site.add_dir('Next Page', nextpage[0], 'List', site.img_next)
```

**Video Playback**:
```python
@site.register()
def Playvid(url, name):
    videourl = extract_video_url(url)
    return videourl  # Kodi handles playback
```

## Integration with Kodi

- Addons are installed via repository.dobbelina
- Repository hosted at https://dobbelina.github.io
- Auto-updates when new versions are pushed to master branch
- Users install repository ZIP, then install addons from repo

## Common Issues

**Cloudflare Protection**: Sites with Cloudflare require:
- FlareSolverr integration (`flaresolverr.py`)
- Or cloudflare bypass (`cloudflare.py`)

**Video Player Selection**: Some sites use custom players (KVS, Uppod, etc.):
- Decrypters in `resources/lib/decrypters/`
- JavaScript crypto implementations in `resources/lib/jscrypto/`

**M3U8 Streams**: HLS streams require:
- `script.module.inputstreamhelper`
- Proper MIME type and headers

## Git Workflow

- Main branch: `master`
- Create commits with descriptive messages
- Recent pattern: `feat:`, `chore:`, `fix:` prefixes
- Include version numbers in commit messages for addon updates
