#!/usr/bin/env python3
"""Compare two live smoke reports and emit a health delta summary."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_RANK = {
    "PASS": 0,
    "SKIP": 1,
    "WARN": 2,
    "FAIL": 3,
    "ERROR": 4,
}

STEP_STATUS_RANK = {
    "PASS": 0,
    "SKIP": 1,
    "FAIL": 2,
}


def classify_message(msg: str) -> str:
    lowered = (msg or "").lower()
    if any(
        token in lowered
        for token in (
            "cloudflare",
            "challenge",
            "captcha",
            "blocked",
            "forbidden",
            "403",
            "429",
            "451",
        )
    ):
        return "BLOCKED"
    if any(
        token in lowered
        for token in ("timeout", "timed out", "connection", "network", "dns")
    ):
        return "NETWORK"
    if any(token in lowered for token in ("no videos", "no items", "empty")):
        return "PARSER"
    if any(
        token in lowered
        for token in (
            "jsondecodeerror",
            "indexerror",
            "keyerror",
            "typeerror",
            "valueerror",
            "attributeerror",
            "traceback",
            "exception",
            "unboundlocalerror",
        )
    ):
        return "CODE"
    if any(token in lowered for token in ("playback", "resolve", "stream", "m3u8", "mp4")):
        return "PLAYBACK"
    return "UNKNOWN"


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_latest_report(results_dir: Path) -> Path:
    candidates = sorted(results_dir.glob("live_smoke_*.json"))
    if not candidates:
        raise FileNotFoundError(f"No live smoke reports found in {results_dir}")
    return candidates[-1]


def get_sites(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {site["site"]: site for site in report.get("sites", [])}


def overall_rank(status: str) -> int:
    return STATUS_RANK.get(status or "ERROR", 99)


def step_rank(status: str) -> int:
    return STEP_STATUS_RANK.get(status or "FAIL", 99)


def failure_class(site: dict[str, Any]) -> str:
    if site.get("error"):
        return classify_message(site.get("error", ""))
    for data in site.get("steps", {}).values():
        if data.get("status") == "FAIL":
            return classify_message(data.get("message", ""))
    notifications = site.get("notifications") or []
    if notifications:
        return classify_message(notifications[-1])
    return "UNKNOWN"


@dataclass
class SiteDelta:
    site: str
    previous: str
    current: str
    kind: str
    detail: str = ""


def compare_reports(
    current_report: dict[str, Any], previous_report: dict[str, Any] | None
) -> dict[str, Any]:
    current_sites = get_sites(current_report)
    previous_sites = get_sites(previous_report or {})

    deltas: list[SiteDelta] = []
    new_failures: list[dict[str, Any]] = []
    resolved_failures: list[dict[str, Any]] = []
    persistent_failures: list[dict[str, Any]] = []
    improved_sites: list[dict[str, Any]] = []
    step_regressions: list[dict[str, Any]] = []

    all_names = sorted(set(current_sites) | set(previous_sites))
    for name in all_names:
        current = current_sites.get(name)
        previous = previous_sites.get(name)
        current_status = current.get("overall", "MISSING") if current else "MISSING"
        previous_status = previous.get("overall", "MISSING") if previous else "MISSING"

        if previous is None:
            deltas.append(SiteDelta(name, previous_status, current_status, "new_site"))
            continue
        if current is None:
            deltas.append(SiteDelta(name, previous_status, current_status, "missing_site"))
            continue

        if overall_rank(current_status) > overall_rank(previous_status):
            deltas.append(SiteDelta(name, previous_status, current_status, "regression"))
        elif overall_rank(current_status) < overall_rank(previous_status):
            deltas.append(SiteDelta(name, previous_status, current_status, "improvement"))

        prev_is_fail = previous_status in {"FAIL", "ERROR"}
        curr_is_fail = current_status in {"FAIL", "ERROR"}
        if curr_is_fail and not prev_is_fail:
            new_failures.append(
                {
                    "site": name,
                    "previous": previous_status,
                    "current": current_status,
                    "class": failure_class(current),
                    "message": site_failure_message(current),
                }
            )
        elif prev_is_fail and not curr_is_fail:
            resolved_failures.append(
                {
                    "site": name,
                    "previous": previous_status,
                    "current": current_status,
                }
            )
        elif prev_is_fail and curr_is_fail:
            persistent_failures.append(
                {
                    "site": name,
                    "previous": previous_status,
                    "current": current_status,
                    "class": failure_class(current),
                    "message": site_failure_message(current),
                }
            )
        elif overall_rank(current_status) < overall_rank(previous_status):
            improved_sites.append(
                {
                    "site": name,
                    "previous": previous_status,
                    "current": current_status,
                }
            )

        current_steps = current.get("steps", {})
        previous_steps = previous.get("steps", {})
        for step_name in sorted(set(current_steps) | set(previous_steps)):
            current_step = current_steps.get(step_name, {})
            previous_step = previous_steps.get(step_name, {})
            current_step_status = current_step.get("status", "MISSING")
            previous_step_status = previous_step.get("status", "MISSING")
            if (
                current_step_status == "FAIL"
                and previous_step_status != "FAIL"
                and step_rank(current_step_status) > step_rank(previous_step_status)
            ):
                step_regressions.append(
                    {
                        "site": name,
                        "step": step_name,
                        "previous": previous_step_status,
                        "current": current_step_status,
                        "message": current_step.get("message", ""),
                        "class": classify_message(current_step.get("message", "")),
                    }
                )

    current_summary = current_report.get("summary", {})
    previous_summary = (previous_report or {}).get("summary", {})
    return {
        "current": {
            "generated": current_summary.get("generated"),
            "sites_total": current_summary.get("sites_total"),
            "pass": current_summary.get("pass"),
            "warn": current_summary.get("warn"),
            "fail": current_summary.get("fail"),
            "error": current_summary.get("error"),
            "skip": current_summary.get("skip"),
        },
        "previous": {
            "generated": previous_summary.get("generated"),
            "sites_total": previous_summary.get("sites_total"),
            "pass": previous_summary.get("pass"),
            "warn": previous_summary.get("warn"),
            "fail": previous_summary.get("fail"),
            "error": previous_summary.get("error"),
            "skip": previous_summary.get("skip"),
        }
        if previous_report
        else None,
        "summary": {
            "new_failures": len(new_failures),
            "resolved_failures": len(resolved_failures),
            "persistent_failures": len(persistent_failures),
            "improved_sites": len(improved_sites),
            "regressions": sum(1 for delta in deltas if delta.kind == "regression"),
            "step_regressions": len(step_regressions),
        },
        "new_failures": new_failures,
        "resolved_failures": resolved_failures,
        "persistent_failures": persistent_failures,
        "improved_sites": improved_sites,
        "step_regressions": step_regressions,
        "deltas": [delta.__dict__ for delta in deltas],
    }


def site_failure_message(site: dict[str, Any]) -> str:
    if site.get("error"):
        return site["error"]
    for step_name, data in site.get("steps", {}).items():
        if data.get("status") == "FAIL":
            return f"{step_name}: {data.get('message', '')}"
    notifications = site.get("notifications") or []
    return notifications[-1] if notifications else ""


def render_markdown(diff: dict[str, Any], current_path: Path, previous_path: Path | None) -> str:
    lines = ["# Site Health Delta", ""]
    lines.append(f"- Current report: `{current_path.name}`")
    if previous_path:
        lines.append(f"- Previous report: `{previous_path.name}`")
    else:
        lines.append("- Previous report: `none`")
    lines.append("")

    current = diff["current"]
    previous = diff.get("previous")
    lines.append("## Snapshot")
    lines.append("")
    if previous:
        lines.append(
            f"- Current: `PASS {current.get('pass', 0)}` | `WARN {current.get('warn', 0)}` | `FAIL {current.get('fail', 0)}` | `ERROR {current.get('error', 0)}` | `SKIP {current.get('skip', 0)}`"
        )
        lines.append(
            f"- Previous: `PASS {previous.get('pass', 0)}` | `WARN {previous.get('warn', 0)}` | `FAIL {previous.get('fail', 0)}` | `ERROR {previous.get('error', 0)}` | `SKIP {previous.get('skip', 0)}`"
        )
    else:
        lines.append(
            f"- Current: `PASS {current.get('pass', 0)}` | `WARN {current.get('warn', 0)}` | `FAIL {current.get('fail', 0)}` | `ERROR {current.get('error', 0)}` | `SKIP {current.get('skip', 0)}`"
        )
    lines.append("")

    summary = diff["summary"]
    lines.append("## Delta Summary")
    lines.append("")
    lines.append(f"- New failures: `{summary['new_failures']}`")
    lines.append(f"- Resolved failures: `{summary['resolved_failures']}`")
    lines.append(f"- Persistent failures: `{summary['persistent_failures']}`")
    lines.append(f"- Site regressions: `{summary['regressions']}`")
    lines.append(f"- Step regressions: `{summary['step_regressions']}`")
    lines.append("")

    sections = [
        ("New Failures", diff["new_failures"], lambda item: f"- **{item['site']}**: `{item['previous']} -> {item['current']}` ({item['class']}) | {item['message']}"),
        ("Resolved Failures", diff["resolved_failures"], lambda item: f"- **{item['site']}**: `{item['previous']} -> {item['current']}`"),
        ("Persistent Failures", diff["persistent_failures"], lambda item: f"- **{item['site']}**: `{item['previous']} -> {item['current']}` ({item['class']}) | {item['message']}"),
        ("Step Regressions", diff["step_regressions"], lambda item: f"- **{item['site']}** `{item['step']}`: `{item['previous']} -> {item['current']}` ({item['class']}) | {item['message']}"),
        ("Improvements", diff["improved_sites"], lambda item: f"- **{item['site']}**: `{item['previous']} -> {item['current']}`"),
    ]

    for title, items, formatter in sections:
        if not items:
            continue
        lines.append(f"## {title}")
        lines.append("")
        for item in items:
            lines.append(formatter(item))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare live smoke reports.")
    parser.add_argument("--current", help="Current smoke report JSON path")
    parser.add_argument("--previous", help="Previous smoke report JSON path")
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory used to auto-detect the latest report",
    )
    parser.add_argument(
        "--json-out",
        help="Optional output path for the diff JSON",
    )
    parser.add_argument(
        "--md-out",
        help="Optional output path for the diff Markdown",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    current_path = Path(args.current) if args.current else find_latest_report(results_dir)
    previous_path = Path(args.previous) if args.previous else None

    current_report = load_report(current_path)
    previous_report = load_report(previous_path) if previous_path and previous_path.exists() else None
    diff = compare_reports(current_report, previous_report)

    if args.json_out:
        json_out = Path(args.json_out)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(diff, indent=2), encoding="utf-8")

    if args.md_out:
        md_out = Path(args.md_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(
            render_markdown(diff, current_path=current_path, previous_path=previous_path),
            encoding="utf-8",
        )

    print(json.dumps(diff, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
