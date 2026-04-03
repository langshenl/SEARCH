import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://www.cnki.net', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        js = r'''
        (() => {
          function visible(el) {
            if (!el) return false;
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
          }
          const inputs = Array.from(document.querySelectorAll('input')).map((el, i) => ({
            idx: i,
            visible: visible(el),
            type: el.type || '',
            placeholder: el.placeholder || '',
            value: el.value || '',
            name: el.name || '',
            id: el.id || '',
            cls: el.className || '',
            outer: el.outerHTML.slice(0, 300)
          })).filter(x => x.visible);

          const searchZone = Array.from(document.querySelectorAll('.search-box, .search-btn, .search, #search, .search-wrap, .search-input')).map((el, i) => ({
            idx: i,
            visible: visible(el),
            tag: el.tagName,
            text: (el.innerText || el.textContent || '').trim().slice(0, 120),
            id: el.id || '',
            cls: el.className || '',
            outer: el.outerHTML.slice(0, 300)
          }));
          return {inputs, searchZone};
        })()
        '''
        data = await page.evaluate(js)
        print(data)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
