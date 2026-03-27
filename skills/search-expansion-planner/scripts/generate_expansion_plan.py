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
DEFAULT_THEME_LABEL = "通用主题"
REQUIRED_FIELDS = ["年份", "地区", "原始需求", "标准主题", "扩展方向", "搜索词", "状态", "执行备注"]

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

NATIONAL_PROVINCES = [
    "北京市", "天津市", "上海市", "重庆市",
    "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
    "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "海南省",
    "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省",
    "内蒙古自治区", "广西壮族自治区", "西藏自治区",
    "宁夏回族自治区", "新疆维吾尔自治区"
]

NATIONAL_DIRECTIONS = ["扶持政策", "发展政策", "建设政策"]

GENERIC_POLICY_SUFFIXES = [
    "扶持政策", "发展政策", "建设政策", "管理政策", "服务政策",
    "保障政策", "改革政策", "创新政策", "提升政策", "监管政策",
    "数字化政策", "人才政策", "财政支持政策", "运营政策", "实施政策"
]

STOPWORDS = [
    "帮我搜索", "帮我查找", "帮我查", "搜索", "搜一下", "搜索一下", "查找", "查一下", "查",
    "请帮我", "麻烦帮我", "帮忙", "一下", "一下子",
    "湖北省内", "省内", "所有的", "相关内容", "相关政策", "内容",
    "关于", "有关", "方面", "方面的", "领域", "领域的", "相关", "内", "年", "的"
]

ALL_POLICY_PATTERNS = [
    "所有政策", "全部政策", "政策内容", "全省政策", "所有政策内容", "全部政策内容"
]

NATIONAL_PATTERNS = ["全国", "中国", "全国范围", "全国各省", "全国各地"]

NORMALIZE_MAP = {
    "教育方面": "教育",
    "教育领域": "教育",
    "教育相关": "教育",
    "教育方面的": "教育",
    "农业方面": "农业",
    "农业领域": "农业",
    "新能源方面": "新能源",
    "博物馆方面": "博物馆"
}


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


def is_all_policy_request(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return any(pat in compact for pat in ALL_POLICY_PATTERNS)


def is_national_request(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return any(pat in compact for pat in NATIONAL_PATTERNS)


def detect_template_theme(text: str, templates: dict):
    lowered = text.strip()
    for theme, meta in templates.items():
        if theme in lowered:
            return theme
        for alias in meta.get("aliases", []):
            if alias in lowered:
                return theme
    return None


def extract_generic_theme(text: str, province: str, year: str) -> str:
    cleaned = text
    if province:
        cleaned = cleaned.replace(province, "")
        cleaned = cleaned.replace(province.replace("省", "").replace("市", ""), "")
    cleaned = cleaned.replace("全国", "")
    cleaned = cleaned.replace("中国", "")
    cleaned = cleaned.replace(f"{year}年", "")
    cleaned = cleaned.replace(year, "")
    for src, dst in NORMALIZE_MAP.items():
        cleaned = cleaned.replace(src, dst)
    for word in STOPWORDS:
        cleaned = cleaned.replace(word, "")
    cleaned = re.sub(r"[，。、；：,.!?？\s]+", "", cleaned)
    cleaned = re.sub(r"^(关于|有关|请|麻烦|帮我|帮忙)+", "", cleaned)
    cleaned = re.sub(r"^(全国的|中国的|全国|中国)+", "", cleaned)
    cleaned = re.sub(r"(相关|方面|领域|内容)+$", "", cleaned)
    if not cleaned:
        return DEFAULT_THEME_LABEL
    return cleaned


def build_generic_expansions(theme: str):
    if theme == DEFAULT_THEME_LABEL:
        return [
            "专题政策", "扶持政策", "发展政策", "管理政策", "实施政策",
            "财政支持政策", "人才政策", "数字化政策"
        ]
    if theme == "全部政策":
        return [
            "经济政策", "科技政策", "工业政策", "招商投资政策", "人才就业政策",
            "财税金融政策", "营商环境政策", "农业政策", "环保双碳政策", "教育政策",
            "医疗卫生政策", "交通物流政策"
        ]
    expansions = []
    for suffix in GENERIC_POLICY_SUFFIXES:
        expansions.append(f"{theme}{suffix}")
    expansions.extend([
        f"{theme}公共服务政策",
        f"{theme}资源保护政策",
        f"{theme}文旅融合政策",
        f"{theme}场馆建设政策",
        f"{theme}教育推广政策"
    ])
    deduped = []
    seen = set()
    for item in expansions:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def build_rows(user_query: str, year: str, province: str, theme: str, expansions):
    rows = []
    for item in expansions:
        rows.append({
            "年份": year,
            "地区": province,
            "原始需求": user_query,
            "标准主题": theme,
            "扩展方向": item,
            "搜索词": f"{year}年{province}{item}",
            "状态": "未执行",
            "执行备注": ""
        })
    return rows


def build_national_rows(user_query: str, year: str, theme: str):
    rows = []
    base_theme = theme.replace("政策", "")
    for province in NATIONAL_PROVINCES:
        for direction in NATIONAL_DIRECTIONS:
            expanded = f"{base_theme}{direction}"
            rows.append({
                "年份": year,
                "地区": province,
                "原始需求": user_query,
                "标准主题": theme,
                "扩展方向": expanded,
                "搜索词": f"{year}年{province}{expanded}",
                "状态": "未执行",
                "执行备注": ""
            })
    return rows


def validate_rows(rows):
    if not rows:
        raise ValueError("扩展结果为空，无法生成表格")
    for idx, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(f"第 {idx} 行缺少字段：{', '.join(missing)}")
        for field in REQUIRED_FIELDS:
            if row.get(field) is None:
                raise ValueError(f"第 {idx} 行字段为空：{field}")


def write_csv(rows):
    validate_rows(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
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
    template_theme = detect_template_theme(user_query, templates)
    national_mode = is_national_request(user_query)

    if is_all_policy_request(user_query):
        theme = "全部政策"
        expansions = build_generic_expansions(theme)
        mode = "all-policy"
        rows = build_rows(user_query, year, province, theme, expansions)
    elif national_mode:
        if template_theme:
            theme = template_theme
        else:
            theme = extract_generic_theme(user_query, "全国", year)
        mode = "national"
        rows = build_national_rows(user_query, year, theme)
        province = "全国"
        expansions = []
    elif template_theme:
        theme = template_theme
        expansions = templates[theme]["expansions"]
        mode = "template"
        rows = build_rows(user_query, year, province, theme, expansions)
    else:
        theme = extract_generic_theme(user_query, province, year)
        expansions = build_generic_expansions(theme)
        mode = "generic"
        rows = build_rows(user_query, year, province, theme, expansions)
    write_csv(rows)

    print(f"已生成扩展表：{OUTPUT_PATH}")
    print(f"年份：{year}")
    print(f"地区：{province}")
    print(f"主题：{theme}")
    print(f"模式：{mode}")
    print(f"扩展数量：{len(rows)}")


if __name__ == "__main__":
    main()
