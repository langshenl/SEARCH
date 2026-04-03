#!/usr/bin/env python3
"""单结果扩词 + 多省份支持"""
import re, json, sys
from pathlib import Path
from datetime import datetime

PROVINCE_MAP = {
    '北京': ('bj', 'www.beijing.gov.cn'),
    '天津': ('tj', 'www.tj.gov.cn'),
    '河北': ('hebei', 'www.hebei.gov.cn'),
    '山西': ('sx', 'www.shanxi.gov.cn'),
    '内蒙古': ('nmg', 'www.nmg.gov.cn'),
    '辽宁': ('ln', 'www.ln.gov.cn'),
    '吉林': ('jl', 'www.jilin.gov.cn'),
    '黑龙江': ('hljs', 'www.hl.gov.cn'),
    '上海': ('sh', 'www.shanghai.gov.cn'),
    '江苏': ('js', 'www.jiangsu.gov.cn'),
    '浙江': ('zj', 'www.zhejiang.gov.cn'),
    '安徽': ('ah', 'www.ah.gov.cn'),
    '福建': ('fj', 'www.fujian.gov.cn'),
    '江西': ('jx', 'www.jiangxi.gov.cn'),
    '山东': ('sd', 'www.sd.gov.cn'),
    '河南': ('henan', 'www.henan.gov.cn'),
    '湖北': ('hub', 'www.hubei.gov.cn'),
    '湖南': ('hun', 'www.hunan.gov.cn'),
    '广东': ('gd', 'www.gd.gov.cn'),
    '广西': ('gx', 'www.gx.gov.cn'),
    '海南': ('hai', 'www.hainan.gov.cn'),
    '重庆': ('cq', 'www.cq.gov.cn'),
    '四川': ('sc', 'www.sc.gov.cn'),
    '贵州': ('gz', 'www.guizhou.gov.cn'),
    '云南': ('yn', 'www.yn.gov.cn'),
    '西藏': ('xz', 'www.xizang.gov.cn'),
    '陕西': ('shaanx', 'www.shaanxi.gov.cn'),
    '甘肃': ('gs', 'www.gansu.gov.cn'),
    '青海': ('qh', 'www.qh.gov.cn'),
    '宁夏': ('nx', 'www.nx.gov.cn'),
    '新疆': ('xj', 'www.xj.gov.cn'),
}

def parse_year_range(text: str):
    """提取年份区间，返回(最小年,最大年,剩余文本)"""
    # 格式: "2020-2026年"、"2020至2026年"、"2020~2026"
    pattern = r'(\d{4})\s*[-至~]\s*(\d{4})\s*年?'
    m = re.search(pattern, text)
    if m:
        start_year, end_year = int(m.group(1)), int(m.group(2))
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        remaining = re.sub(pattern, '', text, count=1)
        return f"{start_year}-01-01", f"{end_year}-12-31", remaining

    # 格式: "2026年"
    pattern2 = r'(\d{4})\s*年'
    m2 = re.search(pattern2, text)
    if m2:
        year = int(m2.group(1))
        remaining = re.sub(pattern2, '', text, count=1)
        return f"{year}-01-01", f"{year}-12-31", remaining

    # 无年份
    year = datetime.now().year
    return f"{year}-01-01", f"{year}-12-31", text

def extract_provinces(text: str):
    """提取所有省份，返回 (provinces_list, remaining_text)"""
    provinces = []
    seen = set()
    remaining = text
    while True:
        found = False
        for prov, (abbr, domain) in PROVINCE_MAP.items():
            idx = remaining.find(prov)
            if idx != -1 and prov not in seen:
                provinces.append((prov, abbr, domain))
                seen.add(prov)
                remaining = remaining[:idx] + remaining[idx+len(prov):]
                found = True
        if not found:
            break
    return provinces, remaining

def extract_keyword_for_province(text: str, province: str):
    """为指定省份提取其专属关键词（省份后的文本）"""
    idx = text.find(province)
    if idx == -1:
        return text
    after = text[idx+len(province):]
    # 去掉标点和语气词
    keyword = re.sub(r'[,，的得地]+', ' ', after)
    keyword = re.sub(r'\s+', ' ', keyword).strip()
    return keyword or '政策'

def build_single_result(province: str, abbr: str, domain: str, keyword: str, start_date: str, end_date: str):
    """构建单省结果"""
    return {
        '年份': f"{start_date},{end_date}",
        '地区': province,
        '缩写': abbr,
        '域名锚点': f'https://{domain}',
        '清洗后关键词': keyword.strip(),
        '最终搜索词': f"{keyword.strip()} site:{domain}",
        '模式': '单省'
    }

def main():
    if len(sys.argv) < 2:
        print("用法: build_single_policy_query.py <自然语言需求>", file=sys.stderr)
        sys.exit(1)

    raw = sys.argv[1]
    raw_copy = raw

    # 清理常见语气词
    for w in ['搜索', '查找', '查询', '帮我', '我想', '请', '一下', '的']:
        raw_copy = re.sub(w, '', raw_copy)

    # 年份区间
    start_date, end_date, remaining = parse_year_range(raw_copy)

    # 提取省份
    provinces, kw_text = extract_provinces(remaining)

    # 共同关键词（kw_text 是去掉省份后的剩余文本）
    keyword = kw_text
    # 去掉累积的"省"字（去掉省份后，"省"可能连续残留）
    keyword = re.sub(r'省+', '', keyword)
    keyword = re.sub(r'[,，的得地\s]+', ' ', keyword).strip()
    keyword = keyword or '政策'

    # 为每个省生成结果，共享同一个关键词
    if provinces:
        results = []
        for prov, abbr, domain in provinces:
            r = build_single_result(prov, abbr, domain, keyword, start_date, end_date)
            results.append(r)

        # 保存元信息（第一省的，供后续步骤使用）
        first = results[0]
        meta = {
            'province': first['地区'],
            'keyword': first['清洗后关键词'],
            'year_range': first['年份'],
            'stamp': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        meta_path = Path.home() / '.search_meta.json'
        meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')

        # 输出所有结果
        if len(results) == 1:
            # 单省：输出单个对象（兼容原有逻辑）
            print(json.dumps(results[0], ensure_ascii=False, indent=2))
        else:
            # 多省：用分隔符连接，去掉末尾分隔符
            output = '\n---SEPARATOR---\n'.join(json.dumps(r, ensure_ascii=False, indent=2) for r in results)
            print(output)
    else:
        # 无省份，按全国处理
        result = {
            '年份': f"{start_date},{end_date}",
            '地区': '全国',
            '缩写': 'china',
            '域名锚点': 'https://www.gov.cn',
            '清洗后关键词': keyword.strip() or '政策',
            '最终搜索词': f"{keyword.strip() or '政策'} site:gov.cn",
            '模式': '全国'
        }
        meta = {
            'province': '',
            'keyword': result['清洗后关键词'],
            'year_range': result['年份'],
            'stamp': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        meta_path = Path.home() / '.search_meta.json'
        meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
