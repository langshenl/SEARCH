#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.request
import urllib.error
import warnings
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
except Exception:
    print('missing dependency: openpyxl', file=sys.stderr)
    sys.exit(2)

COLUMNS = ["标题", "正文", "摘要", "发文机关", "发布时间", "原始链接", "关键词", "类型", "地区"]
TYPE_RULES = [
    ('项目申报', ['申报', '申报指南', '申报条件']),
    ('发展规划', ['发展规划', '规划纲要', '规划']),
    ('工作部署', ['工作要点', '工作方案', '通知', '召开', '部署']),
    ('产业扶持', ['扶持', '支持', '奖补', '补贴', '若干措施', '支持措施']),
    ('管理规范', ['管理办法', '办法', '细则', '监管']),
    ('建设实施', ['建设方案', '建设', '实施']),
    ('政策解读', ['解读', '答记者问']),
    ('统计报告', ['统计公报', '工作报告', '报告', '执行情况']),
    ('资金预算', ['预算', '资金', '财政']),
    ('人才引进', ['人才', '引进']),
]
ORG_PATTERNS = [
    r"([^\n，。；]{2,40}(?:人民政府|人民法院|人民检察院|委员会|管理局|监管局|发展和改革委员会|发展改革委|财政厅|财政局|教育厅|教育局|商务厅|商务局|文旅厅|文化和旅游厅|博物馆|办公室))",
]
DATE_PATTERNS = [
    r"(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)",
    r"(20\d{2}年\d{1,2}月\d{1,2}日)",
    r"(20\d{2}-\d{2}-\d{2})",
]

# URL validation: returns True if URL is accessible (not 404/4xx/5xx)
# ─────────────────────────────────────────────
# Plan A: Real-URL content fetcher (BeautifulSoup)
# ─────────────────────────────────────────────

def _extract_text_lines(elem):
    """从元素中提取干净文本行，去导航碎片、相邻重复"""
    lines = []
    prev = ''
    for e in elem.descendants:
        if isinstance(e, str):
            t = e.strip()
            if not t or len(t) <= 6:
                continue
            if any(w in t for w in [
                'copyright', '版权所有', 'cookie', '隐私政策', '网站地图',
                '请您登录', '请登录', '无障碍', '长者专区', 'loading',
                'ajax', 'javascript', 'jquery', '[', '【', '您的位置',
                '上一页', '下一页', '更多', '网站支持',
            ]):
                continue
            if t != prev:
                lines.append(t)
                prev = t
    return lines


def fetch_clean_content(url, title='', summary='', timeout=8):
    """
    从真实 URL 抓取并解析干净正文，三层兜底：
    1. 找 <article> 或含"来源:"的元素
    2. 找包含标题的段落周围正文
    3. 找文本量最大的 div
    失败返回 None
    """
    if not REQUESTS_AVAILABLE:
        return None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        }
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            r = requests.get(url, headers=headers, timeout=timeout)
        r.encoding = r.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # 去掉噪声标签
        for tag in soup.find_all(['script','style','nav','header','footer','aside','noscript','iframe','svg']):
            tag.decompose()

        # ── 第一层：<article> ──
        article = soup.find('article')
        if article:
            lines = _extract_text_lines(article)
            if len(lines) > 3:
                return '\n'.join(lines)

        # ── 第一层：找含"来源:"的元素 ──
        for elem in soup.find_all(string=lambda t: t and '来源' in t):
            parent = elem.find_parent(['div', 'section', 'article', 'td'])
            if not parent:
                continue
            for _ in range(6):
                parent = parent.parent
                if not parent or not parent.name:
                    break
                pclass = ' '.join(parent.get('class', [])).lower()
                pid = (parent.get('id') or '').lower()
                if any(k in pclass + pid for k in ['container', 'content', 'article', 'main', 'body', 'txt', 'text']):
                    lines = _extract_text_lines(parent)
                    if len(lines) > 3:
                        return '\n'.join(lines)
                    break

        # ── 第二层：找包含标题的段落 ──
        if title:
            kw = title[:15].strip()
            if kw:
                for elem in soup.find_all(string=lambda t: t and kw in t):
                    parent = elem.find_parent(['div', 'p', 'section'])
                    if not parent:
                        continue
                    for _ in range(5):
                        parent = parent.parent
                        if parent and parent.name in ['div', 'section']:
                            pclass = ' '.join(parent.get('class', [])).lower()
                            pid = parent.get('id', '').lower()
                            if 'container' in pclass or 'content' in pclass or 'article' in pid:
                                lines = _extract_text_lines(parent)
                                if len(lines) > 3:
                                    return '\n'.join(lines)
                                break

        # ── 第三层：找最大文本块 ──
        best_div, best_len = None, 0
        for div in soup.find_all('div'):
            div_class = ' '.join(div.get('class', [])).lower()
            div_id = (div.get('id') or '').lower()
            if any(k in div_class + div_id for k in ['nav', 'menu', 'sidebar', 'footer', 'header', 'tool', 'share', 'related', 'comment', 'logo', 'banner']):
                continue
            text = div.get_text(strip=True)
            if len(text) > best_len:
                best_len = len(text)
                best_div = div
        if best_div and best_len > 200:
            lines = _extract_text_lines(best_div)
            if len(lines) > 3:
                return '\n'.join(lines)

        return None
    except Exception:
        return None


def is_url_valid(url, timeout=5):
    if not url or not url.startswith(('http://', 'https://')):
        return False
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            return status < 400
    except Exception:
        # Fallback: try GET request
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                return status < 400
        except Exception:
            return False


def first_match(patterns, text):
    for p in patterns:
        m = re.search(p, text or '')
        if m:
            return m.group(1).strip()
    return ''


def infer_type(title, summary, body):
    text = f'{title or ""} {summary or ""} {body or ""}'
    for label, keywords in TYPE_RULES:
        if any(k in text for k in keywords):
            return label
    return '综合管理'


def infer_region(query, provided_region, text):
    if provided_region:
        return provided_region
    provinces = ["湖北", "湖南", "广东", "浙江", "江苏", "北京", "上海", "天津", "重庆", "四川", "河南", "河北", "山东", "山西", "陕西", "安徽", "福建", "江西", "广西", "云南", "贵州", "海南", "辽宁", "吉林", "黑龙江", "内蒙古", "宁夏", "新疆", "西藏", "青海", "甘肃"]
    merged = ' '.join([query or '', text or ''])
    for p in provinces:
        if p in merged:
            return p
    return '全国'


def clean_text_for_real(text, summary=''):
    """
    对已解析的干净文本做轻清洗：清理 HTML 实体、去除残余噪声碎片
    （正文来自 fetch_clean_content，已经是 BeautifulSoup 解析后的干净文本）
    """
    if not text:
        return text
    # 清理 HTML 实体
    text = re.sub(r'&[a-zA-Z]{2,10};', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&#x[0-9a-fA-F]+;', ' ', text)
    # 去除残余噪声行
    lines = text.split('\n')
    cleaned = []
    seen = set()
    for line in lines:
        line = line.strip()
        if len(line) < 6:
            continue
        if any(w in line.lower() for w in [
            'copyright', '版权所有', 'cookie', '隐私政策', '网站地图',
            '请您登录', '请登录', '无障碍', '长者专区', 'loading',
            'ajax', 'javascript', 'jquery',
        ]):
            continue
        key = line[:30].strip().lower()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(line)
    return '\n'.join(cleaned)


def normalize_item(item, query, region):
    title = (item.get('title') or '').strip()
    url = (item.get('url') or item.get('id') or '').strip()
    summary = (item.get('summary') or item.get('snippet') or '').strip()
    # Plan A: 尝试从真实 URL 抓取干净正文
    raw_text = None
    if url:
        raw_text = fetch_clean_content(url, title=title, summary=summary)
    # 降级：使用 Exa 返回的原始 text
    if not raw_text:
        raw_text = (item.get('text') or item.get('content') or summary).strip()
    # 对原始正文做轻清洗（保留段落结构）
    text = clean_text_for_real(raw_text, summary)
    org = first_match(ORG_PATTERNS, '\n'.join([title, summary, text]))
    publish_date = first_match(DATE_PATTERNS, '\n'.join([title, summary, text]))
    row_region = infer_region(query, region, '\n'.join([title, summary, text]))
    doc_type = infer_type(title, summary, text)
    return {
        '标题': title,
        '正文': text,
        '摘要': summary,
        '发文机关': org,
        '发布时间': publish_date,
        '原始链接': url,
        '关键词': query,
        '类型': doc_type,
        '地区': row_region,
    }


def main():
    if len(sys.argv) < 4:
        print('usage: write_exa_results.py <input_json> <query> <region>', file=sys.stderr)
        sys.exit(1)
    input_json = Path(sys.argv[1]).expanduser()
    query = sys.argv[2]
    region = sys.argv[3]
    data = json.loads(input_json.read_text(encoding='utf-8'))
    if isinstance(data, dict):
        items = data.get('results') or data.get('items') or []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    # Validate URLs and filter out invalid ones
    valid_items = []
    invalid_count = 0
    for item in items:
        url = (item.get('url') or item.get('id') or '').strip()
        if url and is_url_valid(url):
            valid_items.append(item)
        else:
            invalid_count += 1

    rows = [normalize_item(item, query, region) for item in valid_items]
    safe = re.sub(r'[^\w\u4e00-\u9fff-]+', '_', query)[:60].strip('_') or 'exa-search'
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = Path('~/Desktop/exa搜索文件夹').expanduser() / f'{safe}_{ts}'
    out_dir.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = '搜索结果'
    ws.append(COLUMNS)

    # Header style
    header_font = Font(bold=True)
    header_fill = PatternFill(fill_type='solid', fgColor='D9E1F2')
    for col_idx, col_name in enumerate(COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    # Data rows
    url_col_idx = COLUMNS.index('原始链接') + 1
    col_widths = {'标题': 30, '正文': 50, '摘要': 30, '发文机关': 20, '发布时间': 15, '原始链接': 35, '关键词': 20, '类型': 12, '地区': 12}
    for row_idx, row in enumerate(rows, 2):
        for col_idx, col_name in enumerate(COLUMNS, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.alignment = Alignment(vertical='top', wrap_text=True)
            if col_name == '原始链接':
                url = row[col_name]
                if url:
                    cell.hyperlink = url
                    cell.value = url
                    cell.font = Font(color='0563C1', underline='single')
            else:
                cell.value = row[col_name]
        ws.row_dimensions[row_idx].height = 20

    # Set column widths
    for col_idx, col_name in enumerate(COLUMNS, 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = col_widths.get(col_name, 15)

    # Header row height
    ws.row_dimensions[1].height = 22
    xlsx_path = out_dir / '搜索结果.xlsx'
    wb.save(xlsx_path)

    print(json.dumps({
        'output_dir': str(out_dir),
        'excel': str(xlsx_path),
        'count': len(rows),
        'invalid_count': invalid_count,
        'columns': COLUMNS,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
