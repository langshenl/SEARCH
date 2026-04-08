#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

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


def is_url_valid(url, timeout=5):
    if not url or not url.startswith(('http://', 'https://')):
        return False
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode() < 400
    except Exception:
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.getcode() < 400
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


def clean_text(text, summary=''):
    """加强正文清洗：去 script/style/html 噪音，保留可读文本"""
    if not text:
        return ''

    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<noscript[\s\S]*?</noscript>', ' ', text, flags=re.I)
    text = re.sub(r'<!--[\s\S]*?-->', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-zA-Z]{2,10};', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&#x[0-9a-fA-F]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    noise_patterns = [
        r'\bvar\s+\$?\w+\s*=.*?;',
        r'\$\.ajax\(|jQuery\(|\$\(function',
        r'https?://[^\s]{5,200}',
        r'\bfunction\s*\w+\s*\([^)]*\)\s*\{',
    ]
    for p in noise_patterns:
        text = re.sub(p, ' ', text, flags=re.I)

    parts = re.split(r'(?<=[。！？；])\s*', text)
    cleaned = []
    seen = set()
    for part in parts:
        part = part.strip()
        if len(part) < 8:
            continue
        if any(w in part.lower() for w in [
            'copyright', '版权所有', 'cookie', '隐私政策', '网站地图',
            '请您登录', '请登录', '无障碍', '长者专区', 'loading',
            'ajax', 'javascript', 'jquery', 'header 开始', 'header 结束',
            'content 开始', '当前位置 开始', '当前位置 结束', '移动端菜单开始', '移动端菜单结束'
        ]):
            continue
        key = part[:40].strip().lower()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(part)
    return '\n'.join(cleaned)


def normalize_item(item, query, region):
    title = (item.get('title') or '').strip()
    url = (item.get('url') or item.get('id') or '').strip()
    summary = (item.get('summary') or item.get('snippet') or '').strip()
    raw_text = (item.get('text') or item.get('content') or '').strip()
    text = clean_text(raw_text, summary)
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

    header_font = Font(bold=True)
    header_fill = PatternFill(fill_type='solid', fgColor='D9E1F2')
    for col_idx, col_name in enumerate(COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

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

    for col_idx, col_name in enumerate(COLUMNS, 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = col_widths.get(col_name, 15)

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
