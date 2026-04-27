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

    # 格式: "2026年"（数字+年）
    pattern2 = r'(\d{4})\s*年'
    m2 = re.search(pattern2, text)
    if m2:
        year = int(m2.group(1))
        remaining = re.sub(pattern2, '', text, count=1)
        return f"{year}-01-01", f"{year}-12-31", remaining

    # 格式: 纯数字年份紧跟省份或关键词，如 "2025湖北省政策"
    # 匹配 \d{4} 后面紧跟省份名或其他政策关键词（而非年份）
    # 优先匹配4位数字后紧跟省份名的情况
    pattern3 = r'(\d{4})\s*(?=(?:' + '|'.join(PROVINCE_MAP.keys()) + r'|政策|规划|方案|通知|意见))'
    m3 = re.search(pattern3, text)
    if m3:
        year = int(m3.group(1))
        remaining = re.sub(pattern3, '', text, count=1)
        return f"{year}-01-01", f"{year}-12-31", remaining

    # 无年份
    year = datetime.now().year
    return f"{year}-01-01", f"{year}-12-31", text


def parse_min_results(text: str):
    """提取'至少X条'类要求，返回(min_results, remaining_text)
    - '至少N条' / '不少于N条' / '不低于N条' / 'N条以上'
    - '至少N页' / '不少于N页' / '不低于N页' / 'N页以上' → 均视同 N 条（条=搜索结果数量，非页面数）
    - 无此类要求：返回 None
    """
    patterns = [
        r'至少\s*(\d+)\s*条',
        r'不少于\s*(\d+)\s*条',
        r'不低于\s*(\d+)\s*条',
        r'(\d+)\s*条以上',
        r'(\d+)\s*条\s*(?:以?上|及以上)',
        # "页"视同"条"（用户所说的"页"指搜索结果数量，非页面数）
        r'至少\s*(\d+)\s*页',
        r'不少于\s*(\d+)\s*页',
        r'不低于\s*(\d+)\s*页',
        r'(\d+)\s*页以上',
        r'(\d+)\s*页\s*(?:以?上|及以上)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            n = int(m.group(1))
            remaining = re.sub(pat, '', text, count=1)
            return n, remaining
    return None, text

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

def build_single_result(province: str, abbr: str, domain: str, keyword: str, start_date: str, end_date: str, min_results: int = None):
    """构建单省结果

    min_results: 用户指定的最低结果数，不指定则为 None（默认3页=约30条）
    pages_needed: 根据 min_results 推算所需页数，ceil(min_results / 10)
    """
    pages_needed = None
    if min_results is not None:
        pages_needed = (min_results + 9) // 10  # 每页约10条，向上取整
        pages_needed = max(pages_needed, 1)

    result = {
        '年份': f"{start_date},{end_date}",
        '地区': province,
        '缩写': abbr,
        '域名锚点': f'https://{domain}',
        '清洗后关键词': keyword.strip(),
        '最终搜索词': f"{keyword.strip()} site:{domain}",
        '模式': '单省',
    }
    if min_results is not None:
        result['最低结果数'] = min_results
        result['pages_needed'] = pages_needed
    return result

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

    # 最低结果数（"至少50条"）
    min_results, remaining = parse_min_results(remaining)

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
            r = build_single_result(prov, abbr, domain, keyword, start_date, end_date, min_results)
            results.append(r)

        # 保存元信息（第一省的，供后续步骤使用）
        first = results[0]
        meta = {
            'province': first['地区'],
            'keyword': first['清洗后关键词'],
            'year_range': first['年份'],
            'stamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'min_results': min_results,
            'pages_needed': first.get('pages_needed'),
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
        result = build_single_result('全国', 'china', 'www.gov.cn', keyword.strip() or '政策', start_date, end_date, min_results)
        result['域名锚点'] = 'https://www.gov.cn'
        result['最终搜索词'] = f"{keyword.strip() or '政策'} site:gov.cn"
        result['模式'] = '全国'
        meta = {
            'province': '',
            'keyword': result['清洗后关键词'],
            'year_range': result['年份'],
            'stamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'min_results': min_results,
            'pages_needed': result.get('pages_needed'),
        }
        meta_path = Path.home() / '.search_meta.json'
        meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
