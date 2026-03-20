import urllib.request
import urllib.error

url = "https://anybunny.org/new/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://anybunny.org/"
}

print(f"Fetching {url}...")
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"Status: {response.status}")
        print(f"Headers: {response.info()}")
        data = response.read()
        print(f"Data length: {len(data)}")
        # print(data[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print(f"Response headers: {e.info()}")
except Exception as e:
    print(f"Error: {e}")
