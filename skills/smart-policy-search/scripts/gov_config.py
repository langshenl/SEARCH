#!/usr/bin/env python3
"""
官网配置表 - 支持CDP爬虫的政府网站
每个配置定义：域名、搜索URL模板、正文选择器、是否含表格
新增官网只需添加配置，无需修改爬虫代码
"""

# ============================================================
# 部门配置（用于官网搜索，CDP爬虫）
# ============================================================
DEPT_CONFIGS = {
    # 文化和旅游部 ✅ 已验证
    "文化和旅游部": {"domain": "mct.gov.cn", "search_url": "https://www.mct.gov.cn/mctso/s?qt={keyword}", "support_tables": False},
    # 教育部 ✅ 已验证（需表单提交，URL参数无效）
    "教育部": {"domain": "moe.gov.cn", "search_url": "https://so.moe.gov.cn/", "support_tables": False, "search_mode": "form", "search_input": "#qt", "search_button": "#ch-search-b"},
    # 财政部 ✅ 已验证
    "财政部": {"domain": "mof.gov.cn", "search_url": "https://search.mof.gov.cn/was5/web/search?wd={keyword}", "support_tables": False},
    # 国家发展和改革委员会 ✅ 已验证
    "国家发展和改革委员会": {"domain": "ndrc.gov.cn", "search_url": "https://so.ndrc.gov.cn/s?q={keyword}", "support_tables": False},
    # 公安部 ✅ 已验证
    "公安部": {"domain": "mps.gov.cn", "search_url": "https://app.mps.gov.cn/searchweb/search_new.jsp?q={keyword}", "support_tables": False},
    # 民政部 ✅ 已验证
    "民政部": {"domain": "mca.gov.cn", "search_url": "https://so.mca.gov.cn/searchweb/?q={keyword}", "support_tables": False},
    # 商务部 ✅ 已验证
    "商务部": {"domain": "mofcom.gov.cn", "search_url": "https://gzly.mofcom.gov.cn/info/searchText?q={keyword}", "support_tables": False},
    # 人力资源和社会保障部 ✅ 已验证
    "人力资源和社会保障部": {"domain": "mohrss.gov.cn", "search_url": "https://www.mohrss.gov.cn/hsearch/?q={keyword}", "support_tables": False},
    # 自然资源部 ✅ 已验证
    "自然资源部": {"domain": "mnr.gov.cn", "search_url": "https://search.mnr.gov.cn/was5/web/search?wd={keyword}", "support_tables": False},
    # 生态环境部 ✅ 已验证
    "生态环境部": {"domain": "mee.gov.cn", "search_url": "https://www.mee.gov.cn/searchnew/?q={keyword}", "support_tables": False},
    # 住房和城乡建设部 ❌ jsearchfront，需POST，暂无法自动爬取
    "住房和城乡建设部": {"domain": "mohurd.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 交通运输部 ✅ 已验证
    "交通运输部": {"domain": "mot.gov.cn", "search_url": "https://zs.mot.gov.cn/mot/zck/?q={keyword}", "support_tables": False},
    # 水利部 ❌ 超时，无法访问
    "水利部": {"domain": "mwr.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 农业农村部 ✅ 已验证
    "农业农村部": {"domain": "moa.gov.cn", "search_url": "https://www.moa.gov.cn/so/s?qt={keyword}", "support_tables": False},
    # 国家卫生健康委员会 ✅ 已验证
    "国家卫生健康委员会": {"domain": "nhc.gov.cn", "search_url": "https://zs.kaipuyun.cn/s?q={keyword}", "support_tables": False},
    # 应急管理部 ✅ 已验证
    "应急管理部": {"domain": "mem.gov.cn", "search_url": "https://www.mem.gov.cn/was5/web/search?wd={keyword}", "support_tables": False},
    # 科学技术部 ✅ 已验证
    "科学技术部": {"domain": "most.gov.cn", "search_url": "https://www.most.gov.cn/search?q={keyword}", "support_tables": False},
    # 工业和信息化部 ❌ 403，需特定Header
    "工业和信息化部": {"domain": "miit.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 司法部 ❌ 302，需POST
    "司法部": {"domain": "moj.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 国家市场监督管理总局 ❌ 403，需特定Header
    "国家市场监督管理总局": {"domain": "samr.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 国家体育总局 ✅ 已验证
    "国家体育总局": {"domain": "sport.gov.cn", "search_url": "https://www.sport.gov.cn/so/?q={keyword}", "support_tables": False},
    # 国家统计局 ✅ 已验证
    "国家统计局": {"domain": "stats.gov.cn", "search_url": "https://www.stats.gov.cn/search/?q={keyword}", "support_tables": False},
    # 国家知识产权局 ✅ 已验证
    "国家知识产权局": {"domain": "cnipa.gov.cn", "search_url": "https://www.cnipa.gov.cn/jsearchfront/search.do?q={keyword}", "support_tables": False},
    # 国家烟草专卖局 ❌ 超时，无法访问
    "国家烟草专卖局": {"domain": "tobacco.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 国家铁路局 ✅ 已验证
    "国家铁路局": {"domain": "nra.gov.cn", "search_url": "https://www.nra.gov.cn/xxgk/xxgss/?q={keyword}", "support_tables": False},
    # 中国民用航空局 ✅ 已验证
    "中国民用航空局": {"domain": "caac.gov.cn", "search_url": "https://www.caac.gov.cn/INDEX/HLFW/GJHBJHCX2021/?q={keyword}", "support_tables": False},
    # 国家邮政局 ❌ 超时，无法访问
    "国家邮政局": {"domain": "spb.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 国家中医药管理局 ❌ 超时，无法访问
    "国家中医药管理局": {"domain": "satcm.gov.cn", "search_url": "", "support_tables": False, "verified": False},
    # 国务院 ✅ 已验证
    "国务院": {"domain": "gov.cn", "search_url": "https://www.gov.cn/search/?q={keyword}", "support_tables": False},
}

# 部门关键词（用于识别用户提到的部门）
DEPT_KEYWORDS = {
    "文旅部": "文化和旅游部",
    "文化部": "文化和旅游部",
    "旅游部": "文化和旅游部",
    "教育部": "教育部",
    "财政部": "财政部",
    "发改委": "国家发展和改革委员会",
    "公安部": "公安部",
    "民政部": "民政部",
    "商务部": "商务部",
    "人社部": "人力资源和社会保障部",
    "自然资源部": "自然资源部",
    "生态环境部": "生态环境部",
    "住建部": "住房和城乡建设部",
    "交通运输部": "交通运输部",
    "水利部": "水利部",
    "农业农村部": "农业农村部",
    "卫健委": "国家卫生健康委员会",
    "应急管理部": "应急管理部",
    "科技部": "科学技术部",
    "工信部": "工业和信息化部",
    "司法部": "司法部",
    "市场监管总局": "国家市场监督管理总局",
    "体育总局": "国家体育总局",
    "统计局": "国家统计局",
    "知识产权局": "国家知识产权局",
    "烟草局": "国家烟草专卖局",
    "铁路局": "国家铁路局",
    "民航局": "中国民用航空局",
    "邮政局": "国家邮政局",
    "中医药管理局": "国家中医药管理局",
    "国务院": "国务院",
}


def detect_dept_source(query):
    """检测是否有部门关键词，返回所有匹配的部门名列表"""
    matched = []
    for keyword, dept_name in DEPT_KEYWORDS.items():
        if keyword in query and dept_name in DEPT_CONFIGS:
            if dept_name not in matched:
                matched.append(dept_name)
    return matched


# 省份关键词（用于自动识别）
PROVINCE_KEYWORDS = {
    "北京", "天津", "河北", "山西", "内蒙古",
    "辽宁", "吉林", "黑龙江",
    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "广西", "海南",
    "重庆", "四川", "贵州", "云南", "西藏",
    "陕西", "甘肃", "青海", "宁夏", "新疆",
}


# ============================================================
# 通用选择器（作为 fallback，所有部门共用）
# ============================================================
GENERIC_LINK_SELECTORS = [
    ".news-list a",
    ".article-list a",
    ".result-list a",
    ".list a",
    "h3 a",
    "h2 a",
    ".tab-list a",
    "a[href*='/zwgk']",
    "a[href*='/art']",
    "a[href*='/news']",
    "a[href*='/html']",
    "a[href*='/info']",
    ".search-result a",
    ".search-list a",
    ".so-result a",
    ".search-item a",
    ".result-item a",
]

GENERIC_CONTENT_SELECTORS = [
    ".TRS_Editor",
    ".article-content",
    ".article",
    ".detail-content",
    ".content",
    "#zoom",
    "article",
    "main",
    ".main-content",
    "[class*='content']",
    "[id*='content']",
    "body",
]
