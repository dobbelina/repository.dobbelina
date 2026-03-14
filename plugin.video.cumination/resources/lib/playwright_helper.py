"""
Playwright helper utilities for development/testing.

Playwright is disabled by default for addon runtime. Site modules should rely
on request/HTML parsing fallbacks. To enable Playwright explicitly for local
debugging, set environment variable: CUMINATION_ALLOW_PLAYWRIGHT=1
"""

import os
import sys
import warnings
from typing import Optional, Dict

# Try to import playwright - if it fails, we will use npx playwright as fallback
HAS_PLAYWRIGHT_PY = False
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT_PY = True
except (ImportError, Exception):
    pass


def _is_kodi_runtime() -> bool:
    """
    Detect Kodi runtime.
    In Kodi, external browser/node execution is unavailable or unreliable.
    """
    if "xbmc" in sys.modules:
        return True
    try:
        import xbmc  # type: ignore

        return bool(xbmc)
    except Exception:
        return False


def _playwright_enabled() -> bool:
    return os.environ.get("CUMINATION_ALLOW_PLAYWRIGHT") == "1"


def _raise_playwright_disabled():
    raise ImportError(
        "Playwright is disabled for addon runtime (set CUMINATION_ALLOW_PLAYWRIGHT=1 for local debugging only)"
    )

# Try to import stealth - it's optional but recommended
HAS_STEALTH = False
stealth_sync = None

try:
    from playwright_stealth import Stealth
    stealth_obj = Stealth()
    stealth_sync = stealth_obj.apply_stealth_sync
    HAS_STEALTH = True
except (ImportError, Exception):
    pass

# Fallback if stealth not available
if not HAS_STEALTH:
    def stealth_sync(page):
        """Dummy stealth function if playwright-stealth not available."""
        pass


def fetch_with_playwright(
    url: str,
    wait_for: str = "networkidle",
    wait_for_selector: Optional[str] = None,
    timeout: int = 30000,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    """
    Fetch HTML content using Playwright (headless Chromium).
    """
    if _is_kodi_runtime() or not _playwright_enabled():
        _raise_playwright_disabled()

    if not HAS_PLAYWRIGHT_PY:
        raise ImportError("Python playwright package not available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Set headers if provided
        if headers:
            context.set_extra_http_headers(headers)
        else:
            # Default user agent
            context.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            )

        page = context.new_page()
        _apply_stealth(page)

        try:
            # Navigate to the URL
            page.goto(url, wait_until=wait_for, timeout=timeout)

            # Wait for specific selector if provided
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=timeout)

            # Get the fully-rendered HTML
            html = page.content()

            return html

        finally:
            browser.close()


def sniff_video_url(
    url: str,
    play_selectors: Optional[list] = None,
    timeout: int = 30000,
    wait_after_click: int = 3000,
    debug: bool = False,
    exclude_domains: Optional[list] = None,
    preferred_extension: Optional[str] = None,
) -> Optional[str]:
    """
    Navigate to a URL, perform optional clicks (to trigger players),
    and sniff the network for the first video stream URL.
    """
    if _is_kodi_runtime() or not _playwright_enabled():
        _raise_playwright_disabled()

    if not HAS_PLAYWRIGHT_PY:
        raise ImportError("Python playwright package not available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        _apply_stealth(page)

        found_url = [None]
        all_video_urls = []

        def handle_response(response):
            r_url = response.url.lower()
            if any(ext in r_url for ext in [".mp4", ".m3u8", ".m4s"]) and not any(x in r_url for x in ["/thumbs/", "/images/", ".jpg", ".png", "/thumb/", "/image/"]):
                
                # Check exclusion list
                if exclude_domains and any(domain.lower() in r_url for domain in exclude_domains):
                    return

                if response.url not in all_video_urls:
                    all_video_urls.append(response.url)
                    
                    # If this matches our preferred extension, update immediately
                    if preferred_extension and preferred_extension.lower() in r_url:
                        found_url[0] = response.url
                    
                    elif not found_url[0]:
                        found_url[0] = response.url

        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="load", timeout=timeout)
            page.wait_for_timeout(3000)

            if play_selectors:
                clicked = False
                for selector in play_selectors:
                    if found_url[0]:
                        break

                    try:
                        elements = page.locator(selector)
                        count = elements.count()

                        for i in range(count):
                            elem = elements.nth(i)
                            if elem.is_visible(timeout=2000):
                                elem.click(timeout=5000, force=True)
                                clicked = True
                                page.wait_for_timeout(wait_after_click)
                                if found_url[0]:
                                    break

                        if clicked and found_url[0]:
                            break

                        if not clicked:
                            for frame in page.frames:
                                if frame == page.main_frame:
                                    continue
                                try:
                                    target = frame.locator(selector).first
                                    if target.is_visible(timeout=1000):
                                        target.click()
                                        clicked = True
                                        page.wait_for_timeout(wait_after_click)
                                        break
                                except Exception:
                                    continue

                        if found_url[0]:
                            break

                    except Exception:
                        continue

            # Wait a bit more
            for i in range(20):
                if found_url[0]:
                    break
                page.wait_for_timeout(500)

            return found_url[0]

        finally:
            browser.close()


def _apply_stealth(page) -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Stealth has already been applied to this page or context\\. Skipping duplicate application\\.",
            category=UserWarning,
        )
        stealth_sync(page)


def sniff_video_url_npx(
    url: str,
    play_selectors: Optional[list] = None,
    timeout: int = 30000,
    wait_after_click: int = 3000,
    debug: bool = False,
    exclude_domains: Optional[list] = None,
    preferred_extension: Optional[str] = None,
) -> Optional[str]:
    """
    Deprecated: npx/node fallback is disabled for addon compatibility.
    """
    from resources.lib import utils
    utils.kodilog("playwright_helper: npx/node fallback disabled")
    return None


def fetch_with_playwright_npx(
    url: str,
    wait_for: str = "networkidle",
    wait_for_selector: Optional[str] = None,
    timeout: int = 30000,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    """
    Deprecated: npx/node fallback is disabled for addon compatibility.
    """
    from resources.lib import utils
    utils.kodilog("playwright_helper: npx/node fallback disabled")
    return ""
