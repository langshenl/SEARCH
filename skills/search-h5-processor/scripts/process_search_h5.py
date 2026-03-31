#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from datetime import datetime
from html import unescape
from pathlib import Path

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def latest_html_file(folder: Path) -> Path | None:
    files = list(folder.glob('*.html')) + list(folder.glob('*.md'))
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def extract_baidu_results(html: str):
    results = []

    # 方案1：抓跳转链接块
    link_pat = re.compile(r'<a[^>]+href="(https?://www\.baidu\.com/link\?url=[^"]+)"[^>]*>([\s\S]*?)</a>', re.I)
    snippet_window = 1500
    for m in link_pat.finditer(html):
        href = unescape(m.group(1)).strip()
        title = strip_html(m.group(2))
        if not title:
            continue
        start = m.end()
        snippet_raw = html[start:start + snippet_window]
        snippet = strip_html(snippet_raw)[:300]
        results.append({
            'title': title,
            'summary': snippet,
            'url': href,
        })

    # 去重
    dedup = []
    seen = set()
    for r in results:
        key = (r['title'], r['url'])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)
    return dedup


def write_excel(rows, path: Path, source_file: str):
    if Workbook is None:
        raise RuntimeError('openpyxl not installed')
    wb = Workbook()
    ws = wb.active
    ws.title = '搜索结果'
    ws.append(['序号', '标题', '简介', '原文链接', '来源页面文件', '提取时间'])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for i, row in enumerate(rows, 1):
        ws.append([i, row['title'], row['summary'], row['url'], source_file, now])
    wb.save(path)


def write_md(rows, path: Path):
    lines = ['# 原文链接列表', '']
    for i, row in enumerate(rows, 1):
        title = row['title'] or f'结果{i}'
        url = row['url']
        lines.append(f'{i}. [{title}]({url})')
    lines.append('')
    path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    in_dir = Path.home() / 'Desktop' / 'h5'
    out_dir = Path.home() / 'Desktop' / '处理文件夹'
    out_dir.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        html_file = Path(sys.argv[1]).expanduser()
    else:
        html_file = latest_html_file(in_dir)

    if not html_file or not html_file.exists():
        print('ERROR: 未找到可处理的 html 文件', file=sys.stderr)
        sys.exit(1)

    html = html_file.read_text(encoding='utf-8', errors='ignore')
    if '百度安全验证' in html:
        print(f'INPUT: {html_file}')
        print('STATUS: BLOCKED_BAIDU_CAPTCHA')
        print('COUNT: 0')
        sys.exit(0)

    rows = extract_baidu_results(html)
    excel_path = out_dir / '搜索结果.xlsx'
    md_path = out_dir / '原文链接.md'

    write_excel(rows, excel_path, html_file.name)
    write_md(rows, md_path)

    print(f'INPUT: {html_file}')
    print(f'COUNT: {len(rows)}')
    print(f'EXCEL: {excel_path}')
    print(f'MD: {md_path}')


if __name__ == '__main__':
    main()
