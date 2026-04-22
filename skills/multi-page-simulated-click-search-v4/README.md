# multi-page-simulated-click-search-v4

基于 Safari 模拟点击的自动化政策搜索工作流，将自然语言需求转化为结构化政策数据库。

## 功能特性

- **多省份并行搜索**：支持单省/多省政策搜索
- **智能扩词**：自然语言 → 结构化搜索词
- **多页翻页抓取**：自动翻页保存百度搜索结果 HTML
- **时间筛选**：支持年份区间精确筛选
- **批量详情抓取**：5 线程并发抓取政策正文
- **段落结构保留**：正文保持原有段落格式

## 目录结构

```
├── SKILL.md              # Skill 定义文件
├── scripts/
│   ├── build_single_policy_query.py    # 单结果扩词
│   ├── capture_multi_page_baidu.command # Safari 多页抓取
│   ├── process_search_h5_multi.py      # 合并解析 H5
│   ├── fetch_detail_links.py           # 批量抓政策详情
│   └── multi_province_search.py        # 多省搜索调度
├── references/
│   ├── province_rules/     # 省份域名规则
│   └── operations-and-requirements.md
└── dist/
    └── multi-page-simulated-click-search.skill
```

## 使用方法

### 1. 扩词

```bash
python3 scripts/build_single_policy_query.py "2020-2026年湖北省农村振兴"
```

### 2. Safari 抓取

```bash
bash scripts/capture_multi_page_baidu.command "农村振兴 site:www.hubei.gov.cn" 3 "2020-01-01,2026-12-31"
```

### 3. 合并解析

```bash
python3 scripts/process_search_h5_multi.py <搜索词前缀>
```

### 4. 批量抓详情

```bash
python3 scripts/fetch_detail_links.py <搜索关键词>
```

## 环境依赖

- macOS
- Safari
- Python 3
- openpyxl

## 输出目录

`~/Desktop/搜索文件夹/`
