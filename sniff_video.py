import re
import json
import sys
import requests

COMMON_VIDEO_EXTS = ('.m3u8', '.mpd', '.mp4')

def fetch(url, headers=None):
    default_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": url,
    }
    if headers:
        default_headers.update(headers)

    # disable proxies for this request
    session = requests.Session()
    session.trust_env = False  # ignore HTTP(S)_PROXY from environment

    resp = session.get(
        url,
        headers=default_headers,
        timeout=15,
        # you can also do: proxies={"http": None, "https": None}
    )
    resp.raise_for_status()
    return resp.text

def find_urls_in_text(text):
    url_regex = r'https?://[^\s"\'<>]+'
    candidates = re.findall(url_regex, text)
    results = []
    for c in candidates:
        if c.endswith(COMMON_VIDEO_EXTS):
            results.append(c)

    # protocol-relative
    proto_rel = re.findall(r'//[^\s"\'<>]+', text)
    for c in proto_rel:
        full = 'https:' + c
        if full.endswith(COMMON_VIDEO_EXTS):
            results.append(full)

    # de-dup
    return list(dict.fromkeys(results))

def find_embedded_json(text):
    blobs = []
    for m in re.finditer(r'({.*?})', text, flags=re.DOTALL):
        chunk = m.group(1)
        if 20 < len(chunk) < 20000:
            blobs.append(chunk)
    return blobs

def main(page_url):
    try:
      html = fetch(page_url)
    except Exception as e:
      print(f"[!] Could not fetch page: {e}")
      print("[!] If you're inside a container or behind a VPN/proxy, try running this without those,")
      print("    or remove HTTP_PROXY / HTTPS_PROXY / ALL_PROXY from your env.")
      return

    found = []

    # 1) direct links
    found.extend(find_urls_in_text(html))

    # 2) JSON blobs
    for blob in find_embedded_json(html):
        try:
            data = json.loads(blob)
        except Exception:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, str):
                if item.startswith('//'):
                    item = 'https:' + item
                if item.startswith('http') and item.endswith(COMMON_VIDEO_EXTS):
                    found.append(item)

    found = list(dict.fromkeys(found))

    if not found:
        print("No obvious video URLs found.")
    else:
        print("Possible video URLs:")
        for u in found:
            print(" -", u)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sniff_video.py <page_url>")
        sys.exit(1)
    main(sys.argv[1])
