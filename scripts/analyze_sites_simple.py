#!/usr/bin/env python3
"""Site Structure Analyzer - Simplified Version

Uses existing pytest Kodi mocks from tests/conftest.py
Run from repository root: python scripts/analyze_sites_simple.py
"""

import sys
from pathlib import Path

# Add paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))  # For conftest
sys.path.insert(0, str(ROOT / "plugin.video.cumination"))
from conftest import *  # This sets up all Kodi mocks

# Now import our analysis modules
import json
import re

SITES_DIR = ROOT / "plugin.video.cumination" / "resources" / "lib" / "sites"


def analyze_source(file_path):
    """Quick source code analysis"""
    source = file_path.read_text(encoding="utf-8")
    return {
        "uses_beautifulsoup": bool(
            re.search(r"\bparse_html\b|\bBeautifulSoup\b", source)
        ),
        "uses_regex": bool(re.search(r"\bre\.compile\b|\bre\.findall\b", source)),
        "uses_soup_spec": bool(re.search(r"\bSoupSiteSpec\b", source)),
        "source_lines": len(source.splitlines()),
    }


def main():
    print("\nQuick Site Analysis")
    print("=" * 60)

    sites = []
    for file_path in sorted(SITES_DIR.glob("*.py")):
        name = file_path.stem
        if name in {"__init__", "soup_spec"}:
            continue

        analysis = analyze_source(file_path)
        sites.append({"name": name, **analysis})

    # Summary
    bs_sites = [s for s in sites if s["uses_beautifulsoup"]]
    regex_only = [s for s in sites if s["uses_regex"] and not s["uses_beautifulsoup"]]
    soup_spec = [s for s in sites if s["uses_soup_spec"]]

    print(f"\nTotal sites: {len(sites)}")
    print(f"BeautifulSoup: {len(bs_sites)}")
    print(f"Regex-only: {len(regex_only)}")
    print(f"SoupSiteSpec: {len(soup_spec)}")

    # Show regex-only sites
    if regex_only:
        print(f"\nSites still using regex ({len(regex_only)}):")
        for site in regex_only[:20]:
            print(f"  - {site['name']}")
        if len(regex_only) > 20:
            print(f"  ... and {len(regex_only) - 20} more")

    # Save report
    output = ROOT / "results" / "quick_site_analysis.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "summary": {
                    "total": len(sites),
                    "beautifulsoup": len(bs_sites),
                    "regex_only": len(regex_only),
                    "soup_spec": len(soup_spec),
                },
                "sites": sites,
                "regex_only_sites": [s["name"] for s in regex_only],
                "beautifulsoup_sites": [s["name"] for s in bs_sites],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nReport saved to: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
