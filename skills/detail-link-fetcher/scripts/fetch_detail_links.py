#!/usr/bin/env python3
from __future__ import annotations

import re
import time
import urllib.request
from html import unescape
from pathlib import Path

from openpyxl import Workbook

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36'
)
TIMEOUT = 20

FIELDS = [
    '政策ID', '标题', '正文', '摘要', '发文机关', '联合发文机关', '发布时间', '文号',
    '政策层级', '地区', '所属行业', '政策类型', '政策主题', '关键词', '适用对象', '支持方式',
    '申报条件', '申报时间', '有效期', '政策状态', '原始链接', '附件链接', '相似政策', '上位政策/下位政策关系',
    '抓取状态', '正文长度', '是否检测到附件', '是否需要浏览器兜底'
]


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept-Language': 'zh-CN,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or 'utf-8'
        return resp.read().decode(charset, errors='ignore')


def strip_html(text: str) -> str:
    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_meta(html: str, name: str) -> str:
    m = re.search(rf'<meta[^>]+(?:name|property)="{re.escape(name)}"[^>]+content="([^"]*)"', html, flags=re.I)
    return unescape(m.group(1)).strip() if m else ''


def extract_title(html: str) -> str:
    article_title = extract_meta(html, 'ArticleTitle')
    if article_title:
        return article_title
    m = re.search(r'<title>([\s\S]*?)</title>', html, flags=re.I)
    return strip_html(m.group(1)) if m else ''


def extract_body(html: str) -> str:
    patterns = [
        r'<div[^>]+class="[^"]*(?:article-content|article_content|articleCon|wp_articlecontent|TRS_Editor|content|article|zoom)[^"]*"[^>]*>([\s\S]*?)</div>',
        r'<div[^>]+id="[^"]*(?:article|content|zoom|main-content)[^"]*"[^>]*>([\s\S]*?)</div>',
        r'<article[^>]*>([\s\S]*?)</article>',
        r'<div[^>]+class="[^"]*(?:main|detail|pages_content|news_detail|txt_con)[^"]*"[^>]*>([\s\S]*?)</div>',
    ]
    best = ''
    for pat in patterns:
        for m in re.finditer(pat, html, flags=re.I):
            txt = strip_html(m.group(1))
            if len(txt) > len(best):
                best = txt
    return best


def extract_attachments(html: str) -> str:
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.I | re.S)
    hits = []
    for href, text in links:
        t = strip_html(text)
        if re.search(r'附件|下载|PDF|DOC|DOCX|OFD|XLS|XLSX', t, flags=re.I) or re.search(r'\.(pdf|doc|docx|ofd|xls|xlsx|zip)$', href, flags=re.I):
            hits.append(href)
    return '\n'.join(dict.fromkeys(hits))


def derive_policy_id(url: str) -> str:
    m = re.search(r'(t\d+_\d+)', url)
    return m.group(1) if m else ''


def derive_region(url: str, html: str) -> str:
    if 'hubei.gov.cn' in url:
        return '湖北省'
    site_name = extract_meta(html, 'SiteName')
    if '湖北' in site_name:
        return '湖北省'
    return ''


def status_and_fallback(row: dict) -> tuple[str, str, str]:
    body_len = len((row.get('正文') or '').strip())
    has_attachment = '是' if (row.get('附件链接') or '').strip() else '否'
    poor = False
    if not row.get('标题'):
        poor = True
    if body_len < 120:
        poor = True
    if not row.get('发布时间'):
        poor = True
    status = 'GOOD'
    if poor and body_len > 0:
        status = 'PARTIAL'
    if poor and body_len == 0:
        status = 'POOR'
    need_browser = '是' if status in {'PARTIAL', 'POOR'} else '否'
    return status, str(body_len), need_browser if need_browser else '否'


def parse_detail(url: str) -> dict:
    row = {k: '' for k in FIELDS}
    row['原始链接'] = url
    try:
        html = fetch_text(url)
    except Exception:
        row['抓取状态'] = 'FETCH_ERROR'
        row['正文长度'] = '0'
        row['是否检测到附件'] = '否'
        row['是否需要浏览器兜底'] = '是'
        return row

    row['政策ID'] = derive_policy_id(url)
    row['标题'] = extract_title(html)
    row['摘要'] = extract_meta(html, 'Description')
    row['发文机关'] = extract_meta(html, 'ContentSource')
    row['发布时间'] = extract_meta(html, 'PubDate')
    row['关键词'] = extract_meta(html, 'Keywords')
    row['正文'] = extract_body(html)
    row['附件链接'] = extract_attachments(html)
    row['地区'] = derive_region(url, html)
    row['是否检测到附件'] = '是' if row['附件链接'] else '否'

    status, body_len, need_browser = status_and_fallback(row)
    row['抓取状态'] = status
    row['正文长度'] = body_len
    row['是否需要浏览器兜底'] = need_browser
    return row


def read_links(md_path: Path):
    text = md_path.read_text(encoding='utf-8', errors='ignore')
    urls = re.findall(r'\((http[^)]+)\)', text)
    seen = set()
    ordered = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


def write_excel(rows, out_path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = '政策详情'
    ws.append(FIELDS)
    for row in rows:
        ws.append([row.get(f, '') for f in FIELDS])
    wb.save(out_path)


def main():
    link_md = Path.home() / 'Desktop' / '处理文件夹' / '原文链接.md'
    out_dir = Path.home() / 'Desktop' / 'detail-h5'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_excel = out_dir / '政策详情抓取结果.xlsx'

    urls = read_links(link_md)
    rows = []
    for url in urls:
        rows.append(parse_detail(url))
        time.sleep(1)

    if out_excel.exists():
        out_excel.unlink()
    write_excel(rows, out_excel)

    print(f'INPUT_MD={link_md}')
    print(f'COUNT={len(rows)}')
    print(f'EXCEL={out_excel}')


if __name__ == '__main__':
    main()
