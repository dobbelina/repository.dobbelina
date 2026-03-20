import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Visiting https://anybunny.org/new/ with Playwright...")
        response = await page.goto("https://anybunny.org/new/", timeout=60000)
        print(f"Playwright Status: {response.status}")
        
        cookies = await context.cookies()
        print("\nPlaywright Cookies:")
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value']}")
            
        print("\nPlaywright Response Headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
