# Fluffle FMFY Tracker

Last reviewed: 2026-03-22
Primary source: https://fluffle.cc/fmfy
Secondary sources:

- https://onepornlist.com/
- https://pornbox.org/

## Purpose

Track sites listed on Fluffle/FMFY and other discovery indexes that:

- are already supported by Cumination
- exist in the repo but are disabled/excluded
- are not yet supported and should be ranked by likely implementation difficulty

This file is meant to be updated during periodic Fluffle checks instead of re-doing the comparison from scratch each time.

## Current Snapshot

This review covered the visible Fluffle sections:

- Streaming
- Adult Movies / Grindhouse
- Asian / JAV
- Hentai Anime

Secondary-source review notes:

- `OnePornList` is broad and category-rich, so it is useful for expanding the long-term candidate queue.
- `PornBox` is a simpler “sites with videos” source, so it is better for quick gap checks against the core tube-site roster.

## Discovery Source Guidance

### Fluffle / FMFY

Best use:

- broad, curated discovery across multiple content categories
- good source for periodic addon gap reviews
- especially useful for Streaming, JAV, and Hentai buckets

### OnePornList

Best use:

- category-driven discovery when we want to intentionally expand into a segment
- useful for finding new candidate tubes, aggregators, adult-movie sites, and niche categories

Weaknesses:

- very large list surface, so it can create a lot of low-value/duplicate candidates
- needs heavier manual triage than Fluffle

Recommendation:

- treat as a monthly or occasional expansion source, not a daily check source

### PornBox

Best use:

- fast sanity check for missing mainstream tube domains
- useful when we want to compare our current “sites with videos” coverage against a large flat list

Weaknesses:

- less structured than Fluffle or OnePornList
- lower signal for niche categories like JAV or hentai
- includes a lot of clone-tier/low-value tube domains

Recommendation:

- use as a supplemental tube-gap source after Fluffle, not as the primary roadmap source

## Already Supported

These Fluffle-listed sites already map to active site modules in the addon.

### Streaming / Tube

- `hqporner`
- `sxyprn` / SexyPorn
- `watchporn`
- `pornhoarder`
- `noodlemagazine`
- `eporner`
- `xhamster`
- `xvideos`
- `playhdporn`
- `spankbang`
- `neporn`
- `freepornvideos`
- `pornhub`
- `tnaflix`
- `youporn`
- `porntrex`
- `josporn`
- `someporn`
- `xozilla`
- `okxxx`
- `youjizz`
- `jizzbunker`
- `heavyr`
- `xnxx`
- `thepornarea`
- `drtuber`
- `tube8`
- `xmegadrive`
- `porndish`
- `porndig`
- `ask4porn`
- `pornhd3x`
- `beeg`
- `redtube`
- `superporn`
- `txxx`
- `motherless`

### Adult Movies / Grindhouse

- `eroticmv`
- `erogarga`
- `eroticage`
- `paradisehill`
- `xtheatre` / `pornxtheatre`
- `speedporn`

### Asian / JAV

- `sextb` / SexTB
- `supjav`
- `javseen`
- `javgg`
- `javguru`
- `missav`
- `javhdporn`
- `javbangers`

### Hentai Anime

- `animeidhentai`
- `hentai-moon`
- `hentaistream`
- `hentaihavenco`

## Existing But Special State

These are already in the repo, but need attention when doing Fluffle comparisons.

| Site | Repo State | Notes |
|---|---|---|
| `missav` | Present but excluded from main import | Listed in `resources/lib/sites/__init__.py` excluded set. |
| `pornxpert` | Present but excluded from main import | Also listed in the excluded set. |
| `javseen` | Promoted from testing on 2026-03-22 | Now production-ready. |
| `thepornarea` | Promoted from testing on 2026-03-22 | Now production-ready. |
| `someporn` | Promoted from testing on 2026-03-22 | Now production-ready. |

## Candidate Queue

These Fluffle-listed sites were not found as active site modules during this review.

| Site | Category | Difficulty | Status | Notes |
|---|---|---:|---|---|
| `analdin` | Streaming | Easy | Not started | Repo already has `tests/fixtures/sites/analdin_home.html`, which suggests prior parser work or research exists. |
| `porndoe` | Streaming | Easy | Not started | Repo already has `tests/fixtures/sites/porndoe_home.html`; good first candidate. |
| `pornmd` | Streaming / Search | Easy-Medium | Not started | Search/index style site; useful for breadth but playback expectations may be different. |
| `pornobae` | Streaming | Easy-Medium | Not started | Likely standard tube parser if markup is stable. |
| `topvid` | Streaming | Easy-Medium | Not started | Likely generic tube/KVS style candidate. |
| `hotmovix` | Streaming | Easy-Medium | Not started | Likely straightforward tube parser if playback is direct or KVS-based. |
| `iporntv` | Streaming | Easy-Medium | Not started | Likely normal list/play parser work. |
| `vid123` | Streaming | Easy-Medium | Not started | Worth checking if playback is direct or iframe-based. |
| `mangoporn` | Adult Movies | Easy-Medium | Not started | Adult-movie category with likely static listing pages. |
| `film1k` | Adult Movies | Medium | Not started | Movie-site style support may be easier than JAV mirrors, but playback host quality needs checking. |
| `rarelust` | Adult Movies | Medium | Not started | Likely more download/offsite oriented than direct stream oriented. |
| `cat3film` | Adult Movies | Medium | Not started | Movie indexing likely manageable, playback host quality unknown. |
| `cat3movies` | Adult Movies | Medium | Not started | Similar to `cat3film`; may be mostly list/external-host handoff work. |
| `porninja` | Streaming | Medium | Not started | Needs live markup check; likely parser-first, playback uncertain. |
| `ixxx` | Streaming | Medium | Not started | Big target, but modern markup and anti-bot behavior need checking. |
| `streamporn` / `xtapes` / `watchpornx` | Streaming | Medium | Not started | Alias/grouped candidate; should determine whether one parser can support multiple domains. |
| `shyfap` | Streaming | Medium | Not started | Unknown markup stability; requires live inspection. |
| `5moviesporn` | Streaming | Medium | Not started | Needs live validation; likely video-index style site. |
| `pornken` | Streaming | Medium | Not started | Unknown parser difficulty; likely standard list/play flow. |
| `onlinepornhub` | Streaming | Medium | Not started | Name suggests aggregator/cloner; verify legality/stability and playback usefulness first. |
| `xgomovies` | Streaming | Medium | Not started | Movie-style tube candidate; likely more host-resolution heavy. |
| `pornekip` | Streaming | Medium | Not started | Unknown markup quality and host pattern. |
| `adultload` | Adult Movies | Medium | Not started | External-host heavy possibility; needs live evaluation. |
| `wipfilms` | Adult Movies | Medium | Not started | Likely catalog + host handoff; maybe valuable if markup is stable. |
| `javtiful` | JAV | Medium-Hard | Not started | Mirror-heavy JAV site; likely more fragile playback chain than list parsing. |
| `njav` | JAV | Medium-Hard | Not started | Alias/domain churn likely. |
| `highporn` | JAV | Medium-Hard | Not started | Needs live evaluation for mirrors and anti-bot behavior. |
| `senzuri.tube` | JAV | Medium-Hard | Not started | Likely manageable lists, but mirror playback complexity unknown. |
| `javfan` | JAV | Medium-Hard | Not started | Worth checking after first-tier JAV adds are exhausted. |
| `javdoe` | JAV | Hard | Not started | Mirror/host chain likely fragile. |
| `playav` | JAV | Hard | Not started | Historically the sort of site that tends to require brittle playback extraction. |
| `dnaav` | JAV | Hard | Not started | Likely high churn. |
| `javmost` | JAV | Hard | Not started | Needs live inspection and mirror quality evaluation. |
| `avjoy` | JAV | Hard | Not started | Likely anti-bot and mirror-host heavy. |
| `javenglish` | JAV | Hard | Not started | Likely worthwhile, but playback chain may be fragile. |
| `7mmtv` | JAV | Hard | Not started | Unknown stability; likely more time than first-wave candidates. |
| `topdrama` | JAV | Hard | Not started | Needs manual value check before implementation. |
| `jav-angel` | JAV | Hard | Not started | Host chain likely brittle. |
| `koreanpornmovie` | JAV / Korean | Hard | Not started | May be valuable, but likely movie-host rather than direct-stream style. |
| `cosplay.jav` | Niche JAV | Hard | Not started | Niche target; lower priority unless specifically requested. |
| `ixxx` | Streaming | Medium | Not started | Appears on both Fluffle and PornBox, which raises priority as a mainstream gap. |
| `anysex` | Streaming | Medium | Not started | Appears on both Fluffle and PornBox; worth a live inspection pass. |
| `porndoe` | Streaming | Easy | Not started | Appears on PornBox too; still a strong early add candidate. |

## Low Priority / Manual Review Needed

These need a manual product-value check before engineering time:

- `cums`
- `10hitmovies`
- `suj`
- `intporn`
- `siska`
- `anysex`
- `kojka`
- `sex-empire`
- `ifuqyou`
- `film-adult`
- `sex-film`
- `pinkueiga`
- `91porna`
- `91rb`
- `asiangirl`
- `rou.video`
- `watchfreejav`

Reasons they are in this bucket:

- unclear long-term value
- possible clone/low-quality domains
- likely higher churn than reward
- may overlap heavily with already-supported sites

## Secondary Source Notes

### OnePornList

Observed value:

- broad discovery surface across search engines, aggregators, picture sites, adult-movie sites, JAV, hentai, and niche segments
- useful for spotting future candidates after the obvious Fluffle gaps are exhausted

Immediate actionable adds surfaced there that still fit Cumination well:

- `analdin`
- `porndoe`
- `pornmd`
- `pornobae`
- `mangoporn`
- `film1k`

Lower-confidence entries from OnePornList should stay out of the main queue until manually inspected.

### PornBox

Observed value:

- good for cross-checking mainstream video tubes
- confirms some obvious unsupported domains still worth reviewing

Useful gaps surfaced there:

- `ixxx`
- `anysex`
- `porndoe`
- `cliphunter`
- `fuq`
- `4tube`

Of those, the most practical near-term Cumination candidates are:

- `porndoe`
- `ixxx`
- `anysex`

The rest likely need more manual value checking before implementation.

## Recommended Next Adds

If adding from Fluffle systematically, start here:

1. `analdin`
2. `porndoe`
3. `pornmd`
4. `pornobae`
5. `topvid`
6. `hotmovix`
7. `film1k`
8. `mangoporn`

That sequence gives a good mix of:

- likely easier parser work
- decent user-facing value
- lower expected playback-host complexity than the harder JAV candidates

## Update Process

When re-checking Fluffle:

1. Review the same Fluffle sections.
2. Mark any sites that moved from candidate to implemented.
3. Mark any supported sites that are now excluded, broken, or removed.
4. Add newly discovered Fluffle entries into `Candidate Queue`.
5. Re-rank only when live inspection changes the difficulty estimate.

## Change Log

### 2026-03-22

- Created initial Fluffle/FMFW tracker.
- Compared current visible Fluffle list against active site modules.
- Marked `javseen`, `thepornarea`, and `someporn` as production-ready and no longer testing-only.
- Recorded existing exclusions for `missav` and `pornxpert`.
- Added `OnePornList` and `PornBox` as secondary discovery sources.
- Documented when to use each source and folded their strongest candidate signals into the queue.
