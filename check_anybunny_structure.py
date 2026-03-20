import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Visiting home page...")
        await page.goto("https://anybunny.org/", timeout=60000)
        
        # Check for categories on home page
        cat_links = await page.eval_on_selector_all("a[href*='/top/']", "elements => elements.map(e => ({text: e.innerText, href: e.href}))")
        print(f"\nFound {len(cat_links)} links containing '/top/':")
        for link in cat_links[:15]:
            text = link['text'].strip()
            if text:
                print(f"  {text} -> {link['href']}")

        # Check for videos on home page
        video_links = await page.eval_on_selector_all("a[href*='/too/'], a[href*='/view/'], a[href*='/videos/']", "elements => elements.map(e => ({text: e.innerText, href: e.href}))")
        print(f"\nFound {len(video_links)} video links on home page:")
        for link in video_links[:5]:
            text = link['text'].strip()
            print(f"  {text} -> {link['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
