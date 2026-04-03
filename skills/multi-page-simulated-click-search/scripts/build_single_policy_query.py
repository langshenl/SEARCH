#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.parse

PROVINCE_DOMAINS = {
    '北京市': 'https://www.beijing.gov.cn',
    '天津市': 'https://www.tj.gov.cn',
    '河北省': 'https://www.hebei.gov.cn',
    '山西省': 'https://www.shanxi.gov.cn',
    '内蒙古': 'https://www.nmg.gov.cn',
    '辽宁省': 'https://www.ln.gov.cn',
    '吉林省': 'https://www.jl.gov.cn',
    '黑龙江省': 'https://www.hlj.gov.cn',
    '上海市': 'https://www.shanghai.gov.cn',
    '江苏省': 'https://www.jiangsu.gov.cn',
    '浙江省': 'https://www.zj.gov.cn',
    '安徽省': 'https://www.ah.gov.cn',
    '福建省': 'https://www.fujian.gov.cn',
    '江西省': 'https://www.jiangxi.gov.cn',
    '山东省': 'http://www.shandong.gov.cn',
    '河南省': 'https://www.henan.gov.cn',
    '湖北省': 'https://www.hubei.gov.cn',
    '湖南省': 'https://www.hunan.gov.cn',
    '广东省': 'https://www.gd.gov.cn',
    '广西': 'http://www.gxzf.gov.cn',
    '海南省': 'https://www.hainan.gov.cn',
    '重庆市': 'https://www.cq.gov.cn',
    '四川省': 'https://www.sc.gov.cn',
    '贵州省': 'https://www.guizhou.gov.cn',
    '云南省': 'https://www.yn.gov.cn',
    '西藏': 'https://www.xizang.gov.cn',
    '陕西省': 'https://www.shaanxi.gov.cn',
    '甘肃省': 'https://www.gansu.gov.cn',
    '青海省': 'http://www.qinghai.gov.cn',
    '宁夏': 'https://www.nx.gov.cn',
    '新疆': 'https://www.xinjiang.gov.cn',
}

ALIASES = {
    '北京': '北京市', '北京市': '北京市', '天津': '天津市', '天津市': '天津市', '上海': '上海市', '上海市': '上海市',
    '重庆': '重庆市', '重庆市': '重庆市', '河北': '河北省', '河北省': '河北省', '山西': '山西省', '山西省': '山西省',
    '内蒙': '内蒙古', '内蒙古': '内蒙古', '内蒙古自治区': '内蒙古', '辽宁': '辽宁省', '辽宁省': '辽宁省',
    '吉林': '吉林省', '吉林省': '吉林省', '黑龙江': '黑龙江省', '黑龙江省': '黑龙江省', '江苏': '江苏省', '江苏省': '江苏省',
    '浙江': '浙江省', '浙江省': '浙江省', '安徽': '安徽省', '安徽省': '安徽省', '福建': '福建省', '福建省': '福建省',
    '江西': '江西省', '江西省': '江西省', '山东': '山东省', '山东省': '山东省', '河南': '河南省', '河南省': '河南省',
    '湖北': '湖北省', '湖北省': '湖北省', '湖南': '湖南省', '湖南省': '湖南省', '广东': '广东省', '广东省': '广东省',
    '广西': '广西', '广西壮族自治区': '广西', '海南': '海南省', '海南省': '海南省', '四川': '四川省', '四川省': '四川省',
    '贵州': '贵州省', '贵州省': '贵州省', '云南': '云南省', '云南省': '云南省', '西藏': '西藏', '西藏自治区': '西藏',
    '陕西': '陕西省', '陕西省': '陕西省', '甘肃': '甘肃省', '甘肃省': '甘肃省', '青海': '青海省', '青海省': '青海省',
    '宁夏': '宁夏', '宁夏回族自治区': '宁夏', '新疆': '新疆', '新疆维吾尔自治区': '新疆',
}

FILLERS = [
    '帮我搜索一下', '帮我搜一下', '搜索一下', '搜一下', '帮我搜索', '帮我搜', '搜索', '搜',
    '一下', '相关内容', '相关', '内容'
]


def extract_year(text: str) -> tuple[str, str]:
    """返回 (起始年, 终止年)，支持年份区间如'2023到2026年'"""
    # 支持的区间格式：2023到2026年、2023年至2026年、2023-2026年、2023~2026年
    range_m = re.search(r'(20\d{2})\s*(?:到|至|-|~)\s*(20\d{2})\s*年?', text)
    if range_m:
        start, end = sorted([range_m.group(1), range_m.group(2)])
        return start, end
    m = re.search(r'(20\d{2})年?', text)
    year = m.group(1) if m else str(dt.datetime.now().year)
    return year, year


def extract_region(text: str):
    if '全国' in text:
        return '全国'
    for alias in sorted(ALIASES.keys(), key=len, reverse=True):
        if alias in text:
            return ALIASES[alias]
    return None


def clean_query_text(text: str) -> str:
    s = text.strip()
    for x in FILLERS:
        s = s.replace(x, '')
    s = re.sub(r'\s+', '', s)
    s = s.replace('的相关政策', '政策')
    s = s.replace('相关政策', '政策')
    s = s.replace('政策相关', '政策')
    s = s.replace('的政策', '政策')
    s = s.replace('政策的', '政策')
    s = s.replace('的', '')
    return s.strip('，,。；;：: ')


def remove_year_tokens(text: str) -> str:
    # 先去掉年份区间格式（2023到2026年、2023至2026年、2023-2026年）
    s = re.sub(r'20\d{2}\s*(?:到|至|-|~)\s*20\d{2}年?', '', text)
    # 再去掉单个年份
    s = re.sub(r'20\d{2}年?', '', s)
    return re.sub(r'\s+', '', s).strip()


def host_of(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc


def build(text: str) -> dict:
    """
    输入：自然语言，如 "搜索2026年湖北省政策"、"2023到2026年湖北省新能源政策"
    返回：{年份区间, 地区, 域名锚点, 清洗后关键词, 最终搜索词, 模式}
    """
    from datetime import datetime as dt

    # 0. 原始文本备用
    raw = text.strip()

    # 1. 提取年份区间
    range_m = re.search(r'(20\d{2})\s*(?:到|至|-|~)\s*(20\d{2})\s*年?', raw)
    if range_m:
        start_year, end_year = sorted([range_m.group(1), range_m.group(2)])
    else:
        m = re.search(r'(20\d{2})年?', raw)
        y = m.group(1) if m else str(dt.now().year)
        start_year = end_year = y

    # 2. 用原始文本识别省份（不受清洗影响）
    region = extract_region(raw) or ''
    if not region:
        region = extract_region(re.sub(r'^去(搜索|找|查)', '', raw)) or ''

    # 3. 清洗文本
    cleaned = clean_query_text(raw)

    # 4. 去掉"到"前缀（clean_query_text 加的）和年份
    for prefix in ['去', '到']:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    # 5. 去掉年份区间和单个年份
    cleaned = re.sub(r'20\d{2}\s*(?:到|至|-|~)\s*20\d{2}年?', '', cleaned)
    cleaned = re.sub(r'20\d{2}年?', '', cleaned)
    cleaned = re.sub(r'\s+', '', cleaned).strip()

    # 6. 去掉省份前缀
    keyword = cleaned
    if region:
        # 去掉省份简称和全称
        for alias in sorted(ALIASES.keys(), key=len, reverse=True):
            full = ALIASES[alias]
            if full == region:
                for prefix in [alias, region]:
                    if keyword.startswith(prefix):
                        keyword = keyword[len(prefix):]
                        break
        # 去掉开头残留的"省"字
        keyword = re.sub(r'^省+', '', keyword)

    # 7. 只有省份没有任何其他词时才加"政策"
    if not keyword.strip():
        keyword = '政策'

    year_field = f'{start_year}-01-01,{end_year}-12-31'

    # 8. 根据模式组装
    if region == '全国':
        return {
            '年份': year_field,
            '地区': '全国',
            '域名锚点': 'gov.cn',
            '清洗后关键词': keyword,
            '最终搜索词': f'{keyword} site:www.gov.cn',
            '模式': '全国',
        }
    elif region and region in PROVINCE_DOMAINS:
        site = PROVINCE_DOMAINS[region]
        host = host_of(site)
        return {
            '年份': year_field,
            '地区': region,
            '域名锚点': site,
            '清洗后关键词': keyword,
            '最终搜索词': f'{keyword} site:{host}',
            '模式': '单省',
        }
    else:
        return {
            '年份': year_field,
            '地区': '',
            '域名锚点': 'gov.cn',
            '清洗后关键词': keyword,
            '最终搜索词': f'{keyword} site:www.gov.cn',
            '模式': '普通',
        }



def main():
    if len(sys.argv) < 2:
        print('用法: python3 build_single_policy_query.py "搜索湖北省新能源相关政策"')
        return 1
    text = sys.argv[1]
    result = build(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
