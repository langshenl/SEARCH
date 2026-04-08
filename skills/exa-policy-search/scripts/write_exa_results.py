#!/usr/bin/env python3
import json
import os
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

COLUMNS = ["标题", "正文", "摘要", "发文机关", "发布时间", "原始链接", "关键词", "类型", "地区", "可信度"]
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
def fetch_url_meta(url, timeout=5):
    if not url or not url.startswith(('http://', 'https://')):
        return {'ok': False, 'status': None, 'final_url': '', 'title': ''}
    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            final_url = resp.geturl()
            content = resp.read(120000).decode('utf-8', errors='ignore')
            m = re.search(r'<title>(.*?)</title>', content, re.I | re.S)
            title = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
            return {'ok': status < 400, 'status': status, 'final_url': final_url, 'title': title, 'content': content}
    except Exception:
        return {'ok': False, 'status': None, 'final_url': '', 'title': '', 'content': ''}


def score_confidence(result_title, summary, body, meta):
    if not meta.get('ok'):
        return '低可信'
    page_title = meta.get('title', '') or ''
    final_url = meta.get('final_url', '') or ''
    low_title = result_title.lower()
    low_page = page_title.lower()
    low_summary = (summary or '').lower()
    low_body = (body or '').lower()

    title_hit = 0
    for token in re.findall(r'[\u4e00-\u9fffA-Za-z0-9]{2,}', result_title)[:6]:
        if token.lower() in low_page:
            title_hit += 1
    summary_hit = 0
    for token in re.findall(r'[\u4e00-\u9fffA-Za-z0-9]{2,}', summary)[:8]:
        if token.lower() in low_body:
            summary_hit += 1

    if any(k in low_page for k in ['404', 'not found', '错误', '出错']) or any(k in final_url.lower() for k in ['/404', 'error']):
        return '低可信'
    if title_hit >= 2 and summary_hit >= 2:
        return '高可信'
    if title_hit >= 1 or summary_hit >= 1:
        return '中可信'
    return '低可信'


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
    """
    对 Exa 返回的 text/content 做轻清洗：保留段落结构，去实体和残余噪声
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
    raw_text = (item.get('text') or item.get('content') or summary).strip()
    text = clean_text(raw_text, summary)
    meta = fetch_url_meta(url)
    confidence = score_confidence(title, summary, text, meta)
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
        '可信度': confidence,
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

    rows_all = [normalize_item(item, query, region) for item in items]
    invalid_count = sum(1 for r in rows_all if r['可信度'] == '低可信')
    rows = [r for r in rows_all if r['可信度'] != '低可信']
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
    col_widths = {'标题': 30, '正文': 50, '摘要': 30, '发文机关': 20, '发布时间': 15, '原始链接': 35, '关键词': 20, '类型': 12, '地区': 12, '可信度': 12}
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
