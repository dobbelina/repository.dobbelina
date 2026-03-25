#!/usr/bin/env python3
import os
import sys

# Enable Playwright for this script BEFORE ANY OTHER IMPORTS
os.environ["CUMINATION_ALLOW_PLAYWRIGHT"] = "1"

"""Playwright Smoke Runner for Cumination Sites.

This script performs a live verification of all site modules in plugin.video.cumination.
It uses a two-stage approach:
1. Standard Fetch (requests/urllib): Fast, mimics Kodi behavior.
2. Playwright Fallback: If stage 1 is blocked by Cloudflare or JS, use Playwright to see if the site is still accessible.
3. Sniff Check: On a sample video page, use Playwright network sniffing to see if a video stream can be found.

Reports are saved to results/playwright_smoke_[timestamp].md
"""
import time
import json
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "plugin.video.cumination"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PLUGIN_PATH))

# Enable Playwright for this script BEFORE imports
os.environ["CUMINATION_ALLOW_PLAYWRIGHT"] = "1"

# Mock sys.argv for Kodi-style execution before importing plugin modules
real_argv = sys.argv[:]
sys.argv = ["plugin.video.cumination", "1", ""]

# Mock Kodi modules before importing anything else
import types


def mock_kodi():
    if "kodi_six" in sys.modules:
        return

    # Mock xbmc modules
    for name in [
        "xbmc",
        "xbmcgui",
        "xbmcplugin",
        "xbmcvfs",
        "xbmcaddon",
        "StorageServer",
        "CommonFunctions",
        "requests",
        "websocket",
    ]:
        mock = types.ModuleType(name)
        if name == "requests":
            mock.Session = lambda: types.SimpleNamespace(
                get=lambda *args, **kwargs: None, headers={}
            )
            mock.get = lambda *args, **kwargs: None
            mock.post = lambda *args, **kwargs: None
        if name == "websocket":
            mock.WebSocket = lambda: None
            mock.create_connection = lambda *args, **kwargs: None
        if name == "xbmc":
            mock.LOGDEBUG = 0
            mock.LOGINFO = 1
            mock.log = lambda *args, **kwargs: None
            mock.translatePath = lambda p: p
        if name == "xbmcvfs":
            mock.translatePath = lambda p: p
        if name == "xbmcgui":

            class Dialog:
                def __init__(self):
                    pass

                def ok(self, *args):
                    return True

                def notification(self, *args):
                    pass

            class DialogProgress:
                def __init__(self):
                    pass

                def create(self, *args):
                    pass

                def update(self, *args):
                    pass

                def close(self):
                    pass

            class ListItem:
                def __init__(self, *args, **kwargs):
                    pass

                def setArt(self, *args):
                    pass

                def setInfo(self, *args):
                    pass

                def addContextMenuItems(self, *args):
                    pass

                def setProperty(self, *args):
                    pass

            mock.Dialog = Dialog
            mock.DialogProgress = DialogProgress
            mock.ListItem = ListItem
        if name == "xbmcplugin":
            mock.addDirectoryItem = lambda *args, **kwargs: True
            mock.addDirectoryItems = lambda *args, **kwargs: True
            mock.endOfDirectory = lambda *args, **kwargs: True
            mock.setContent = lambda *args, **kwargs: True
            mock.setResolvedUrl = lambda *args, **kwargs: True
        if name == "xbmcaddon":

            class Addon:
                def __init__(self, id=None):
                    pass

                def getSetting(self, id):
                    if id in ["cache_time", "qualityask", "sortxt", "content"]:
                        return "0"
                    return "false"

                def setSetting(self, id, val):
                    pass

                def getLocalizedString(self, id):
                    return str(id)

                def getAddonInfo(self, id):
                    if id == "version":
                        return "20.0.0"
                    if id == "path":
                        return str(PLUGIN_PATH)
                    if id == "profile":
                        return str(ROOT / "userdata")
                    return "."

            mock.Addon = Addon
        if name == "StorageServer":

            class Storage:
                def __init__(self, id, time):
                    pass

                def set(self, key, val):
                    pass

                def get(self, key):
                    return None

                def cacheFunction(self, f, *args, **kwargs):
                    return f(*args, **kwargs)

            mock.StorageServer = Storage
        sys.modules[name] = mock

    # Mock kodi_six
    kodi_six = types.ModuleType("kodi_six")
    for name in ["xbmc", "xbmcgui", "xbmcplugin", "xbmcvfs", "xbmcaddon"]:
        setattr(kodi_six, name, sys.modules[name])
    sys.modules["kodi_six"] = kodi_six


mock_kodi()

# Now imports that depend on mocks
from resources.lib import utils
from resources.lib import playwright_helper
from resources.lib.playwright_helper import fetch_with_playwright

# Override Kodi detection so Playwright works during testing
playwright_helper._is_kodi_runtime = lambda: False


class SmokeRunner:
    def __init__(self):
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = ROOT / "results"
        self.output_dir.mkdir(exist_ok=True)

    def run_site_test(self, site_name: str, quiet: bool = False) -> Dict[str, Any]:
        if not quiet:
            print(f"\n--- Testing Site: {site_name} ---")

        # 1. Load the site module
        try:
            module_path = f"resources.lib.sites.{site_name}"
            # Reload if already imported
            if module_path in sys.modules:
                importlib.reload(sys.modules[module_path])
            module = importlib.import_module(module_path)
            site_obj = getattr(module, "site", None)
            if not site_obj:
                return {
                    "site": site_name,
                    "status": "ERROR",
                    "message": "No 'site' object found in module",
                }
        except Exception as e:
            return {
                "site": site_name,
                "status": "ERROR",
                "message": f"Import error: {str(e)}",
            }

        result = {
            "site": site_name,
            "url": site_obj.url,
            "standard_fetch": "UNKNOWN",
            "playwright_fetch": "UNKNOWN",
            "cloudflare_detected": False,
            "sniff_result": "N/A",
            "status": "FAIL",
            "notes": [],
        }

        # 2. Standard Fetch Test
        try:
            html = utils.getHtml(site_obj.url)
            if html and len(html) > 500:
                if (
                    "Cloudflare" in html
                    or "Just a moment" in html
                    or "Verify you are human" in html
                ):
                    result["standard_fetch"] = "BLOCKED"
                    result["cloudflare_detected"] = True
                    result["notes"].append("Blocked by Cloudflare in standard fetch.")
                else:
                    result["standard_fetch"] = "OK"
                    result["status"] = "PASS"
            else:
                result["standard_fetch"] = "EMPTY/SMALL"
                result["notes"].append(
                    f"Standard fetch returned minimal content ({len(html) if html else 0} bytes)."
                )
        except Exception as e:
            result["standard_fetch"] = "ERROR"
            result["notes"].append(f"Standard fetch error: {str(e)}")

        # 3. Playwright Fetch (if blocked or failed)
        if result["standard_fetch"] != "OK" or result["cloudflare_detected"]:
            if not quiet:
                print(f"  Standard fetch failed for {site_name}, trying Playwright...")
            try:
                pw_html = fetch_with_playwright(site_obj.url, timeout=30000)
                if pw_html and len(pw_html) > 500:
                    if "Cloudflare" in pw_html or "Just a moment" in pw_html:
                        result["playwright_fetch"] = "BLOCKED"
                        result["notes"].append("Playwright also blocked by Cloudflare.")
                    else:
                        result["playwright_fetch"] = "OK"
                        result["status"] = "OK (PLAYWRIGHT ONLY)"
                        result["notes"].append(
                            "Accessible via Playwright (JS required)."
                        )
                else:
                    result["playwright_fetch"] = "EMPTY"
            except Exception as e:
                result["playwright_fetch"] = "ERROR"
                result["notes"].append(f"Playwright fetch error: {str(e)}")

        # 4. Sniff Check (Optional: on a sample video page if possible)
        # For simplicity, we'll skip this unless explicitly requested or if we find a link
        # But for now, let's just mark the main page status

        if not quiet:
            print(f"  Result: {result['status']}")
        return result

    def generate_report(self):
        report_path = self.output_dir / f"playwright_smoke_{self.timestamp}.md"
        json_path = self.output_dir / f"playwright_smoke_{self.timestamp}.json"

        # Save JSON data
        with open(json_path, "w") as f:
            json.dump(
                {"timestamp": self.timestamp, "results": self.results}, f, indent=2
            )

        # Create Markdown
        lines = [
            f"# Cumination Playwright Smoke Test Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"| Total Sites | Standard OK | Playwright Only | Blocked/Failed |",
            f"|-------------|-------------|-----------------|----------------|",
        ]

        total = len(self.results)
        std_ok = len([r for r in self.results if r.get("standard_fetch") == "OK"])
        pw_ok = len(
            [r for r in self.results if r.get("status") == "OK (PLAYWRIGHT ONLY)"]
        )
        failed = total - std_ok - pw_ok

        lines.append(f"| {total} | {std_ok} | {pw_ok} | {failed} |")
        lines.append("")
        lines.append("## Detailed Results")
        lines.append("")
        lines.append("| Site | URL | Std Fetch | PW Fetch | Status | Notes |")
        lines.append("|------|-----|-----------|----------|--------|-------|")

        for r in self.results:
            status = r.get("status", "UNKNOWN")
            status_icon = "✅" if "OK" in status or status == "PASS" else "❌"
            notes = "; ".join(r.get("notes", []))
            if r.get("message"):
                notes += f" {r['message']}"
            lines.append(
                f"| {r.get('site')} | {r.get('url')} | {r.get('standard_fetch')} | {r.get('playwright_fetch')} | {status_icon} {status} | {notes} |"
            )

        with open(report_path, "w") as f:
            f.write("\n".join(lines))

        print(f"\nReport saved to: {report_path}")

    def run_all(self, limit: Optional[int] = None):
        sites_dir = PLUGIN_PATH / "resources" / "lib" / "sites"
        all_sites = [f.stem for f in sites_dir.glob("*.py") if f.stem != "__init__"]
        all_sites.sort()

        if limit:
            all_sites = all_sites[:limit]

        print(f"Starting smoke test for {len(all_sites)} sites...")

        for site in all_sites:
            try:
                res = self.run_site_test(site)
                self.results.append(res)
            except KeyboardInterrupt:
                print("\nInterrupted by user.")
                break
            except Exception as e:
                print(f"Unhandled error testing {site}: {e}")
                self.results.append(
                    {"site": site, "status": "CRASH", "message": str(e)}
                )

        self.generate_report()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--site", help="Test a specific site")
    parser.add_argument("--limit", type=int, help="Limit number of sites to test")
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    # Use real_argv excluding the script name for parsing
    args = parser.parse_args(real_argv[1:])

    runner = SmokeRunner()
    if args.site:
        res = runner.run_site_test(args.site, quiet=args.json)
        runner.results.append(res)
        if args.json:
            print(json.dumps(res))
        else:
            runner.generate_report()
    else:
        runner.run_all(limit=args.limit)
