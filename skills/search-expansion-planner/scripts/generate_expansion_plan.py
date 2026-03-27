#!/usr/bin/env python3
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_PATH = BASE_DIR / "references" / "theme_templates.json"
OUTPUT_DIR = Path.home() / "Desktop" / "搜索配置文件夹"
OUTPUT_PATH = OUTPUT_DIR / "current-expansion-plan.csv"
DEFAULT_PROVINCE = "湖北省"
DEFAULT_THEME = "农业政策"

PROVINCES = [
    "北京市", "天津市", "上海市", "重庆市",
    "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
    "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "海南省",
    "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省",
    "台湾省", "内蒙古自治区", "广西壮族自治区", "西藏自治区",
    "宁夏回族自治区", "新疆维吾尔自治区",
    "香港特别行政区", "澳门特别行政区",
    "北京", "天津", "上海", "重庆",
    "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "海南",
    "四川", "贵州", "云南", "陕西", "甘肃", "青海",
    "台湾", "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"
]


def load_templates():
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_province(name: str) -> str:
    mapping = {
        "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市",
        "河北": "河北省", "山西": "山西省", "辽宁": "辽宁省", "吉林": "吉林省", "黑龙江": "黑龙江省",
        "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省", "福建": "福建省", "江西": "江西省", "山东": "山东省",
        "河南": "河南省", "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "海南": "海南省",
        "四川": "四川省", "贵州": "贵州省", "云南": "云南省", "陕西": "陕西省", "甘肃": "甘肃省", "青海": "青海省",
        "内蒙古": "内蒙古自治区", "广西": "广西壮族自治区", "西藏": "西藏自治区", "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
        "香港": "香港特别行政区", "澳门": "澳门特别行政区", "台湾": "台湾省"
    }
    return mapping.get(name, name)


def extract_year(text: str) -> str:
    match = re.search(r"(20\d{2})年?", text)
    if match:
        return match.group(1)
    return str(datetime.now().year)


def extract_province(text: str) -> str:
    for province in sorted(PROVINCES, key=len, reverse=True):
        if province in text:
            return normalize_province(province)
    return DEFAULT_PROVINCE


def detect_theme(text: str, templates: dict) -> str:
    lowered = text.strip()
    for theme, meta in templates.items():
        if theme in lowered:
            return theme
        for alias in meta.get("aliases", []):
            if alias in lowered:
                return theme
    return DEFAULT_THEME


def build_rows(user_query: str, year: str, province: str, theme: str, templates: dict):
    expansions = templates[theme]["expansions"]
    rows = []
    for item in expansions:
        rows.append({
            "年份": year,
            "地区": province,
            "原始需求": user_query,
            "标准主题": theme,
            "扩展方向": item,
            "搜索词": f"{year}年{province}{item}",
            "状态": "待执行",
            "执行备注": ""
        })
    return rows


def write_csv(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = ["年份", "地区", "原始需求", "标准主题", "扩展方向", "搜索词", "状态", "执行备注"]
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    templates = load_templates()
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:]).strip()
    else:
        user_query = input("请输入搜索需求：").strip()

    if not user_query:
        print("错误：搜索需求不能为空")
        sys.exit(1)

    year = extract_year(user_query)
    province = extract_province(user_query)
    theme = detect_theme(user_query, templates)
    rows = build_rows(user_query, year, province, theme, templates)
    write_csv(rows)

    print(f"已生成扩展表：{OUTPUT_PATH}")
    print(f"年份：{year}")
    print(f"地区：{province}")
    print(f"主题：{theme}")
    print(f"扩展数量：{len(rows)}")


if __name__ == "__main__":
    main()
