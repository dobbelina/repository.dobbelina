import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Visiting anybunny.org...")
        try:
            await page.goto("https://anybunny.org/", timeout=60000)
            print(f"Current URL: {page.url}")
            
            # Take a screenshot to see what's going on
            await page.screenshot(path="anybunny_home.png")
            
            # Find all links
            links = await page.eval_on_selector_all("a", "elements => elements.map(e => ({text: e.innerText, href: e.href}))")
            print("\nFound links:")
            for link in links:
                if any(x in link['text'].lower() or x in link['href'].lower() for x in ['new', 'top', 'popular', 'video']):
                    print(f"  Text: {link['text']}, Href: {link['href']}")
            
            # Check a few specific potential URLs
            for path in ['new/', 'top/', 'videos/']:
                url = f"https://anybunny.org/{path}"
                print(f"\nChecking {url}...")
                response = await page.goto(url, timeout=30000)
                print(f"Status: {response.status}, Final URL: {page.url}")
                if response.status == 200:
                    await page.screenshot(path=f"anybunny_{path.replace('/', '')}.png")
                    # Peek at the items
                    items = await page.eval_on_selector_all("a[href*='/videos/'], a[href*='/view/']", "elements => elements.length")
                    print(f"Found {items} potential video links")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
