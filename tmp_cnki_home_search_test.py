import asyncio
from pathlib import Path

from scrapling.fetchers import AsyncStealthySession

QUERY = "科技相关"
OUT = Path('/tmp/cnki_home_search_test.html')

JS = r'''
(async () => {
  function findInput() {
    const selectors = [
      'input[type="search"]',
      'input[placeholder*="检索"]',
      'input[placeholder*="搜索"]',
      'input[placeholder*="主题"]',
      'input[class*="search"]',
      'input'
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) return el;
    }
    return null;
  }
  const input = findInput();
  if (!input) return 'INPUT_NOT_FOUND';
  input.focus();
  input.value = '科技相关';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  const btn = document.querySelector('button[type="submit"], button[class*="search"], .search-btn, .btn-search, button');
  if (btn) {
    btn.click();
    return 'CLICKED_SEARCH';
  }
  const form = input.closest('form');
  if (form) {
    form.submit();
    return 'SUBMITTED_FORM';
  }
  input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', bubbles: true}));
  input.dispatchEvent(new KeyboardEvent('keypress', {key: 'Enter', code: 'Enter', bubbles: true}));
  input.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', bubbles: true}));
  return 'ENTER_SEARCH';
})();
'''

async def main():
    async with AsyncStealthySession(headless=False, max_pages=1) as session:
        page = await session.fetch('https://kns.cnki.net/', google_search=False)
        await page.wait(4000)
        status = await page.evaluate(JS)
        await page.wait(8000)
        html = await page.content()
        OUT.write_text(html, encoding='utf-8')
        print('SEARCH_STATUS=', status)
        print('OUT=', OUT)
        print('TITLE=', await page.title())

if __name__ == '__main__':
    asyncio.run(main())
