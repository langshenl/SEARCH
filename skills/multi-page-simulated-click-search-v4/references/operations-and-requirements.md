# Operations and Requirements

## What this skill does

This skill packages the current verified multi-page simulated click search workflow for policy and official-document searches.

It performs:
- single-result policy query expansion
- direct use of the unique final query
- Safari + Baidu simulated search
- current-year time filter
- multi-page capture of search result H5 files
- merged parsing of multi-page search results
- deduplicated direct fetching of original policy links
- structured policy-detail Excel output
- hyperlink output for source URLs in Excel
- one retained classification field: `类型`
- browser-fallback candidate marking

## Environment requirements

Required runtime environment:
- macOS
- Safari
- osascript (AppleScript)
- Python 3
- Python package: `openpyxl`

Why:
- multi-page capture depends on Safari automation
- result parsing and detail extraction depend on Python scripts
- Excel output depends on `openpyxl`

## Required output directories

The current workflow writes to these desktop folders:
- `~/Desktop/h5/`
- `~/Desktop/处理文件夹/`
- `~/Desktop/detail-h5/`

These folders can be auto-created by scripts when needed.

## Bundled scripts and what each one does

### 1. `scripts/build_single_policy_query.py`

Purpose:
- Clean natural-language search input
- Extract an explicit year if present, otherwise default to current year
- Detect province or nationwide scope
- Match province to government domain
- Return one unique final search query

Rules:
- single province → `年份 + 搜索关键词 + site:省级域名`
- nationwide → `年份 + 搜索关键词 + site:gov.cn`
- return only one final result
- do not output multiple candidates
- do not write CSV
- do not write `搜索配置文件夹`

### 2. `scripts/capture_multi_page_baidu.command`

Purpose:
- Open Safari
- Search Baidu with the selected query
- Click the time filter
- Fill current-year start/end date
- Save page 1 H5
- Click next page repeatedly
- Save page 2 / page 3 ... until target page limit or no next page
- Close only the current search page while keeping Safari window alive

Parameters:
- arg1: search query
- arg2: max page count (default `3`)

Output:
- multiple H5/HTML-equivalent files in `~/Desktop/h5/`

Important rules:
- max pages is an upper bound, not a guarantee
- if available pages are fewer than requested, capture only existing pages
- stop normally when no next page exists

### 3. `scripts/process_search_h5_multi.py`

Purpose:
- Read a batch of multi-page H5 files from the same capture run
- Merge results across pages
- Resolve Baidu redirect links to final landing URLs when possible
- Deduplicate merged search results
- Output normalized search-result files

Input:
- file prefix for one capture batch

Outputs:
- `~/Desktop/处理文件夹/搜索结果.xlsx`
- `~/Desktop/处理文件夹/原文链接.md`

Output columns in `搜索结果.xlsx`:
- 标题
- 简介
- 原始百度链接
- 原文链接

### 4. `scripts/fetch_detail_links.py`

Purpose:
- Read `原文链接.md`
- Count raw links
- Deduplicate final original links
- Fetch detail pages one by one
- Extract structured fields
- Output policy-detail Excel
- Write source links as clickable hyperlinks in Excel

Input:
- `~/Desktop/处理文件夹/原文链接.md`

Output:
- `~/Desktop/detail-h5/搜索词_YYYYMMDD_HHMMSS.xlsx`

Important rules:
- serial fetching
- 1-second spacing between links
- keep all required columns even if values are missing
- keep only one classification field: `类型`
- `类型` represents what the policy is for (e.g. 发展规划 / 工作部署 / 项目申报 / 产业扶持 / 管理规范 / 建设实施 / 政策解读 / 统计报告 / 资金预算 / 人才引进 / 综合管理)
- support multiple government URL formats for 政策ID extraction

## Full workflow order

### Step 1. Build one final search query

Run:
```bash
python3 scripts/build_single_policy_query.py "搜索湖北省政策"
```

Result example:
- `2026年 湖北省政策 site:www.hubei.gov.cn`

### Step 2. Run multi-page Baidu capture

Run:
```bash
scripts/capture_multi_page_baidu.command "2026年 湖北省政策 site:www.hubei.gov.cn" 3
```

Result:
- page1/page2/page3 H5 files are saved to `~/Desktop/h5/`

### Step 3. Merge and parse captured search pages

Run:
```bash
python3 scripts/process_search_h5_multi.py "20260331_152309_2026年 湖北省政策 site_www.hubei.gov.cn"
```

Result:
- merged search results Excel
- merged original-link markdown

### Step 4. Fetch original policy-detail pages

Run:
```bash
python3 scripts/fetch_detail_links.py
```

Result:
- detail Excel in `~/Desktop/detail-h5/`

## Current workflow rules

- The whole workflow defaults to multi-page search
- Query expansion returns only one final result
- Search page count is capped by a target maximum, but actual page count depends on what Baidu offers
- If page count is insufficient, capture whatever pages exist
- If merged result count is `0`, return exactly:
  - `暂未搜索到相关内容`
- Detail fetching uses deduplicated original links
- Raw link count and unique link count should both be surfaced
- Policy ID extraction should support multiple government URL styles
- Final Excel should use clickable hyperlinks for source URLs
- The retained classification field is `类型`, not `政策类型` or `政策用途`

## Required detail output fields

The detail Excel must always keep these columns:
- 政策ID
- 标题
- 正文
- 摘要
- 发文机关
- 联合发文机关
- 发布时间
- 文号
- 政策层级
- 地区
- 所属行业
- 类型
- 政策主题
- 关键词
- 适用对象
- 支持方式
- 申报条件
- 申报时间
- 有效期
- 政策状态
- 原始链接
- 附件链接
- 相似政策
- 上位政策/下位政策关系
- 抓取状态
- 正文长度
- 是否检测到附件
- 是否需要浏览器兜底

Rule:
- if a field cannot be extracted, leave it empty
- never remove required columns

## Browser fallback

Browser fallback is not the default for all items.

Use fallback candidates when:
- `抓取状态` is `PARTIAL` or `POOR`
- or `是否需要浏览器兜底 = 是`

## Migration checklist for another machine

When moving this skill to another OpenClaw machine:

1. Install the skill package or copy the whole skill directory
2. Ensure macOS + Safari are available
3. Ensure `osascript` works
4. Ensure Python 3 is installed
5. Install `openpyxl`
6. Verify desktop output folders can be created
7. Run one test query end-to-end

Recommended validation query examples:
- `搜索湖北省政策`
- `搜索湖北省新能源相关政策`
- `搜索四川的相关政策`
- `搜索云南省政策`
- `搜索河北政策`

## Packaging artifact

Packaged skill file:
- `dist/multi-page-simulated-click-search.skill`

Recommended transfer target:
- another OpenClaw machine that runs on macOS

## Non-goal

This skill does not preserve old single-page search as its main workflow.
Single-page logic is not part of the intended default path for this packaged skill.
