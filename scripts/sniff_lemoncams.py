import argparse
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

INTERESTING_DOMAINS = (
    "lemoncams.com",
    "api-v2-prod.lemoncams.com",
    "render-v2.lemoncams.com",
    "stripchat.com",
    "media-hls.doppiocdn.",
    "edge-hls.doppiocdn.",
    "saawsedge.com",
    "doppiocdn.com",
    "doppiocdn.net",
)

INTERESTING_TOKENS = (
    ".m3u8",
    ".mp4",
    ".ts",
    ".m4s",
    "manifest",
    "playlist",
    "_hls_msn",
    "_hls_part",
    "api",
    "stream",
    "video/",
)


def is_interesting_url(url):
    lower_url = url.lower()
    if any(token in lower_url for token in INTERESTING_TOKENS):
        return True
    host = urlparse(url).netloc.lower()
    return any(domain in host for domain in INTERESTING_DOMAINS)


def classify_url(url):
    lower_url = url.lower()
    host = urlparse(url).netloc.lower()
    if ".m3u8" in lower_url or "manifest" in lower_url or "playlist" in lower_url:
        return "manifest"
    if any(ext in lower_url for ext in [".mp4", ".m4s", ".ts"]):
        return "media"
    if "api-v2-prod.lemoncams.com" in host:
        return "api"
    if "stripchat.com" in host:
        return "stripchat"
    if "lemoncams.com" in host:
        return "lemoncams"
    return "other"


def register_page(page, seen_requests, seen_responses):
    def handle_request(request):
        url = request.url
        if not is_interesting_url(url):
            return
        key = (request.method, url)
        if key in seen_requests:
            return
        seen_requests.add(key)
        print(
            "REQ [{kind}] {method} {url}".format(
                kind=classify_url(url),
                method=request.method,
                url=url,
            )
        )
        sys.stdout.flush()

    def handle_response(response):
        url = response.url
        if not is_interesting_url(url):
            return
        key = (response.status, url)
        if key in seen_responses:
            return
        seen_responses.add(key)
        print(
            "RES [{kind}] {status} {url}".format(
                kind=classify_url(url),
                status=response.status,
                url=url,
            )
        )
        sys.stdout.flush()

    page.on("request", handle_request)
    page.on("response", handle_response)


def run(start_url):
    print("Starting LemonCams sniffer")
    print("Open the Stripchat-backed LemonCams model page in the browser window.")
    print("Interesting requests and responses will be printed here.")
    print("Press Enter here when you want to close the browser and stop sniffing.")
    sys.stdout.flush()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1440, "height": 960},
            user_agent=BROWSER_USER_AGENT,
        )

        seen_requests = set()
        seen_responses = set()

        def attach_page(page):
            print("PAGE {}".format(page.url or "about:blank"))
            sys.stdout.flush()
            register_page(page, seen_requests, seen_responses)

        context.on("page", attach_page)

        page = context.new_page()
        attach_page(page)
        page.goto(start_url, wait_until="domcontentloaded", timeout=60000)

        try:
            input()
        finally:
            context.close()
            browser.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sniff LemonCams network traffic while you browse manually."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://www.lemoncams.com/",
        help="Starting URL to open in the browser.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.url)
