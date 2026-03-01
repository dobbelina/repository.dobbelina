import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

def get_addon_version(addon_dir):
    addon_xml = Path(addon_dir) / "addon.xml"
    if not addon_xml.exists():
        return None
    tree = ET.parse(addon_xml)
    return tree.getroot().get("version")

def get_recent_commits(count=10):
    try:
        # Get commits since last tag or just last N commits
        # We filter out automated chore/bump commits
        cmd = ["git", "log", f"-n", str(count), "--pretty=format:- %s"]
        output = subprocess.check_output(cmd, text=True).splitlines()
        
        filtered = []
        for line in output:
            # Skip automated commits
            if any(x in line.lower() for x in ["chore: auto-bump", "skip ci", "merge branch"]):
                continue
            filtered.append(line)
        return filtered
    except Exception as e:
        print(f"Error getting commits: {e}")
        return []

def update_changelog(addon_dir):
    changelog_path = Path(addon_dir) / "changelog.txt"
    version = get_addon_version(addon_dir)
    if not version:
        print("Could not find addon version")
        return

    commits = get_recent_commits()
    if not commits:
        print("No new commits found to add to changelog")
        return

    new_entry = f"[B]Version {version}[/B]\n" + "\n".join(commits) + "\n\n"
    
    current_content = ""
    if changelog_path.exists():
        current_content = changelog_path.read_text(encoding="utf-8")

    # Check if this version is already at the top
    if f"[B]Version {version}[/B]" in current_content[:100]:
        print(f"Version {version} already exists in changelog, skipping update.")
        return

    updated_content = new_entry + current_content
    changelog_path.write_text(updated_content, encoding="utf-8")
    print(f"Updated changelog for version {version}")

if __name__ == "__main__":
    update_changelog("plugin.video.cumination")
