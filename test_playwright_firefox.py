import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            await page.goto("http://example.com")
            print(f"Title: {await page.title()}")
            await browser.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
