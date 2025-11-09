# Cumination BeautifulSoup Migration Roadmap

**Project Goal**: Migrate all 137 sites from regex-based HTML parsing to BeautifulSoup4 for improved reliability and maintainability.

**Started**: 2025-11-01
**Current Version**: v1.1.181
**Progress**: 24/137 sites (17.5%) migrated

---

## Why BeautifulSoup?

**Current Problems with Regex Parsing**:
- Sites break 8-10 times per year when HTML structure changes
- Complex regex patterns are hard to read and maintain
- Whitespace/attribute order changes break parsers
- One parsing failure crashes entire video list

**Benefits of BeautifulSoup**:
- Resilient to HTML formatting changes
- Graceful degradation (one video failure doesn't crash all)
- More readable and maintainable code
- CSS selectors easier than complex regex
- Estimated 70% reduction in site breakage

**Performance**: BeautifulSoup is slightly slower but negligible for typical use (20-30 videos per page).

---

## Migration Status

### ✅ Phase 0: Infrastructure (COMPLETED)

- [x] Add BeautifulSoup4 dependency to addon.xml
- [x] Create helper functions in utils.py
  - [x] `parse_html(html)` - Parse HTML into BeautifulSoup object
  - [x] `safe_get_attr(element, attr, fallback_attrs, default)` - Safe attribute extraction
  - [x] `safe_get_text(element, default, strip)` - Safe text extraction
  - [x] `soup_videos_list(site, soup, selectors, ...)` - Shared BeautifulSoup video listing helper
- [x] Test infrastructure with pilot site

### 🚀 Phase 1: High Priority Sites (8/10 completed - 80%)

These are the highest-traffic mainstream sites that break most often.

| Priority | Site | Status | Notes |
|----------|------|--------|-------|
| 1 | **pornhub** | ✅ **COMPLETED** | Migrated in v1.1.165 |
| 2 | **xvideos** | ✅ **COMPLETED** | BeautifulSoup listing & pagination |
| 3 | **xnxx** | ✅ **COMPLETED** | BeautifulSoup listing overhaul |
| 4 | **spankbang** | ✅ **COMPLETED** | BeautifulSoup migration with modern markup |
| 5 | **xhamster** | ✅ **COMPLETED** | BeautifulSoup migration for categories, channels, pornstars & celebrities |
| 6 | **txxx** | ℹ️ API-based | JSON API already used for listings; no BeautifulSoup migration required |
| 7 | **beeg** | ℹ️ API-based | JSON API already used for listings; no BeautifulSoup migration required |
| 8 | **eporner** | ✅ **COMPLETED** | BeautifulSoup migration for listings/categories |
| 9 | **hqporner** | ✅ **COMPLETED** | BeautifulSoup migration for listings/categories |
| 10 | **porntrex** | ✅ **COMPLETED** | BeautifulSoup migration for listings/pagination |

**Status**: 8/10 BeautifulSoup migrations complete; remaining work limited to monitoring API-based providers.

> ℹ️ **Note**: `txxx` and `beeg` already rely on JSON APIs without regex parsing. They are monitored for regressions but are not counted toward the BeautifulSoup conversion totals.

---

### 🎯 Phase 2: Medium Priority Sites (12/20 completed - 60%)

Secondary mainstream sites with good traffic.

| Site | Status | Category | Notes |
|------|--------|----------|-------|
| drtuber | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration |
| tnaflix | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration |
| pornhat | ✅ **COMPLETED** | Mainstream | BeautifulSoup + 7 related sites |
| pornone | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration |
| anybunny | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration |
| sxyprn | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration |
| pornkai | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration with resilient pagination |
| whoreshub | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration for List, Categories, Playlist, ListPL |
| yespornplease | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration for List, Categories with error handling |
| porngo | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration for listings, categories, pagination, and playback |
| watchporn | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration for listings, categories & pagination |
| justporn | ✅ **COMPLETED** | Mainstream | BeautifulSoup migration for listings & categories |
| netflixporno | ⏳ Pending | Mainstream | |
| peekvids | ⏳ Pending | Mainstream | |
| playvids | ⏳ Pending | Mainstream | |
| porndig | ⏳ Pending | Mainstream | |
| pornhoarder | ⏳ Pending | Aggregator | |
| pornmz | ⏳ Pending | Mainstream | |
| longvideos | ⏳ Pending | Long content | |
| luxuretv | ⏳ Pending | Mainstream | |

**Target**: Complete by end of Phase 2

---

### 📺 Phase 3: Live Cam Sites (1/8 completed)

**Note**: These sites had SQL injection fixes in v1.1.165. May need additional attention.

| Site | Status | Platform | Notes |
|------|--------|----------|-------|
| chaturbate | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |
| bongacams | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |
| stripchat | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |
| camsoda | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |
| cam4 | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |
| streamate | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |
| naked | ✅ **COMPLETED** | Live Cams | BeautifulSoup migration for inline JSON payload |
| amateurtv | ⏳ Pending | Live Cams | SQL fixed in v1.1.165 |

**Target**: Complete by end of Phase 3

---

### 🎌 Phase 4: JAV Sites (0/20 completed)

Japanese adult video sites.

| Site | Status | Notes |
|------|--------|-------|
| missav | ⏳ Pending | Popular JAV site |
| javgg | ⏳ Pending | |
| javguru | ⏳ Pending | |
| javbangers | ⏳ Pending | |
| javhdporn | ⏳ Pending | |
| javmoe | ⏳ Pending | |
| kissjav | ⏳ Pending | |
| supjav | ⏳ Pending | |
| hpjav | ⏳ Pending | |
| netflav | ⏳ Pending | |
| avple | ⏳ Pending | |
| iflix | ⏳ Pending | |
| japteenx | ⏳ Pending | |
| terebon | ⏳ Pending | |
| 85po | ⏳ Pending | Chinese site |
| aagmaal | ⏳ Pending | Indian content |
| aagmaalpro | ⏳ Pending | Indian content |
| awmnet | ⏳ Pending | Asian content |
| foxnxx | ⏳ Pending | |
| sextb | ⏳ Pending | |

**Target**: Complete by end of Phase 4

---

### 🎨 Phase 5: Hentai/Anime Sites (0/10 completed)

Animated adult content.

| Site | Status | Notes |
|------|--------|-------|
| hanime | ⏳ Pending | Popular hentai site |
| hentaidude | ⏳ Pending | |
| hentaihavenco | ⏳ Pending | |
| hentai-moon | ⏳ Pending | |
| hentaistream | ⏳ Pending | |
| heroero | ⏳ Pending | |
| animeidhentai | ⏳ Pending | |
| erogarga | ⏳ Pending | |
| rule34video | ⏳ Pending | |
| taboofantazy | ⏳ Pending | |

**Target**: Complete by end of Phase 5

---

### 🌐 Phase 6: International Sites (0/15 completed)

Region-specific or non-English sites.

| Site | Status | Region | Notes |
|------|--------|--------|-------|
| mrsexe | ⏳ Pending | French | |
| porno1hu | ⏳ Pending | Hungarian | |
| porno365 | ⏳ Pending | Russian | |
| nltubes | ⏳ Pending | Dutch | |
| vaginanl | ⏳ Pending | Dutch | |
| perverzija | ⏳ Pending | Balkan | |
| viralvideosporno | ⏳ Pending | Spanish | |
| netfapx | ⏳ Pending | International | |
| porntn | ⏳ Pending | International | |
| yrprno | ⏳ Pending | International | |
| watchmdh | ⏳ Pending | German | |
| americass | ⏳ Pending | International | |
| trannyteca | ⏳ Pending | Trans content | |
| tubxporn | ⏳ Pending | International | |
| xxdbx | ⏳ Pending | International | |

**Target**: Complete by end of Phase 6

---

### 📹 Phase 7: Niche & Specialty Sites (3/30 completed - 10%)

Specialized content sites.

| Site | Status | Category | Notes |
|------|--------|----------|-------|
| theyarehuge | ⏳ Pending | BBW | |
| bubbaporn | ⏳ Pending | BBW | |
| vintagetube | ⏳ Pending | Vintage | |
| tabootube | ⏳ Pending | Taboo | |
| celebsroulette | ⏳ Pending | Celebrity | |
| reallifecam | ✅ **COMPLETED** | Voyeur | BeautifulSoup migration committed in 80964d1 (2025-11-03) |
| noodlemagazine | ⏳ Pending | Amateur | |
| erome | ⏳ Pending | Amateur | |
| thothub | ⏳ Pending | OnlyFans leaks | Login flow refit today; ready for credential testing/polish next session |
| camwhoresbay | ✅ **COMPLETED** | Cam recordings | BeautifulSoup migration committed in 80964d1 (2025-11-03) |
| myfreecams | ⏳ Pending | Cam archives | |
| cambro | ✅ **COMPLETED** | Cam recordings | BeautifulSoup migration committed in 80964d1 (2025-11-03) |
| eroticmv | ⏳ Pending | Premium | |
| hobbyporn | ⏳ Pending | Amateur | |
| homemoviestube | ⏳ Pending | Amateur | |
| freeuseporn | ⏳ Pending | Niche | |
| familypornhd | ⏳ Pending | Niche | |
| cumlouder | ⏳ Pending | Spanish porn | |
| absoluporn | ⏳ Pending | French | |
| beemtube | ⏳ Pending | Various | |
| blendporn | ⏳ Pending | Various | |
| naughtyblog | ⏳ Pending | Blog/Amateur | |
| nonktube | ⏳ Pending | Asian | |
| paradisehill | ⏳ Pending | Vintage | |
| premiumporn | ⏳ Pending | Premium | |
| seaporn | ⏳ Pending | Asian | |
| speedporn | ⏳ Pending | Various | |
| trendyporn | ⏳ Pending | Various | |
| uflash | ⏳ Pending | Flashing | |
| whereismyporn | ⏳ Pending | Aggregator | |

**Target**: Complete by end of Phase 7

---

### 🔧 Phase 8: Remaining Sites (0/44 completed)

All other sites not in previous phases.

| Site | Status | Notes |
|------|--------|-------|
| 6xtube | ⏳ Pending | |
| hdporn | ⏳ Pending | |
| hdporn92 | ⏳ Pending | |
| hitprn | ⏳ Pending | |
| eroticage | ⏳ Pending | |
| freeomovie | ⏳ Pending | |
| freshporno | ⏳ Pending | |
| fullporner | ⏳ Pending | |
| fullxcinema | ⏳ Pending | |
| hqporner | ⏳ Pending | |
| justfullporn | ⏳ Pending | |
| netflixporno | ⏳ Pending | |
| porn4k | ⏳ Pending | |
| porndish | ⏳ Pending | |
| pornez | ⏳ Pending | |
| pornhits | ⏳ Pending | |
| pornroom | ⏳ Pending | |
| pornxp | ⏳ Pending | |
| vipporns | ⏳ Pending | |
| watcherotic | ⏳ Pending | |
| xfreehd | ⏳ Pending | |
| xmoviesforyou | ⏳ Pending | |
| xozilla | ⏳ Pending | |
| xsharings | ⏳ Pending | |
| xtheatre | ⏳ Pending | |
| youcrazyx | ⏳ Pending | |

**Target**: Complete by end of Phase 8

---

## Migration Guidelines

### Code Pattern to Follow

See `plugin.video.cumination/resources/lib/sites/pornhub.py` for the reference implementation.

**BEFORE (Regex)**:
```python
match = re.compile(r'<div class="item">.*?href="([^"]+)".*?title="([^"]+)"', re.DOTALL).findall(html)
for url, title in match:
    site.add_download_link(title, url, 'Playvid', img, desc)
```

**AFTER (BeautifulSoup)**:
```python
soup = utils.parse_html(html)
items = soup.select('.item, [class*="item"]')

for item in items:
    link = item.select_one('a')
    url = utils.safe_get_attr(link, 'href')
    title = utils.safe_get_attr(link, 'title')
    img_tag = item.select_one('img')
    img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-lazy'])

    site.add_download_link(title, url, 'Playvid', img, desc)
```

### Helper Functions Available

**From `utils.py`** (lines 84-170):

1. **`parse_html(html)`** - Parse HTML into BeautifulSoup object
   ```python
   soup = utils.parse_html(listhtml)
   ```

2. **`safe_get_attr(element, attr, fallback_attrs=None, default='')`** - Get attribute with fallbacks
   ```python
   img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-lazy'], '')
   ```

3. **`safe_get_text(element, default='', strip=True)`** - Get text content safely
   ```python
   duration = utils.safe_get_text(duration_tag, '00:00')
   ```

### Testing Checklist

For each migrated site:

1. **Video Listing**: Main page loads with thumbnails, titles, durations
2. **Pagination**: Next/Previous page buttons work
3. **Categories**: Category browsing works
4. **Search**: Search returns results
5. **Video Playback**: Videos play correctly
6. **Error Handling**: Missing elements don't crash the parser

### Commit Message Format

```
feat: migrate [sitename] to BeautifulSoup

- Replace regex parsing with BeautifulSoup in List() function
- Replace regex parsing in Categories() function (if applicable)
- Add graceful error handling per video item
- Tested: listing, pagination, categories, search, playback

Part of BeautifulSoup migration roadmap (site X/137)
```

---

## Progress Tracking

### Overall Progress

- **Total Sites**: 137
- **Completed**: 24 (17.5%)
- **In Progress**: 0
- **Remaining**: 113 (82.5%)

### Phase Progress

| Phase | Sites | Completed | Percentage |
|-------|-------|-----------|------------|
| Phase 0: Infrastructure | 3 items | 3 | 100% ✅ |
| Phase 1: High Priority | 10 | 8 | 80% 🚧 |
| Phase 2: Medium Priority | 20 | 12 | 60% 🚀 |
| Phase 3: Live Cams | 8 | 1 | 12.5% |
| Phase 4: JAV Sites | 20 | 0 | 0% |
| Phase 5: Hentai/Anime | 10 | 0 | 0% |
| Phase 6: International | 15 | 0 | 0% |
| Phase 7: Niche/Specialty | 30 | 3 | 10% 🚀 |
| Phase 8: Remaining | 44 | 0 | 0% |

### Velocity Tracking

| Date | Sites Completed | Cumulative | Notes |
|------|----------------|------------|-------|
| 2025-11-01 | 11 (drtuber, eporner, hqporner, pornhat, pornhub, pornone, porntrex, spankbang, tnaflix, xnxx, xvideos) | 11/137 | Commit `a21064e`: bulk BeautifulSoup rollout for mainstream providers |
| 2025-11-03 | 1 (anybunny) | 12/137 | Commit `159e0a4`: migrated Anybunny to BeautifulSoup |
| 2025-11-03 | 1 (sxyprn) | 13/137 | Commit `5947ce6`: migrated Sxyprn to BeautifulSoup |
| 2025-11-03 | 3 (cambro, camwhoresbay, reallifecam) | 16/137 | Commit `80964d1`: migrated cam niche providers to BeautifulSoup |
| 2025-11-04 | 1 (pornkai) | 17/137 | Commit `652652b`: migrated PornKai to BeautifulSoup with tests |
| 2025-11-05 | 1 (xhamster) | 18/137 | Local dev: migrated xHamster categories/channels/pornstars/celebrities to BeautifulSoup |
| 2025-11-07 | 1 (whoreshub) | 19/137 | Migrated WhoresHub to BeautifulSoup for List, Categories, Playlist, ListPL |
| 2025-11-07 | 1 (yespornplease) | 20/137 | Migrated YesPornPlease to BeautifulSoup for List, Categories with error handling |
| 2025-11-08 | Maintenance (whoreshub pagination, xvideos titles) | 20/137 | Kodi regression fixes; queued **porngo** migration next |

**Estimated Timeline** (at 1 site/week, focusing on remaining backlog):
- Phase 1 (3 remaining sites): ~3 weeks
- Phase 2 (11 remaining sites): ~11 weeks
- Full migration (117 remaining sites): ~117 weeks (≈2.2 years)

**Optimistic Timeline** (at 3 sites/week):
- Phase 1 (3 remaining sites): ~1 week
- Phase 2 (11 remaining sites): ~4 weeks
- Full migration (117 remaining sites): ~39 weeks (≈9 months)

---

## Site Status Legend

- ✅ **COMPLETED** - Migrated to BeautifulSoup, tested, and merged
- 🚧 **IN PROGRESS** - Currently being migrated
- ⏳ **PENDING** - Not started yet
- ⚠️ **BLOCKED** - Waiting on dependency or issue resolution
- 🔴 **BROKEN** - Site is broken/offline, skip for now
- 🏷️ **DEPRECATED** - Site removed from addon

---

## Notes

- **Prioritization**: Focus on high-traffic mainstream sites first for maximum user impact
- **Testing**: Each site requires manual testing in Kodi environment
- **Breaking Changes**: Some sites may need URL or parameter adjustments during migration
- **Documentation**: Update CHANGES_vX.X.X.md for each release with migrated sites
- **Performance**: BeautifulSoup adds minimal overhead (<100ms per page)
- **Dependencies**: Requires `script.module.beautifulsoup4` (added in v1.1.165)

---

## Quick Reference

**Files to modify per site migration**:
1. `plugin.video.cumination/resources/lib/sites/[sitename].py` - Main site file
2. `ROADMAP.md` - Update status (this file)
3. `CHANGES_vX.X.X.md` - Document changes in version notes

**Commands**:
```bash
# Build and test
python3 build_repo_addons.py --addons plugin.video.cumination

# Verify BeautifulSoup in specific site
grep -n "utils.parse_html" plugin.video.cumination/resources/lib/sites/[sitename].py

# Count migrated sites
grep -c "✅ \*\*COMPLETED\*\*" ROADMAP.md
```

---

**Last Updated**: 2025-11-08 (justporn migration)
**Next Review**: After each Phase 2 site completion
