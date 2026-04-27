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
            name: el.name || '',
            id: el.id || '',
            cls: el.className || ''
          }));
          const buttons = Array.from(document.querySelectorAll('button, a, input[type="submit"]')).map((el, i) => ({
            idx: i,
            visible: visible(el),
            text: (el.innerText || el.textContent || '').trim().slice(0, 80),
            id: el.id || '',
            cls: el.className || ''
          })).filter(x => x.visible || /搜索|检索|高级检索|主题/.test(x.text));
          const searchTexts = Array.from(document.querySelectorAll('body *')).map((el, i) => ({
            idx: i,
            tag: el.tagName,
            text: (el.innerText || el.textContent || '').trim().slice(0, 80),
            cls: el.className || '',
            id: el.id || '',
            visible: visible(el)
          })).filter(x => x.text && /搜索|检索|高级检索|主题|学术搜索/.test(x.text)).slice(0, 60);
          return {inputs, buttons: buttons.slice(0, 80), searchTexts};
        })()
        '''
        data = await page.evaluate(js)
        print(data)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
