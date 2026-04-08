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


def strip_html(html):
    """用 html.parser 深度清理 HTML，移除 script/style/nav/footer 等噪声块"""
    if not html:
        return ''
    try:
        from html.parser import HTMLParser
    except ImportError:
        return html

    class ContentExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.result = []
            self.skip_depth = 0  # 0=正常收集, >0=跳过
            self.skip_tags = {'script', 'style', 'noscript', 'iframe', 'svg', 'math'}
            self.current_tag = ''
            self._in_body = False

        def handle_starttag(self, tag, attrs):
            self.current_tag = tag
            if tag in self.skip_tags:
                self.skip_depth += 1

        def handle_endtag(self, tag):
            if tag in self.skip_tags and self.skip_depth > 0:
                self.skip_depth -= 1
            if tag == 'body':
                self._in_body = False
            self.current_tag = ''

        def handle_data(self, data):
            if self.skip_depth > 0:
                return
            stripped = data.strip()
            if not stripped:
                return
            # 过滤 JS/CSS 残片
            if self._is_noise(stripped):
                return
            self.result.append(stripped)

        def _is_noise(self, text):
            # 导航类
            if re.match(r'^\[.*\]$', text):  # [首页] > [政务公开]
                return True
            if re.match(r'^\s*>>?\s*$', text):  # 导航箭头
                return True
            # JS代码残片
            if re.search(r'\.ajax\(|\$\(|jQuery\(|handleClick|onclick=|onerror=', text, re.I):
                return True
            # URL残片
            if re.match(r'https?://[^\s]+$', text) and len(text) < 200:
                return True
            # 纯短英文/数字行
            if re.match(r'^[a-zA-Z]{1,30}([.][a-zA-Z]{1,10})?$', text) and len(text) < 40:
                return True
            if re.match(r'^\d+$', text):
                return True
            return False

        def get_text(self):
            return '\n'.join(self.result)

    try:
        # 预处理：去掉已知噪声块
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.I)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html, flags=re.DOTALL | re.I)

        parser = ContentExtractor()
        parser.feed(html)
        return parser.get_text()
    except Exception:
        return html


def clean_text(text, summary=''):
    """深度清洗正文：HTML解析 + 噪声去除 + 去重"""
    if not text:
        return text

    # 第一步：用 html.parser 清理 HTML 结构和 JS/CSS 残片
    text = strip_html(text)

    # 第二步：通用 HTML 实体清理
    text = re.sub(r'&[a-zA-Z]{2,10};', ' ', text)  # &nbsp; &gt; &lt; 等
    text = re.sub(r'&#\d+;', ' ', text)           # &#123; 等

    # 第三步：按段落分割，去除重复段落和噪声
    paragraphs = re.split(r'[\n\r]+', text)
    seen = set()
    cleaned = []

    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 6:
            continue
        # 跳过含显著噪声关键词的段落
        noise_words = ['copyright', '版权所有', 'cookie', '隐私政策', '网站地图',
                       '请您登录', '请登录', '立即登录', '用户登录', '注册账号',
                       'loading', 'loading...', '加载中', '无障碍', '长者专区',
                       'jquery', 'javascript', 'ajax', 'document.cookie']
        if any(w in para.lower() for w in noise_words):
            continue
        # 摘要去重（与摘要前60字相同的段落跳过）
        if summary:
            summary_key = summary[:60].strip().lower()
            if summary_key and summary_key in para.lower():
                continue
        # 段落去重
        para_key = para[:40].strip().lower()
        if para_key and para_key not in seen:
            seen.add(para_key)
            cleaned.append(para)

    return '\n'.join(cleaned)


def normalize_item(item, query, region):
    title = (item.get('title') or '').strip()
    url = (item.get('url') or item.get('id') or '').strip()
    summary = (item.get('summary') or item.get('snippet') or '').strip()
    text = (item.get('text') or item.get('content') or summary).strip()
    text = clean_text(text, summary)
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
