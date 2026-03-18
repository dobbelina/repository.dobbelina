---
name: playwright-expert
description: "Specialized guidance for analyzing Playwright diagnostics, mapping DOM to BeautifulSoup, and handling anti-bot measures."
---

# Playwright Expert: Site Diagnostics & Scraping Bridge

This skill provides expert guidance for bridging the gap between live browser-based diagnostics (Playwright) and static Python-based scraping (BeautifulSoup). It is designed to help you analyze site failures, bypass anti-bot measures, and ensure reliable content extraction for the Cumination plugin.

<HARD-GATE>
Before proposing any changes to a site's Python scraping logic (`plugin.video.cumination/resources/lib/sites/`), you MUST first run a diagnostic trace using the `/pw-smoke` or `/pw-sniff` command to confirm the current live state of the target URL.
</HARD-GATE>

## Checklist for Site Diagnostics

1. **Run Smoke Test** - Use `/pw-smoke <site>` to verify overall site health.
2. **Analyze Network Traces** - Look for failed requests (403, 404, 503) or specific blocked patterns.
3. **Capture DOM State** - Use Playwright to dump the fully rendered HTML after all JS has executed.
4. **Map to BeautifulSoup** - Compare the Playwright-rendered DOM with the static HTML seen by `requests` to identify dynamic elements.
5. **Verify Assets** - Check that image URLs and video streams are accessible and return valid content-types.

## 1. Network Trace Analysis

When a site fails, the network log is your first source of truth:
- **Identify Blocking:** Look for `status: 403` or `status: 503` on initial page loads, often indicating Cloudflare or other WAFs.
- **Find the Media:** Look for `XHR/Fetch` requests or `video/mp4`, `application/x-mpegURL` (HLS) content types to find the real stream URL.
- **Check Referer/Origin:** Note if certain assets require specific headers that the Python `resolveurl` logic might be missing.
- **Console Errors:** Check for JavaScript errors that might prevent the page from rendering the expected elements.

## 2. Mapping DOM to BeautifulSoup

Python-based scrapers often fail because they expect elements to be present in the initial HTML, while modern sites load them via JS:
- **Inspect Live Elements:** Identify the CSS selectors (classes, IDs, data attributes) of the elements you need in the Playwright browser.
- **Check for iFrames:** If an element is missing from the main DOM, check if it's inside an iframe (common for video players).
- **Find the Pattern:** Identify a stable selector that BeautifulSoup can use on the static HTML if possible. If the element is purely JS-driven, you must find the underlying API call or the JSON blob embedded in a `<script>` tag.
- **BeautifulSoup Strategy:** Prefer `soup.find()` or `soup.select_one()` with unique class names or data attributes over fragile index-based selection (e.g., `div[2]/span[1]`).

## 3. Handling Cloudflare & Anti-Bot

Cloudflare "Under Attack" mode and Turnstile are common obstacles:
- **Detection:** Look for `<title>Just a moment...</title>` or the presence of `cf-challenge` classes.
- **Waiting Strategy:** Use `page.wait_for_selector('.main-content', { state: 'visible' })` to wait for the challenge to resolve automatically via Playwright's default behavior.
- **User-Agent Alignment:** Ensure the `User-Agent` used in Playwright matches what the Python scraper will eventually use. Discrepancies often trigger secondary challenges.
- **Cookie Extraction:** If Playwright solves the challenge, you may need to extract the `cf_clearance` cookie to pass back to the Python `requests` session.

## 4. Verification of Images and Playback

A "found" URL is not necessarily a "working" URL:
- **Image Health:** Verify that thumbnail URLs return `200 OK` and have an `image/*` content-type. Check dimensions if possible (e.g., no 1x1 tracking pixels).
- **Stream Integrity:** For HLS (`.m3u8`), ensure the manifest contains at least one variant playlist. For MP4, verify the `Content-Length` is greater than a few kilobytes.
- **Playback Simulation:** Use `/pw-sniff <url>` to see if the video actually starts loading in a real browser environment.

## Key Principles

- **Trust but Verify:** Never assume the HTML in your IDE matches what the site delivers to a browser today.
- **Be Surgical:** Only use Playwright when static scraping is impossible. Use it to *discover* the pattern, then implement the pattern in Python for performance.
- **Respect Constraints:** Remember that Kodi's Python environment is limited. Avoid complex dependencies that won't run in `script.module.resolveurl`.
- **Fail Gracefully:** If a site is fundamentally broken (e.g., taken down), report it as "Site Down" rather than "Parser Error".
