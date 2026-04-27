import asyncio
from pathlib import Path

from scrapling.fetchers import AsyncStealthySession

OUT = Path('/tmp/cnki_www_home_search_test.html')
URL = 'https://www.cnki.net'
QUERY = '科技相关'

JS = r'''
(() => {
  function visible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }
  const inputs = Array.from(document.querySelectorAll('input')).filter(visible);
  let input = null;
  for (const el of inputs) {
    const p = (el.placeholder || '') + ' ' + (el.name || '') + ' ' + (el.id || '') + ' ' + (el.className || '');
    if (/检索|搜索|主题|关键词|query|word|txt/i.test(p)) { input = el; break; }
  }
  if (!input && inputs.length) input = inputs[0];
  if (!input) return 'INPUT_NOT_FOUND';

  input.focus();
  input.value = '科技相关';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));

  const candidates = Array.from(document.querySelectorAll('button, a, input[type="submit"]')).filter(visible);
  let btn = null;
  for (const el of candidates) {
    const t = (el.innerText || el.textContent || '') + ' ' + (el.className || '') + ' ' + (el.id || '');
    if (/搜索|检索|search/i.test(t)) { btn = el; break; }
  }
  if (btn) {
    btn.click();
    return 'CLICKED_SEARCH_BUTTON';
  }

  const form = input.closest('form');
  if (form) {
    form.submit();
    return 'SUBMITTED_FORM';
  }

  input.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', code:'Enter', bubbles:true}));
  input.dispatchEvent(new KeyboardEvent('keypress', {key:'Enter', code:'Enter', bubbles:true}));
  input.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter', code:'Enter', bubbles:true}));
  return 'ENTER_SEARCH';
})();
'''

async def main():
    async with AsyncStealthySession(headless=False, max_pages=1) as session:
        page = await session.fetch(URL, google_search=False)
        status = await page.evaluate(JS)
        html = await page.html_content()
        OUT.write_text(html, encoding='utf-8')
        print('SEARCH_STATUS=', status)
        print('OUT=', OUT)

if __name__ == '__main__':
    asyncio.run(main())
