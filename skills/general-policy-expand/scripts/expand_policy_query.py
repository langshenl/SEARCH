#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
import urllib.parse
from pathlib import Path

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

PROVINCE_ALIASES = {
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
    '帮我搜索一下', '帮我搜一下', '搜索一下', '搜一下', '搜索', '搜',
    '政策相关内容', '相关内容', '相关', '内容', '一下', '方面', '领域'
]

GENERIC_DIRECTIONS = ['发展规划', '实施意见', '若干措施', '管理办法', '工作通知', '建设方案', '申报指南', '专项政策']
TOPIC_TEMPLATES = {
    '博物馆': ['博物馆发展规划', '博物馆实施意见', '博物馆管理办法', '博物馆建设方案', '博物馆扶持政策', '文物保护实施意见', '公共文化服务若干措施', '博物馆工作通知'],
    '农业': ['农业发展规划', '农业实施意见', '农业管理办法', '农业扶持政策', '高标准农田建设方案', '粮食安全实施意见', '农业若干措施', '农业工作通知'],
    '新能源': ['新能源发展规划', '新能源实施意见', '新能源管理办法', '新能源扶持政策', '光伏建设方案', '储能实施意见', '新能源若干措施', '新能源工作通知'],
    '教育': ['教育发展规划', '教育实施意见', '教育管理办法', '教育建设方案', '教育扶持政策', '教育若干措施', '教育工作通知', '教育专项政策'],
}


def extract_year(text: str) -> str:
    m = re.search(r'(20\d{2})年?', text)
    return m.group(1) if m else str(dt.datetime.now().year)


def extract_province(text: str):
    for alias in sorted(PROVINCE_ALIASES.keys(), key=len, reverse=True):
        if alias in text:
            return PROVINCE_ALIASES[alias]
    return None


def clean_text(text: str) -> str:
    s = text.strip()
    for x in FILLERS:
        s = s.replace(x, '')
    s = re.sub(r'\s+', '', s)
    s = s.replace('的政策', '政策').replace('的', '')
    return s


def detect_mode(text: str) -> str:
    t = text.replace(' ', '')
    if '全国' in t:
        return '全国'
    if any(k in t for k in ['政策', '实施意见', '管理办法', '若干措施', '发展规划', '通知', '公告', '工作方案', '建设方案']):
        return '政策'
    return '普通'


def extract_topic(cleaned: str, province: str | None) -> str | None:
    s = cleaned
    if province:
        variants = {province, province.replace('省', ''), province.replace('市', '')}
        for v in sorted(variants, key=len, reverse=True):
            if v:
                s = s.replace(v, '')
    s = s.replace('全国', '')
    s = s.replace('政策', '')
    s = s.strip()
    return s or None


def host_of(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc


def make_rows(year: str, province: str, raw_topic: str | None, directions: list[str], mode: str):
    site = PROVINCE_DOMAINS[province]
    host = host_of(site)
    rows = []
    for d in directions:
        query = f'{year}年 {province} {d} site:{host}'
        rows.append({
            '年份': year,
            '地区': province,
            '域名锚点': site,
            '原始主题': raw_topic or '泛政策',
            '扩展方向': d,
            '搜索关键词': query,
            '模式': mode,
        })
    return rows


def expand(text: str):
    year = extract_year(text)
    province = extract_province(text)
    mode = detect_mode(text)
    cleaned = clean_text(text)
    topic = extract_topic(cleaned, province)

    if mode == '普通':
        return {'mode': '普通', 'rows': [{'年份': year, '地区': province or '', '域名锚点': '', '原始主题': topic or '', '扩展方向': '', '搜索关键词': text, '模式': '普通'}]}

    if '全国' in text:
        if topic and topic in TOPIC_TEMPLATES:
            base = [TOPIC_TEMPLATES[topic][0], TOPIC_TEMPLATES[topic][1]]
        elif topic:
            base = [f'{topic}发展规划', f'{topic}实施意见']
        else:
            base = ['发展规划', '实施意见']
        rows = []
        for p in PROVINCE_DOMAINS:
            rows.extend(make_rows(year, p, topic, base[:2], '全国'))
        return {'mode': '全国', 'rows': rows}

    if province:
        if topic and topic in TOPIC_TEMPLATES:
            directions = TOPIC_TEMPLATES[topic][:8]
        elif topic:
            directions = [f'{topic}发展规划', f'{topic}实施意见', f'{topic}若干措施', f'{topic}管理办法', f'{topic}建设方案', f'{topic}扶持政策', f'{topic}工作通知', f'{topic}专项政策'][:8]
        else:
            directions = GENERIC_DIRECTIONS[:8]
        rows = make_rows(year, province, topic, directions, '单省')
        return {'mode': '单省', 'rows': rows}

    return {'mode': '普通', 'rows': [{'年份': year, '地区': '', '域名锚点': '', '原始主题': topic or '', '扩展方向': '', '搜索关键词': text, '模式': '普通'}]}


def main():
    if len(sys.argv) < 2:
        print('用法: python3 expand_policy_query.py "河北省政策"')
        return 1
    text = sys.argv[1]
    result = expand(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    out_dir = Path.home() / 'Desktop' / '搜索配置文件夹'
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / 'general-policy-expand-output.csv'
    rows = result['rows']
    fields = ['年份', '地区', '域名锚点', '原始主题', '扩展方向', '搜索关键词', '模式']
    with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'CSV: {csv_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
