#!/usr/bin/env python3
"""Audit site modules and smoke results to guide site profile rollout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITES_DIR = ROOT / "plugin.video.cumination" / "resources" / "lib" / "sites"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import live_smoke_test


def load_latest_smoke(results_dir: Path) -> dict[str, Any]:
    candidates = sorted(results_dir.glob("live_smoke_*.json"))
    if not candidates:
        return {"summary": {}, "sites": []}
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def load_smoke_report(results_dir: Path, smoke_report: str | None = None) -> dict[str, Any]:
    if smoke_report:
        return json.loads(Path(smoke_report).read_text(encoding="utf-8"))
    return load_latest_smoke(results_dir)


def site_source_info(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "has_list": "def List(" in text,
        "has_categories": "def Categories(" in text or "def Cat(" in text,
        "has_search": "def Search(" in text,
        "has_play": "def Playvid(" in text,
        "adultsite_count": text.count("AdultSite("),
    }


def classify_priority(site_name: str, smoke_site: dict[str, Any], profile: dict[str, Any]) -> str:
    tier = profile.get("tier", 99)
    overall = smoke_site.get("overall", "UNKNOWN")
    if tier == 1 and overall in {"FAIL", "WARN"}:
        return "tier1_hot"
    if overall == "FAIL":
        return "failing"
    if overall == "WARN":
        return "warn"
    if tier == 1:
        return "tier1"
    return "backlog"


def build_audit(results_dir: Path, smoke_report: str | None = None) -> dict[str, Any]:
    smoke = load_smoke_report(results_dir, smoke_report)
    smoke_sites = {site["site"]: site for site in smoke.get("sites", [])}
    site_names = live_smoke_test.discover_site_names()

    rows = []
    for site_name in site_names:
        profile = live_smoke_test.get_site_profile(site_name)
        smoke_site = smoke_sites.get(site_name, {})
        source = site_source_info(SITES_DIR / f"{site_name}.py")
        rows.append(
            {
                "site": site_name,
                "priority": classify_priority(site_name, smoke_site, profile),
                "tier": profile.get("tier"),
                "overall": smoke_site.get("overall", "UNKNOWN"),
                "content_type": profile.get("content_type", "video"),
                "requires_flaresolverr": bool(profile.get("requires_flaresolverr", False)),
                "supports": profile.get("supports", {}),
                "harness": profile.get("harness", {}),
                "source": source,
                "smoke_steps": smoke_site.get("steps", {}),
            }
        )

    priority_order = {
        "tier1_hot": 0,
        "failing": 1,
        "warn": 2,
        "tier1": 3,
        "backlog": 4,
    }
    rows.sort(key=lambda row: (priority_order.get(row["priority"], 99), row["site"]))

    return {
        "summary": {
            "sites": len(rows),
            "tier1_hot": sum(1 for row in rows if row["priority"] == "tier1_hot"),
            "failing": sum(1 for row in rows if row["priority"] == "failing"),
            "warn": sum(1 for row in rows if row["priority"] == "warn"),
            "tier1": sum(1 for row in rows if row["priority"] == "tier1"),
            "backlog": sum(1 for row in rows if row["priority"] == "backlog"),
        },
        "sites": rows,
    }


def render_markdown(audit: dict[str, Any]) -> str:
    lines = ["# Site Profile Audit", ""]
    summary = audit["summary"]
    lines.append(f"- Sites: `{summary['sites']}`")
    lines.append(f"- Tier1 hot: `{summary['tier1_hot']}`")
    lines.append(f"- Failing: `{summary['failing']}`")
    lines.append(f"- Warn: `{summary['warn']}`")
    lines.append("")
    lines.append("| Site | Priority | Overall | Tier | Type | FS | List | Cat | Search | Play |")
    lines.append("|---|---|---|---:|---|---|---|---|---|---|")
    for row in audit["sites"]:
        supports = row["supports"]
        lines.append(
            f"| {row['site']} | {row['priority']} | {row['overall']} | {row.get('tier') or ''} | "
            f"{row['content_type']} | {'Y' if row['requires_flaresolverr'] else ''} | "
            f"{'Y' if supports.get('list', True) else ''} | "
            f"{'Y' if supports.get('categories', True) else ''} | "
            f"{'Y' if supports.get('search', True) else ''} | "
            f"{'Y' if supports.get('play', True) else ''} |"
        )

    lines.append("")
    lines.append("## Next Batch")
    lines.append("")
    for row in audit["sites"][:20]:
        step_failures = [
            f"{name}:{data.get('status')}"
            for name, data in row.get("smoke_steps", {}).items()
            if data.get("status") == "FAIL"
        ]
        details = f" | failures: {', '.join(step_failures)}" if step_failures else ""
        lines.append(f"- **{row['site']}** ({row['priority']}, tier={row.get('tier')}){details}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit site profiles against latest smoke results.")
    parser.add_argument("--results-dir", default=str(ROOT / "results"))
    parser.add_argument("--smoke-report")
    parser.add_argument("--json-out")
    parser.add_argument("--md-out")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = build_audit(Path(args.results_dir), args.smoke_report)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(render_markdown(audit), encoding="utf-8")
    print(json.dumps(audit["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
