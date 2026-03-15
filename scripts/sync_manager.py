#!/usr/bin/env python3
"""
Sync Manager for Dobbelina Repository Fork.
Automates identifying, analyzing, and cherry-picking commits from upstream.
"""

import subprocess
import re
import sys
from pathlib import Path
import csv
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Configuration
UPSTREAM_REMOTE = "https://github.com/dobbelina/repository.dobbelina.git"
REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_FILE = REPO_ROOT / "docs" / "development" / "UPSTREAM_SYNC.md"
AUDIT_FILE = REPO_ROOT / "bs4_migration_audit.csv"
SITES_DIR = REPO_ROOT / "plugin.video.cumination" / "resources" / "lib" / "sites"


class SyncManager:
    def __init__(self, dry_run=False, skip_changelog=True):
        self.dry_run = dry_run
        self.skip_changelog = skip_changelog
        self.bs4_sites = self._load_bs4_sites()
        self.tracked_hashes = self._load_tracked_hashes()
        self.integrated_in_git = self._load_git_history_hashes()

    def _run_git(self, args):
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="replace",
        )
        return result

    def _load_bs4_sites(self):
        if not AUDIT_FILE.exists():
            return set()
        bs4_sites = set()
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("BeautifulSoup", "").strip().lower() == "true":
                        bs4_sites.add(row["Site"].strip().lower())
        except Exception as e:
            print(f"Warning: Could not load audit file: {e}")
        return bs4_sites

    def _load_tracked_hashes(self):
        if not SYNC_FILE.exists():
            print(f"Warning: {SYNC_FILE} not found")
            return set()
        content = SYNC_FILE.read_text(encoding="utf-8")
        # Find all 7-character hex strings in backticks
        hashes = set(re.findall(r"`([0-9a-f]{7,40})`", content))
        return hashes

    def _load_git_history_hashes(self):
        # Find hashes mentioned in "cherry picked from commit ..."
        result = self._run_git(["log", "--all", "--grep=cherry picked from commit"])
        hashes = set(
            re.findall(r"cherry picked from commit ([0-9a-f]{7,40})", result.stdout)
        )
        return hashes

    def ensure_upstream(self):
        result = self._run_git(["remote"])
        if "upstream" not in result.stdout.split():
            print(f"Adding upstream remote: {UPSTREAM_REMOTE}")
            self._run_git(["remote", "add", "upstream", UPSTREAM_REMOTE])

        print("Fetching upstream...")
        self._run_git(["fetch", "upstream", "--quiet"])

    def get_new_commits(self):
        # Get commits in upstream/master not in origin/master
        result = self._run_git(
            [
                "log",
                "upstream/master",
                "--not",
                "origin/master",
                "--oneline",
                "--no-merges",
            ]
        )
        commits = []
        if not result.stdout or not result.stdout.strip():
            return []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue
            sha, msg = parts
            if "Bumped to v." in msg:
                continue
            commits.append({"sha": sha, "msg": msg})
        return commits

    def analyze_commit(self, sha):
        # Get files changed in this commit
        result = self._run_git(["show", "--name-only", "--format=", sha])
        files = result.stdout.strip().split("\n")

        # Get full commit message for deeper analysis
        msg_full = self._run_git(["show", "-s", "--format=%B", sha]).stdout.lower()

        sites_affected = set()
        changelog_affected = False
        for f in files:
            if "plugin.video.cumination/resources/lib/sites/" in f:
                site_name = Path(f).stem.lower()
                sites_affected.add(site_name)
            if "changelog.txt" in f:
                changelog_affected = True

        playback_keywords = ["playback", "play", "vid", "stream", "decrypt", "kvs"]
        playback_affected = any(kw in msg_full for kw in playback_keywords)
        
        # Check if the code changes themselves mention playback related things
        if not playback_affected:
            diff = self._run_git(["show", "--format=", sha]).stdout.lower()
            playback_affected = any(kw in diff for kw in playback_keywords)

        is_bs4_only = False
        if sites_affected:
            is_bs4_only = all(site in self.bs4_sites for site in sites_affected)

        return {
            "files": files,
            "sites": list(sites_affected),
            "is_bs4_only": is_bs4_only,
            "changelog_affected": changelog_affected,
            "playback_affected": playback_affected,
        }

    def preview_commit(self, sha):
        print(f"\n--- PREVIEW: {sha} ---")
        result = self._run_git(["show", "--stat", sha])
        print(result.stdout)
        print("--------------------------\n")

    def update_sync_file(self, sha, msg, fork_sha=None, skip_reason=None):
        if self.dry_run:
            print(f"[DRY RUN] Would update {SYNC_FILE} for {sha}")
            return

        if not SYNC_FILE.exists():
            print(f"Error: {SYNC_FILE} not found. Cannot update tracking.")
            return

        content = SYNC_FILE.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")

        if skip_reason:
            # Add to "Intentionally Skipped" section
            entry = f"| `{sha}` | {msg} | {skip_reason} |\n"
            # Find the table header for skipped commits
            pattern = r"(### Intentionally Skipped.*?\n\|.*?\n\|.*?\n)"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = content[: match.end()] + entry + content[match.end() :]
            else:
                content += (
                    f"\n### Intentionally Skipped\n\n| Upstream Hash | Message | Reason |\n|---|---|---|\n"
                    + entry
                )
        else:
            # Add to "Integrated" section
            entry = f"| `{sha}` | {msg} | `{fork_sha}` | {today} | Cherry-picked with -x |\n"

            section_header = f"### {today} Cherry-Pick Session"
            if section_header not in content:
                # Insert new section after "## Already Integrated Commits"
                insertion_point = content.find("## Already Integrated Commits")
                if insertion_point != -1:
                    insertion_point = content.find("\n", insertion_point) + 1
                    new_section = f"\n{section_header}\n\n| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |\n|---------------|---------|-----------|-----------------|-------|\n"
                    content = (
                        content[:insertion_point]
                        + new_section
                        + content[insertion_point:]
                    )

            section_idx = content.find(section_header)
            table_end = content.find("\n\n", section_idx)
            if table_end == -1:
                table_end = len(content)

            content = content[:table_end].rstrip() + "\n" + entry + content[table_end:]

        SYNC_FILE.write_text(content, encoding="utf-8")

    def run(self):
        self.ensure_upstream()
        new_commits = self.get_new_commits()

        pending = []
        for c in new_commits:
            sha = c["sha"]
            # Check tracking file (handle varying SHA lengths)
            if any(sha.startswith(h) or h.startswith(sha) for h in self.tracked_hashes):
                continue
            # Check git history
            if any(
                sha.startswith(h) or h.startswith(sha) for h in self.integrated_in_git
            ):
                continue
            pending.append(c)

        if not pending:
            print("✅ Fork is up to date!")
            return

        print(f"📊 Found {len(pending)} new commits to analyze.")

        to_integrate = []
        to_skip = []

        for c in pending:
            analysis = self.analyze_commit(c["sha"])
            if analysis["is_bs4_only"]:
                print(
                    f"⏭️  Auto-skipping {c['sha']} (BS4 site: {', '.join(analysis['sites'])})"
                )
                to_skip.append(c)
            else:
                msg_extra = ""
                if analysis["changelog_affected"]:
                    msg_extra = " [CHANGELOG]"
                print(f"🆕 NEW: {c['sha']} - {c['msg']}{msg_extra}")
                if analysis["sites"]:
                    print(f"   Affected sites: {', '.join(analysis['sites'])}")
                to_integrate.append(c)

        if to_skip:
            confirm = input(f"Auto-skip {len(to_skip)} BS4-related commits? (y/n): ")
            if confirm.lower() == "y":
                for c in to_skip:
                    self.update_sync_file(
                        c["sha"],
                        c["msg"],
                        skip_reason="Fork has BeautifulSoup migration",
                    )
                print(f"✅ Updated {SYNC_FILE} with skipped commits.")

        if not to_integrate:
            print("No new commits require integration.")
            return

        print(f"\nRemaining commits to integrate ({len(to_integrate)}):")
        for i, c in enumerate(to_integrate):
            print(f"{i + 1}. {c['sha']} - {c['msg']}")

        action = input(
            "\nSelect action: [number] to cherry-pick, 'all' to cherry-pick all, 'q' to quit: "
        )

        if action.lower() == "q":
            return

        targets = []
        if action.lower() == "all":
            targets = to_integrate
        elif action.isdigit() and 1 <= int(action) <= len(to_integrate):
            targets = [to_integrate[int(action) - 1]]

        for c in targets:
            sha = c["sha"]
            analysis = self.analyze_commit(sha)
            
            if self.dry_run:
                print(f"[DRY RUN] Would cherry-pick {sha}")
                continue

            print(f"🍒 Cherry-picking {sha}...")
            
            # If changelog is affected and we want to skip it, use a cleaner approach
            if analysis["changelog_affected"] and self.skip_changelog:
                print(f"   Note: This commit contains changelog changes. Attempting to exclude them...")
                # Cherry-pick without committing
                self._run_git(["cherry-pick", "-n", "-x", sha])
                
                # Revert any changelog files
                for f in analysis["files"]:
                    if "changelog.txt" in f:
                        self._run_git(["checkout", "HEAD", "--", f])
                
                # Try to commit
                result = self._run_git(["commit", "-m", f"cherry picked from commit {sha} (excluded changelog)"])
                if result.returncode != 0:
                    # If commit failed (maybe only changelog was changed?), check if anything is staged
                    status = self._run_git(["status", "--porcelain"])
                    if not status.stdout.strip():
                        print(f"⚠️  Skipping {sha} because it only contained changelog changes after filtering.")
                        # Still track it as integrated to avoid re-prompting
                        self.update_sync_file(sha, c["msg"], fork_sha="skipped-changelog-only")
                        continue
                    else:
                        print(f"❌ Failed to commit after excluding changelog for {sha}")
                        print(result.stderr)
                        break
            else:
                # Normal cherry-pick
                result = self._run_git(["cherry-pick", "-x", sha])
                if result.returncode != 0:
                    print(f"❌ Conflict while cherry-picking {sha}!")
                    print(result.stderr)
                    print("\nPlease resolve manually, commit, then update UPSTREAM_SYNC.md.")
                    break

            fork_sha = self._run_git(["log", "-1", "--format=%h"]).stdout.strip()
            self.update_sync_file(sha, c["msg"], fork_sha=fork_sha)
            print(f"✅ Successfully integrated {sha} as {fork_sha}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync Manager for Dobbelina Repository Fork")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--no-skip-changelog", action="store_true", help="Don't skip changelog files during cherry-picking")
    
    args = parser.parse_args()
    
    manager = SyncManager(dry_run=args.dry_run, skip_changelog=not args.no_skip_changelog)
    manager.run()
