# Upstream Sync Tracking

**Purpose**: Track which commits from upstream (dobbelina/repository.dobbelina) have been integrated into this fork.

**Last Updated**: 2026-02-12
**Last Sync**: 2026-02-12 - Cherry-picked commit af3c079 (porntn liting, fixes #1731)

---

## How to Use This File

1. **Before cherry-picking**: Check this file to see if a commit is already integrated
2. **After cherry-picking**: Add the new entry to the appropriate section below
3. **Format for new entries**:
   ```
   | `upstream-hash` | Commit message | `fork-hash` | YYYY-MM-DD | Notes |
   ```

---

## Already Integrated Commits

These upstream commits have been integrated into the fork:

### 2026-01-04 Cherry-Pick Session

| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |
|---------------|---------|-----------|-----------------|-------|
| `7bbe1c7` | Fix video playback for FlareSolverr scraped sites (e.g. luxuretv) | `d079d3f` | 2026-01-04 | Cherry-picked with -x |
| `43c6322` | americass - removed fixes #1709 | `1dd541c` | 2026-01-04 | Cherry-picked with -x |

### 2026-01-17 Cherry-Pick Session

| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |
|---------------|---------|-----------|-----------------|-------|
| `1270357` | new site fixes #1735 | `0fa653b` | 2026-01-17 | Cherry-picked with -x |

### 2026-02-05 Cherry-Pick Session

| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |
|---------------|---------|-----------|-----------------|-------|
| `8b2cd89` | sxyprn - fix search fixes #1277 | `25c2afb` | 2026-02-05 | Cherry-picked with -x |
| `63348e8` | chaturbate favorites - fixes #1745 | `6137f6f` | 2026-02-05 | Cherry-picked with -x |
| `9ac3255` | allclassic - fixes #1742 | `8e5b74a` | 2026-02-05 | Cherry-picked with -x |
| `a4e50af` | kissjav - fix thumbnails, playback fixes #1743 | `732cab5` | 2026-02-05 | Cherry-picked with -x |
| `99dd004` | fix pagination | `c4c3c72` | 2026-02-05 | Cherry-picked with -x |
| `beb5b9d` | luxuretv - fix nextpage, thumbnails | `95f32d6` | 2026-02-05 | Cherry-picked with -x |

### 2026-02-12 Cherry-Pick Session

| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |
|---------------|---------|-----------|-----------------|-------|
| `af3c079` | porntn liting, fixes #1731 | `3ccc67f` | 2026-02-12 | Cherry-picked with manual conflict resolution (preserved BS4 parsers) |

### 2026-03-03 Cherry-Pick Session

| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |
|---------------|---------|-----------|-----------------|-------|
| `ebf141f` | speedporn - fixes #1770 | `manual` | 2026-03-03 | Manual integration in BS4 scraper |
| `ef8811d` | xmoviesforyou - fix page numbers, goto page | `manual` | 2026-03-03 | Manual integration in BS4 scraper (updated pagination spec) |
| `3a8df5f` | heroero - fix playback | `manual` | 2026-03-03 | Manual integration in BS4 scraper (added iframe/videoFormats parsing) |
| `e90da9b` | hqporner - fix thumbnails fixes #1769 | `already-in` | 2026-03-03 | Fork already has Referer fix for hqporner |
| `73a6488` | sxyprn - fix playback (direct links) fixes #1763 | `already-in` | 2026-03-03 | Fork already has updated getvsrc logic |

### Previously Integrated (Manual)

| Upstream Hash | Message | Fork Hash | Date Integrated | Notes |
|---------------|---------|-----------|-----------------|-------|
| `673fe9b` | fix module load error on TvOS #1724 | `07aafdc` | 2025-12-28 | Manual integration |
| `8eae561` | fullxcinema | `ef3a914` | 2025-12-28 | Manual integration |
| `3a98f37` | Python 2 fixes #1722 fixes #1663 | `f9e4c51` | 2025-12-28 | Manual integration |
| `c11caeb` | pornhoarder fixes #1713 | `b4a998e` | 2025-12-28 | Manual integration |
| `31644dc` | pornhub fixes #1712 | `1888b76` | 2025-12-28 | Manual integration |
| `53a9dfe` | whoreshub fixes #1715 | `ab66f4f` | 2025-12-28 | Manual integration |
| `0509d5b` | premiumporn - fixes #1714 | `8ee8f7f` | 2025-12-28 | Manual integration |
| `51c39fb` | porntn fixes #1720 | `5e1458b` | 2025-12-28 | Manual integration |
| `afe1ff0` | celebsroulette, awmnet | `dfbc225` | 2025-12-28 | Manual integration |
| `b4daafc` | fixes (cumlouder, justporn, porndig, porno1hu) | `unknown` | 2025-11-30 | Manual integration |
| `90d2f5a` | pornxp - domain change - fixes #1711 | `unknown` | ~2025-11 | Fork already has pornxp.com-mirror.com |
| `122e955` | freepornvideos - new site | `unknown` | 2025-11-30 | Added in v1.1.197 |
| `67bd60f` | tokyomotion - new site fixes #1689 | `unknown` | ~2025-11 | Site exists in fork |
| `f4c5a43` | iflix - removed | `unknown` | ~2025-11 | Already removed from fork |
| `b5ae7b6` | bubba, cambro, yespornplease removed | `unknown` | 2025-11-30 | All removed in v1.1.197 |
| `71d1398` | vintagetube - removed | `unknown` | ~2025-11 | Already removed from fork |

### Intentionally Skipped (BeautifulSoup Migration Conflicts)

The following upstream commits are regex-based fixes for sites that have been migrated to BeautifulSoup4 in the fork. Since BeautifulSoup parsing is more robust, these fixes are unnecessary:

| Upstream Hash | Message | Reason |
|---------------|---------|--------|
| `68e4ef97` | pornkai - fixes #1760 | Fork has BeautifulSoup migration |
| `f3d48c1b` | xhmster playback | Fork has BeautifulSoup migration |
| `1721e034` | terebon - fix playback | Fork has BeautifulSoup migration |
| `d47192d5` | camsoda #1685 | Fork has BeautifulSoup migration |
| `86d995a6` | hanime fixes #1686 | Fork has BeautifulSoup migration |
| `60b6859a` | hanime playback - fixes #1688 | Fork has BeautifulSoup migration |
| `9722f3eb` | camwhoresbay - fix next page | Fork has BeautifulSoup migration |
| `67bd60fe` | tokyomotion - new site fixes #1689 | Fork has BeautifulSoup migration |
| `a34c0a78` | terebon - fix listing | Fork has BeautifulSoup migration |
| `e40d58df` | camcaps site name change | Fork has BeautifulSoup migration |
| `122e9555` | freepornvideos - new site | Fork has BeautifulSoup migration |
| `d522cedb` | awmnet - fix listing | Fork has BeautifulSoup migration |
| `b4beb803` | camwhoresbay - fix playback | Fork has BeautifulSoup migration |
| `b4daafcf` | fixes | Fork has BeautifulSoup migration |
| `e96ed9b6` | stripchat - fix playback (SD only) fixes #1710 | Fork has BeautifulSoup migration |
| `90d2f5af` | pornxp - domain change - fixes #1711 | Fork has BeautifulSoup migration |
| `afe1ff04` | celebsroulette, awmnet | Fork has BeautifulSoup migration |
| `51c39fb2` | porntn fixes #1720 | Fork has BeautifulSoup migration |
| `0509d5b0` | premiumporn - fixes #1714 | Fork has BeautifulSoup migration |
| `d92bd04d` | tnaflix fixes #1718 | Fork has BeautifulSoup migration |
| `53a9dfe3` | whoreshub fixes #1715 | Fork has BeautifulSoup migration |
| `31644dcc` | pornhub fixes #1712 | Fork has BeautifulSoup migration |
| `c11caeb6` | pornhoarder fixes #1713 | Fork has BeautifulSoup migration |
| `3a98f37d` | Python 2 fixes #1722 fixes #1663 | Fork has BeautifulSoup migration |
| `8eae561a` | fullxcinema | Fork has BeautifulSoup migration |
| `673fe9b8` | fix module load error on TvOS #1724 | Fork has BeautifulSoup migration |
| `004f106f` | luxuretv - fix nextpage, fixes #1734 | Fork has BeautifulSoup migration |
| `b075cbdf` | luxuretv - fix nextpage | Fork has BeautifulSoup migration |
| `0d683b26` | freshporno - fix domain fixes #1748 | Fork has BeautifulSoup migration |
| `8ff6fe1f` | allclassic, watchporn playback, fixes #1751 | Fork has BeautifulSoup migration |
| `6f3103ab` | javguru - fix playback, thumbnails - fixes #1749 | Fork has BeautifulSoup migration |
| `3e995d97` | hentaidude - fix listing - fixes #1750 | Fork has BeautifulSoup migration |
| `2ad68a13` | simpvids - name chaged to camcaps - fixes #1757 | Fork has BeautifulSoup migration |
| `0d683b2` | freshporno - fix domain fixes #1748 | Fork has BeautifulSoup migration |
| `8ff6fe1` | allclassic, watchporn playback, fixes #1751 | Fork has BeautifulSoup migration |
| `6f3103a` | javguru - fix playback, thumbnails - fixes #1749 | Fork has BeautifulSoup migration |
| `3e995d9` | hentaidude - fix listing - fixes #1750 | Fork has BeautifulSoup migration |
| `004f106` | luxuretv - fix nextpage, fixes #1734 | Fork has BeautifulSoup migration |
| `b075cbd` | luxuretv - fix nextpage | Fork has BeautifulSoup migration |
| `d92bd04` | tnaflix fixes #1718 | Fork has BeautifulSoup migration |
| `e96ed9b` | stripchat - fix playback (SD only) fixes #1710 | Fork has BeautifulSoup migration |
| `b4beb80` | camwhoresbay - fix playback | Fork has BeautifulSoup migration |
| `9722f3e` | camwhoresbay - fix next page | Fork has BeautifulSoup migration |
| `60b6859` | hanime playback - fixes #1688 | Fork has BeautifulSoup migration |
| `86d995a` | hanime fixes #1686 | Fork has BeautifulSoup migration |
| `d47192d` | camsoda #1685 | Fork has BeautifulSoup migration |
| `f3d48c1` | xhmster playback | Fork has BeautifulSoup migration |
| `d522ced` | awmnet - fix listing | Fork has BeautifulSoup migration |
| `a34c0a7` | terebon - fix listing | Fork has BeautifulSoup migration |
| `1721e03` | terebon - fix playback | Fork has BeautifulSoup migration |
| `e40d58d` | camcaps site name change | Fork has BeautifulSoup migration |

**Note**: Our fork has migrated 114/143 sites (79.7%) to BeautifulSoup4, providing 70% reduction in site breakage and better resilience to HTML changes. Many upstream regex-based fixes address issues that don't occur with BeautifulSoup parsing.

### Not Applicable (Files Don't Exist in Fork)

The following upstream commits attempt to modify or remove files that don't exist in this fork:

| Upstream Hash | Message | Reason |
|---------------|---------|--------|
| `e8ebd05` | #1739 (Remove easynews.py) | File doesn't exist in fork - already removed or never added |

---

## Pending Upstream Commits

**Status as of 2026-01-04**: All applicable upstream commits have been reviewed.

- **2 commits successfully integrated** (FlareSolverr fix, americass removal)
- **16 commits confirmed already integrated** (sites/features already in fork)
- **15 commits intentionally skipped** (BeautifulSoup migrations make them unnecessary)

See `CHERRY_PICK_ANALYSIS.md` for initial analysis from 2026-01-04.

---

## Integration Commands

When cherry-picking from upstream, use the `-x` flag to automatically track the source:

```bash
# Cherry-pick with tracking
git cherry-pick -x <upstream-commit-hash>

# This adds a line to the commit message:
# (cherry picked from commit <upstream-commit-hash>)
```

After cherry-picking, update this file:

```bash
# Get the new commit hash in your fork
git log -1 --oneline

# Add entry to this file under 'Already Integrated Commits':
# | `<upstream-hash>` | Commit message | `<fork-hash>` | YYYY-MM-DD | Cherry-picked with -x |
```

---

## Checking Sync Status

To see what new commits are in upstream:

```bash
# Fetch latest from upstream
git fetch upstream

# View commits in upstream not in fork (excluding version bumps)
git log upstream/master --not origin/master --oneline --no-merges | grep -v 'Bumped to v.'

# View detailed changes
git log upstream/master --not origin/master --stat

# Check if a specific upstream commit is in fork
git log --all --grep='cherry picked from commit <hash>'
```

---

## Future Integration Strategy

**Recommended workflow:**

Use the automated Sync Manager:
```bash
python scripts/sync_manager.py
```

This script will:
1. Fetch latest from upstream
2. Identify new commits
3. Auto-skip fixes for sites already migrated to BeautifulSoup4
4. Prompt for cherry-picking remaining commits
5. Automatically update this file (`UPSTREAM_SYNC.md`)

**Manual workflow (if needed):**

1. **Weekly/Monthly sync check**:
   ```bash
   git fetch upstream
   git log upstream/master --not origin/master --oneline --no-merges | grep -v 'Bumped to v.' > /tmp/new_commits.txt
   ```

2. **Review new commits**:
   - Read commit messages and changes
   - Categorize by priority (critical/high/medium/low)
   - Check for conflicts with fork-specific changes

3. **Cherry-pick with tracking**:
   ```bash
   git cherry-pick -x <hash>  # Automatically adds source reference
   ```

4. **Update this file**:
   - Add entry to 'Already Integrated Commits' table
   - Include any notes about conflicts or modifications

5. **Test**:
   ```bash
   python run_tests.py
   python run_tests.py --coverage
   ```

---

## Notes

- **Manual integrations**: Some commits were manually applied before this tracking system existed
- **Modified integrations**: If a commit was cherry-picked but modified, note it in the 'Notes' column
- **Skipped commits**: If you intentionally skip an upstream commit, document why
- **Version bumps**: Generally skip upstream version bumps and manage versions independently
