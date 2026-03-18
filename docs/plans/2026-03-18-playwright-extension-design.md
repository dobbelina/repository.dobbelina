# Spec: Playwright Testing & Debugging Extension

**Status**: Draft
**Date**: 2026-03-18
**Topic**: Playwright-based automated browser testing and debugging for Cumination Kodi addon.

---

## 1. Overview
The **Playwright Diagnostics Extension** (provisionally `playwright-diagnostics`) is a Gemini CLI extension designed to automate the verification, debugging, and snapshotting of adult video sites supported by the Cumination Kodi addon. It bridges the gap between the Gemini CLI's conversational agent and the project's existing Python-based Playwright infrastructure.

### 1.1 Goals
- **Automate Live Verification**: Run smoke tests for any site to detect breakage or Cloudflare blocks.
- **Deep Sniffing**: Automatically find playable video stream URLs (.m3u8, .mp4) by simulating user interaction.
- **HTML Snapshotting**: Capture fresh HTML fixtures for BeautifulSoup4 parser development and regression testing.
- **Agent Integration**: Provide a specialized "Expert" skill to help the Gemini agent diagnose complex site changes.

---

## 2. Architecture & Components

The extension will be a hybrid of **Slash Commands** (for quick actions) and an **Agent Skill** (for deep analysis).

### 2.1 Directory Structure
The extension will reside in `.gemini/extensions/playwright-diagnostics/`:
```text
.gemini/extensions/playwright-diagnostics/
├── gemini-extension.json      # Extension manifest & command mapping
├── package.json               # Node.js dependencies (bridge logic)
├── lib/
│   ├── bridge.js              # Node-to-Python execution logic
│   └── formatters.js          # Result presentation logic
└── skills/
    └── playwright-expert/
        └── SKILL.md           # Instructions for deep agent-led debugging
```

### 2.2 Integration Bridge
The extension will not rewrite existing logic but will call existing project scripts:
- `scripts/playwright_smoke_runner.py`
- `plugin.video.cumination/resources/lib/playwright_helper.py`

Environment Requirement: `CUMINATION_ALLOW_PLAYWRIGHT=1` must be set during execution.

---

## 3. Slash Commands

| Command | Argument | Description | Underlying Script |
| :--- | :--- | :--- | :--- |
| `/pw-smoke` | `[site]` | Run a deep smoke test for a specific site. | `scripts/playwright_smoke_runner.py --site {site}` |
| `/pw-sniff` | `[url]` | Sniff the network for the first playable video URL. | `plugin.video.cumination/resources/lib/playwright_helper.py` |
| `/pw-snap` | `[site]` | Capture and save a fresh HTML snapshot as a fixture. | `scripts/codegen.py` or a new snapshot utility |
| `/pw-debug` | `[url]` | Open a site and return a summary of network/DOM state. | `plugin.video.cumination/resources/lib/playwright_helper.py` |
| `/pw-test-env` | (none) | Verify that Playwright and Python bridge are operational. | (New internal script) |

---

## 4. The Playwright Expert Skill (`SKILL.md`)

This skill will be activated when the user asks for manual debugging or when a `/pw-` command returns a complex failure.

### 4.1 Core Instructions
- **Analysis**: If a site is blocked by Cloudflare, guide the agent to try the Playwright fallback.
- **Selector Mapping**: If BeautifulSoup4 parsing fails, use Playwright to find the correct CSS selectors in the live DOM.
- **Network Tracing**: Analyze captured network logs to find hidden stream URLs that regular scrapers miss.
- **Visual Validation**: (Optional) Use screenshot tools to confirm that images and interactive elements are visible.

---

## 5. Implementation Roadmap

1.  **Phase 1: Environment & Bridge**: Create the `gemini-extension.json` and basic Node.js bridge to call `playwright_smoke_runner.py`.
2.  **Phase 2: Core Commands**: Implement `/pw-smoke` and `/pw-sniff`.
3.  **Phase 3: Snapshot & Debug**: Implement `/pw-snap` and `/pw-debug`.
4.  **Phase 4: Agent Skill**: Write and register the `playwright-expert` skill.
5.  **Phase 5: Validation**: Add the `/pw-test-env` command and verify across a sample of 5 sites.

---

## 6. Security & Performance
- **Isolation**: Playwright instances will be closed immediately after use to prevent memory leaks.
- **Headless Default**: All commands will run headless unless a `--headful` flag is explicitly provided.
- **Secrets**: No cookies or sensitive user data will be logged or persisted by the extension.
