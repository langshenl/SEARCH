import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path('/tmp/cnki_www_home_search_precise.html')
QUERY = '科技相关'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://www.cnki.net', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        box = page.locator('textarea#txt_SearchText')
        btn = page.locator('div.search-btn')

        await box.click()
        await box.fill(QUERY)
        await page.wait_for_timeout(1000)
        await btn.click()
        print('SEARCH_STATUS=CLICKED_SEARCH')
        await page.wait_for_timeout(8000)

        html = await page.content()
        OUT.write_text(html, encoding='utf-8')
        print(f'OUT={OUT}')
        print(f'TITLE={await page.title()}')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
