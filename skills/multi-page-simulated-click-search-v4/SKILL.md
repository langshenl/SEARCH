---
name: multi-page-simulated-click-search-v4
description: 多页模拟点击搜索工作流（v4）。支持单省和多省搜索。完整流程：单结果扩词 → Safari 新建窗口抓取多页百度搜索结果（含年份筛选，默认3页） → 合并解析 → 批量直抓政策详情（正文保留段落结构，5线程并发） → 输出 Excel + 原文链接。所有输出文件统一存放在 ~/Desktop/搜索文件夹/ 下，便于管理。
---

# Multi-Page Simulated Click Search Test v2

## 概述

政策/官方文件搜索的完整自动化流水线。将自然语言需求转化为结构化政策数据库，支持多省份、多关键词搜索，结果保留原文段落格式。

**验证记录（2026-04-02）：**
- ✅ 四川省"经济发展"搜索：3页全抓，时间筛选生效，29条详情，25条GOOD
- ✅ 湖北省"农村振兴"搜索：5页全抓，48条详情，43条GOOD
- ✅ 湖南省"乡村教育"搜索：5页全抓，48条详情，44条GOOD，4条FETCH_ERROR
- ✅ 湖北省"新能源"搜索：3页全抓，时间筛选生效，30条详情，29条GOOD，1条PARTIAL，总耗时约80秒
- ✅ 河北省"乡村振兴"搜索：3页全抓，时间筛选生效，30条详情，30条PARTIAL（政府网站JS渲染，需浏览器兜底）

## 目录结构

```
~/Desktop/搜索文件夹/
├── h5/{省份}+{搜索词}_{时间戳}/
│   └── {时间戳}_{搜索词}_page{N}.md    # 每页 HTML 源码
├── 处理文件夹/
│   ├── 搜索结果.xlsx          # 标题/简介/百度链接/原文链接
│   └── 原文链接.md             # 原始链接列表
└── detail-h5/{关键词}_{时间戳}.xlsx  # 9列政策详情
```

## 新增多省搜索

```bash
python3 scripts/multi_province_search.py "湖南湖北新能源"
```

**流程：** 扩词 → 逐省 Safari 抓取 → 合并所有省 H5 → 合并处理 → 详情抓取

**支持两种 H5 目录命名格式：**
- 有省份前缀：`湖北+新能源 site_www.hubei.gov.cn_时间戳/`
- 无省份前缀：`新能源 site_www.hubei.gov.cn_时间戳/`

**域名锚点：** `https://www.hubei.gov.cn` 等

## 脚本列表

| 脚本 | 说明 |
|------|------|
| `scripts/build_single_policy_query.py` | 单结果扩词（支持多省拆分） |
| `scripts/capture_multi_page_baidu.command` | Safari 多页抓取（新建窗口） |
| `scripts/process_search_h5_multi.py` | 合并解析多页 H5（支持多省合并） |
| `scripts/fetch_detail_links.py` | 批量直抓政策详情（5线程并发，9列输出） |
| `scripts/multi_province_search.py` | 多省搜索调度器 |

## 流程详解

### 第 1 步：单结果扩词

```bash
python3 scripts/build_single_policy_query.py "2020-2026年湖北省农村振兴"
```

**输出示例：**
```json
{
  "年份": "2020-01-01,2026-12-31",
  "地区": "湖北省",
  "域名锚点": "https://www.hubei.gov.cn",
  "清洗后关键词": "农村振兴",
  "最终搜索词": "农村振兴 site:www.hubei.gov.cn",
  "模式": "单省"
}
```

**扩词规则：**
- 年份区间（2020-2026年）→ 取头尾，格式 `2020-01-01,2026-12-31`
- 单年份（2026年）→ 格式 `2026-01-01,2026-12-31`
- 无年份 → 默认当前年
- **结果数量（可选）**：`至少30条` / `不少于30条` / `不低于30条` → 自动换算所需页数 `ceil(30/10)=3` 页，**上限10页**；不说默认3页
- 识别省份匹配政府域名（省份词不进入搜索关键词，由域名区分）
- 单省：关键词 + `site:www.{省}.gov.cn`
- 全国：关键词 + `site:gov.cn`
- 只输出一个唯一结果，不返回候选列表

### 第 2 步：Safari 多页抓取

```bash
bash scripts/capture_multi_page_baidu.command "农村振兴 site:www.hubei.gov.cn" 3 "2020-01-01,2026-12-31"
```

**参数：**
1. 最终搜索词（必填）
2. 最大页数（**默认 3**，但若 meta 文件有 `pages_needed` 则自动覆盖）
3. 年份区间（可选，格式 `2020-01-01,2026-12-31`）

**自动页数逻辑：**
- `build_single_policy_query` 解析出"至少X条" → 写入 `~/.search_meta.json` → `capture_multi_page_baidu.command` 启动时读取 → 用 `pages_needed` 覆盖 `MAX_PAGES`
- 无数量指定 → 默认3页
- pages_needed 最多10页（"直到没有"的上限）

**Safari 关键机制：**
- 创建**全新 Safari 窗口** `make new document` 并设置 URL
- 新窗口只有搜索 tab，`front document` 始终正确指向搜索页
- 点击"时间不限"下拉框 → 填写年份区间 → 确认
- 逐页保存 HTML 源码到 `~/Desktop/搜索文件夹/h5/{搜索词}_{时间戳}/`
- 完成后 `close front document` 关闭窗口，不影响原窗口

**Safari 选择器（已验证有效）：**
- 时间按钮：`document.getElementById('timeRlt')`
- 日期面板：`.custom_2wanX`
- 日期输入框：panel 内的前两个 text 类型 input
- 确认按钮：panel 内的 `button`
- 下一页：`innerText.trim() === '下一页'`

### 第 3 步：合并处理多页结果

```bash
python3 scripts/process_search_h5_multi.py <搜索词前缀>
```

**输入：** 传入搜索词前缀（不含时间戳），自动模糊匹配找到对应的 `{搜索词}_{时间戳}` 目录并解析所有页面
**输出：**
- `~/Desktop/搜索文件夹/处理文件夹/搜索结果.xlsx`（标题/简介/百度链接/原文链接）
- `~/Desktop/搜索文件夹/处理文件夹/原文链接.md`

结果为 0 时返回"暂未搜索到相关内容"。

### 第 4 步：批量直抓原文详情

```bash
python3 scripts/fetch_detail_links.py <搜索关键词>
```

**输入：** `~/Desktop/搜索文件夹/处理文件夹/原文链接.md`
**输出：** `~/Desktop/搜索文件夹/detail-h5/{关键词}_{时间戳}.xlsx`

**规则：**
- 先按原文链接去重，再抓取
- **5 线程并发**抓取，每条间隔 1 秒
- 超时时间：5 秒（避免拖慢整体）
- 输出固定 28 字段，不删列
- **正文保留段落结构**：块级标签（`<p><div><li><tr><section><article>` 等）转为换行，段落分明
- 正文过短（< 120 字）/ 缺时间 / 抓取失败 → 标记 `需要浏览器兜底: 是`
- 输出统计：`RAW_LINK_COUNT / UNIQUE_LINK_COUNT / COUNT`

**28 字段：**
标题、正文、摘要、发文机关、发布时间、原始链接、关键词、类型、地区

## 环境依赖

- macOS
- Safari
- osascript
- Python 3
- openpyxl

## Hard Rules

- 只走单结果扩词主路径，不混单页逻辑
- 不返回扩词候选列表
- 页数上限只是上限，抓到哪里算哪里
- 详情抓取先去重再抓
- 政府网站正文若为 JS 渲染导致正文字数过短，标记浏览器兜底候选

## 修改记录

- 2026-04-03：与 testv4 脚本同步；SKILL.md 更新版本号、多省双格式目录、9列输出说明
