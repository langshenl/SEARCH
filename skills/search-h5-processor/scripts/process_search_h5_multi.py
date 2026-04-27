#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import urllib.request
from html import unescape
from pathlib import Path

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36'
)
TIMEOUT = 15


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def resolve_final_url(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.geturl()
    except Exception:
        return url


def extract_baidu_results(html: str):
    results = []
    link_pat = re.compile(r'<a[^>]+href="(https?://www\.baidu\.com/link\?url=[^"]+)"[^>]*>([\s\S]*?)</a>', re.I)
    snippet_window = 1500
    for m in link_pat.finditer(html):
        raw_url = unescape(m.group(1)).strip()
        title = strip_html(m.group(2))
        if not title:
            continue
        start = m.end()
        snippet_raw = html[start:start + snippet_window]
        summary = strip_html(snippet_raw)[:300]
        final_url = resolve_final_url(raw_url)
        results.append({
            'title': title,
            'summary': summary,
            'raw_url': raw_url,
            'final_url': final_url,
        })
    return results


def write_excel(rows, path: Path):
    if Workbook is None:
        raise RuntimeError('openpyxl not installed')
    wb = Workbook()
    ws = wb.active
    ws.title = '搜索结果'
    ws.append(['标题', '简介', '原始百度链接', '原文链接'])
    for row in rows:
        ws.append([row['title'], row['summary'], row['raw_url'], row['final_url']])
    wb.save(path)


def write_md(rows, path: Path):
    lines = ['# 原文链接列表', '']
    for i, row in enumerate(rows, 1):
        title = row['title'] or f'结果{i}'
        url = row['final_url'] or row['raw_url']
        lines.append(f'{i}. [{title}]({url})')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def list_input_files(folder: Path, prefix: str | None):
    files = list(folder.glob('*.html')) + list(folder.glob('*.md'))
    if prefix:
        files = [p for p in files if p.name.startswith(prefix)]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def main():
    in_dir = Path.home() / 'Desktop' / 'h5'
    out_dir = Path.home() / 'Desktop' / '处理文件夹'
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = sys.argv[1] if len(sys.argv) > 1 else None
    html_files = list_input_files(in_dir, prefix)
    if not html_files:
        print('ERROR: 未找到可处理的多页 h5 文件', file=sys.stderr)
        sys.exit(1)

    merged = []
    blocked = 0
    source_names = []
    for html_file in html_files:
        source_names.append(html_file.name)
        html = html_file.read_text(encoding='utf-8', errors='ignore')
        if '百度安全验证' in html:
            blocked += 1
            continue
        merged.extend(extract_baidu_results(html))

    dedup = []
    seen = set()
    for r in merged:
        key = (r['title'], r['final_url'] or r['raw_url'])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)

    excel_path = out_dir / '搜索结果.xlsx'
    md_path = out_dir / '原文链接.md'
    if excel_path.exists():
        excel_path.unlink()
    if md_path.exists():
        md_path.unlink()

    write_excel(dedup, excel_path)
    write_md(dedup, md_path)

    print('INPUT_FILES:')
    for name in source_names:
        print(name)
    print(f'FILE_COUNT: {len(source_names)}')
    print(f'BLOCKED_COUNT: {blocked}')
    print(f'COUNT: {len(dedup)}')
    print(f'EXCEL: {excel_path}')
    print(f'MD: {md_path}')


if __name__ == '__main__':
    main()
