import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path('/tmp/cnki_result_probe_after_scroll.html')
QUERY = '科技相关'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://www.cnki.net', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)
        await page.locator('textarea#txt_SearchText').click()
        await page.locator('textarea#txt_SearchText').fill(QUERY)
        await page.wait_for_timeout(500)
        await page.locator('div.search-btn').click()
        await page.wait_for_timeout(10000)
        await page.mouse.wheel(0, 2000)
        await page.wait_for_timeout(3000)
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        OUT.write_text(html, encoding='utf-8')

        js = r'''
        (() => {
          function visible(el) {
            if (!el) return false;
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
          }
          const links = Array.from(document.querySelectorAll('a')).map((el, i) => ({
            idx: i,
            visible: visible(el),
            text: (el.innerText || el.textContent || '').trim().replace(/\s+/g,' ').slice(0,120),
            href: el.href || '',
            cls: el.className || '',
            id: el.id || ''
          })).filter(x => x.visible && x.text).slice(0, 200);

          const blocks = Array.from(document.querySelectorAll('li, div, p, span')).map((el, i) => ({
            idx: i,
            tag: el.tagName,
            visible: visible(el),
            text: (el.innerText || el.textContent || '').trim().replace(/\s+/g,' ').slice(0,180),
            cls: el.className || '',
            id: el.id || ''
          })).filter(x => x.visible && x.text && (/作者|来源|DOI|摘要|关键词|科技相关|人工智能|研究|大学|期刊/.test(x.text))).slice(0, 200);
          return {links, blocks};
        })()
        '''
        data = await page.evaluate(js)
        print('TITLE=', await page.title())
        print('OUT=', OUT)
        print(data)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
