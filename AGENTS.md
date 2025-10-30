# Repository Guidelines

## Project Structure & Module Organization
- `plugin.video.cumination/` — main Kodi video add‑on. Python sources in `resources/lib/`, site scrapers in `resources/lib/sites/`, settings in `resources/settings.xml`.
- `plugin.video.uwc/` — legacy/alternate add‑on.
- `script.video.F4mProxy/` — streaming helpers (HLS/TS utilities under `lib/`).
- `repository.dobbelina/` — repository metadata, icons, and zips.
- Root: `addons.xml` and `addons.xml.md5` index all packaged add‑ons; `README.md` overview.

## Build, Test, and Development Commands
- Update version: edit `addon.xml` inside the add‑on you changed and append notes to its `changelog.txt`.
- Package (Windows PowerShell): `Compress-Archive plugin.video.cumination plugin.video.cumination-<ver>.zip` (run from repo root). Place the zip under the add‑on folder or `repository.dobbelina/`.
- Update index: regenerate `addons.xml` and `addons.xml.md5` when publishing the repo site.
- Local run: in Kodi, Add‑ons → Install from zip → select your packaged zip. Dev path (Windows): `%APPDATA%\Kodi\addons\plugin.video.cumination`.

## Coding Style & Naming Conventions
- Python 3, PEP 8, 4‑space indentation, max line length ~100.
- Files/modules: `snake_case.py`; classes: `CamelCase`; functions/vars: `snake_case`.
- Cumination sites live in `resources/lib/sites/*.py` and typically define an `AdultSite` instance plus `@site.register` handlers (e.g., `Main`, `List`, `Playvid`). Prefer `utils` helpers for HTTP, parsing, and UI.

## Testing Guidelines
- Smoke test each flow in Kodi: navigation, search, pagination, and playback.
- Validate with debug logs enabled in Kodi; ensure no tracebacks. If adding a new site, verify at least: listing → details → playback.
- No unit test suite exists; keep logic small and reuse `resources/lib/utils.py` where possible.

## Commit & Pull Request Guidelines
- Commits: imperative mood and scoped, e.g., `cumination: fix pornhub pagination`, `repo: bump addons.xml`.
- PRs: include a concise description, linked issue (if any), steps to reproduce/verify, and screenshots or log excerpts when relevant. Touch only related files.

## Fork & Upstream Sync
- Keep diffs small to ease merging with upstream. Avoid sweeping reformatting.
- Preserve `addon id` unless you intend a rebranded release; if you do, change the ID and repo paths consistently.
- Periodically pull upstream changes and resolve conflicts in site modules first (`resources/lib/sites/`).

## Security & Configuration Tips
- Do not hardcode credentials or tokens. Avoid shipping binaries beyond icons/zips already present.
- Respect site TOS and rate limits; prefer existing request utilities that set headers/cookies safely.
- Kodi compatibility: target Matrix/Nexus (Python 3). Prefer `kodi-six` helpers where needed for cross‑version behavior.
