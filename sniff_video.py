import re
import json
import sys
import requests
from urllib.parse import urljoin

COMMON_VIDEO_EXTS = ('.m3u8', '.mpd', '.mp4')

def fetch(url, headers=None):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Referer": url,
    }
    if headers:
        default_headers.update(headers)
    r = requests.get(url, headers=default_headers, timeout=15)
    r.raise_for_status()
    return r.text

def find_urls_in_text(text, base_url=None):
    # very loose URL finder
    url_regex = r'https?://[^\s"\'<>]+'
    candidates = re.findall(url_regex, text)
    results = []
    for c in candidates:
        if c.endswith(COMMON_VIDEO_EXTS):
            results.append(c)
    # also catch protocol-relative //cdn... links
    proto_rel = re.findall(r'//[^\s"\'<>]+', text)
    for c in proto_rel:
        full = 'https:' + c
        if full.endswith(COMMON_VIDEO_EXTS):
            results.append(full)
    # de-dup
    return list(dict.fromkeys(results))

def find_embedded_json(text):
    """Try to pull JSON blobs from <script> tags that have {...}"""
    blobs = []
    # very naive: grab big {...} blocks
    for m in re.finditer(r'({.*?})', text, flags=re.DOTALL):
        chunk = m.group(1)
        # keep small-ish ones
        if 20 < len(chunk) < 20000:
            blobs.append(chunk)
    return blobs

def main(page_url):
    html = fetch(page_url)
    found = []

    # 1) direct URLs in HTML
    found.extend(find_urls_in_text(html, base_url=page_url))

    # 2) check <script> JSON-ish blobs
    # (this helps with sites like Stripchat that stick the stream in window.__INITIAL_STATE__)
    for blob in find_embedded_json(html):
        # try to parse json
        try:
            data = json.loads(blob)
        except Exception:
            continue
        # walk the dict looking for strings that look like video urls
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for v in item.values():
                    stack.append(v)
            elif isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, str):
                if item.startswith('//'):
                    item = 'https:' + item
                if item.startswith('http') and item.endswith(COMMON_VIDEO_EXTS):
                    found.append(item)

    # de-dup again
    found = list(dict.fromkeys(found))

    if not found:
        print("No obvious video URLs found.")
        return

    print("Possible video URLs:")
    for u in found:
        print(" -", u)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sniff_video.py <page_url>")
        sys.exit(1)
    main(sys.argv[1])
