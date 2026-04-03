import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path('/tmp/cnki_playwright_home_search.html')
QUERY = '科技相关'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://www.cnki.net', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        selectors = [
            'input[placeholder*="检索"]',
            'input[placeholder*="搜索"]',
            'input[placeholder*="关键词"]',
            'input[type="search"]',
            'input'
        ]
        found = None
        for sel in selectors:
            try:
                locator = page.locator(sel).first
                if await locator.count() > 0:
                    found = locator
                    break
            except Exception:
                pass
        if not found:
            print('SEARCH_STATUS=INPUT_NOT_FOUND')
            html = await page.content()
            OUT.write_text(html, encoding='utf-8')
            print(f'OUT={OUT}')
            print(f'TITLE={await page.title()}')
            await browser.close()
            return

        await found.click()
        await found.fill(QUERY)
        await page.wait_for_timeout(1000)

        button_selectors = [
            'button:has-text("搜索")',
            'button:has-text("检索")',
            'input[type="submit"]',
            'button',
            'a:has-text("搜索")'
        ]
        clicked = False
        for sel in button_selectors:
            try:
                locator = page.locator(sel).first
                if await locator.count() > 0:
                    await locator.click()
                    clicked = True
                    break
            except Exception:
                pass
        if not clicked:
            await found.press('Enter')
            print('SEARCH_STATUS=ENTER_SEARCH')
        else:
            print('SEARCH_STATUS=CLICKED_SEARCH')

        await page.wait_for_timeout(8000)
        html = await page.content()
        OUT.write_text(html, encoding='utf-8')
        print(f'OUT={OUT}')
        print(f'TITLE={await page.title()}')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
