#!/usr/bin/env python3
"""
Builds Kodi add-on ZIPs with a correct folder root and forward-slash paths,
then optionally updates addons.xml and its MD5 checksum.

Usage examples:
  python build_repo_addons.py                       # build all add-ons found
  python build_repo_addons.py --addons plugin.video.cumination
  python build_repo_addons.py --out . --update-index

This script intentionally:
  - Writes entries with POSIX '/' separators (Kodi requirement)
  - Ensures a single top-level folder in the zip: '<addon_id>/'
  - Excludes previously built '*.zip', '__pycache__', '.git', '.github'
  - Updates 'addons.xml' version attributes for built add-ons and regenerates
    'addons.xml.md5' if --update-index is specified
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, List, Tuple
import zipfile


EXCLUDED_DIRS = {".git", ".github", "__pycache__"}
EXCLUDED_SUFFIXES = {".zip", ".pyc"}
EXCLUDED_FILES = {"Thumbs.db", ".DS_Store"}


def is_excluded(path: Path, addon_root: Path) -> bool:
    rel_parts = path.relative_to(addon_root).parts
    # Exclude known directories anywhere in the tree
    if any(p in EXCLUDED_DIRS for p in rel_parts):
        return True
    # Exclude by suffix or filename
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name in EXCLUDED_FILES:
        return True
    return False


def read_addon_meta(addon_dir: Path) -> Tuple[str, str]:
    addon_xml = addon_dir / "addon.xml"
    if not addon_xml.is_file():
        raise FileNotFoundError(f"Missing addon.xml in {addon_dir}")
    tree = ET.parse(addon_xml)
    root = tree.getroot()
    addon_id = root.get("id")
    version = root.get("version")
    if not addon_id or not version:
        raise ValueError(f"Could not read id/version from {addon_xml}")
    return addon_id, version


def build_zip(addon_dir: Path, out_dir: Path) -> Path:
    addon_id, version = read_addon_meta(addon_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{addon_id}-{version}.zip"

    # Create zip with normalized forward-slash entries under '<addon_id>/'
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in addon_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if is_excluded(file_path, addon_dir):
                continue
            rel = file_path.relative_to(addon_dir).as_posix()
            arcname = f"{addon_id}/{rel}"
            zf.write(file_path, arcname)

        # Sanity check: ensure no backslashes in names
        for info in zf.infolist():
            if "\\" in info.filename:
                raise RuntimeError(f"Backslash found in zip entry: {info.filename}")

    return zip_path


def find_addons(base_dir: Path, filter_ids: Iterable[str] | None) -> List[Path]:
    candidates = []
    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        addon_xml = child / "addon.xml"
        if addon_xml.is_file():
            if filter_ids:
                try:
                    addon_id, _ = read_addon_meta(child)
                except Exception:
                    continue
                if addon_id not in set(filter_ids):
                    continue
            candidates.append(child)
    return candidates


def update_addons_index(addons_xml_path: Path, updated: List[Tuple[str, str]]) -> None:
    if not addons_xml_path.is_file():
        print(f"addons.xml not found at {addons_xml_path}, skipping index update", file=sys.stderr)
        return

    tree = ET.parse(addons_xml_path)
    root = tree.getroot()
    updated_map = {aid: ver for aid, ver in updated}
    changed = False
    for addon in root.findall("addon"):
        aid = addon.get("id")
        if aid in updated_map:
            new_ver = updated_map[aid]
            if addon.get("version") != new_ver:
                addon.set("version", new_ver)
                changed = True

    if changed:
        # Write compact XML similar to input
        ET.indent(tree, space="", level=0) if hasattr(ET, "indent") else None
        tree.write(addons_xml_path, encoding="utf-8", xml_declaration=True)

    # Regenerate MD5 regardless to keep it in sync
    md5_path = addons_xml_path.with_suffix(addons_xml_path.suffix + ".md5")
    digest = hashlib.md5(addons_xml_path.read_bytes()).hexdigest()
    md5_path.write_text(digest, encoding="utf-8")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Build Kodi add-on ZIPs with proper structure")
    parser.add_argument("--addons", nargs="*", help="Specific add-on IDs to build (default: all in cwd)")
    parser.add_argument("--out", default=".", help="Output directory for ZIPs (default: current dir)")
    parser.add_argument("--update-index", action="store_true", help="Update addons.xml and addons.xml.md5")
    args = parser.parse_args(argv)

    base = Path.cwd()
    out_dir = Path(args.out)

    addon_dirs = find_addons(base, set(args.addons) if args.addons else None)
    if not addon_dirs:
        print("No add-ons found to build.")
        return 1

    built: List[Tuple[str, str]] = []
    for addon_dir in addon_dirs:
        addon_id, version = read_addon_meta(addon_dir)
        zip_path = build_zip(addon_dir, out_dir)
        built.append((addon_id, version))
        print(f"Built {zip_path}")

    if args.update_index:
        update_addons_index(base / "addons.xml", built)
        print("Updated addons.xml and addons.xml.md5")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

