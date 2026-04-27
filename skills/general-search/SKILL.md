---
name: general-search
description: 通用多页搜索技能。百度全网搜索，不限政府网站，支持任意话题。触发词：事件、人物、产品、技术等非政策类搜索需求。
---

# General Search - 通用多页搜索

## 概述

通用搜索技能，不限政府网站，对任意话题进行百度全网搜索，流程与 v4/testv4 相同（Safari 多页抓取）。

**与 v4 的根本区别：**

| | v4/testv4 | general-search |
|--|----------|---------------|
| 搜索范围 | `site:gov.cn` 政府官网 | 百度全网 |
| 适用场景 | 政府政策文件采集 | 事件、话题、产品、技术等 |

## 目录结构

```
~/Desktop/搜索文件夹/
├── 通用h5/{搜索词}_{时间戳}/     # Safari 抓取的 HTML 源码
├── 通用处理文件夹/
│   ├── 搜索结果.xlsx
│   └── 原文链接.md
└── detail-h5/{搜索词}_{时间戳}.xlsx
```

## 流程

### 第 1 步：扩词

```bash
python3 scripts/build_single_policy_query.py "武汉市樱花节"
```

无 site 限制，返回全国搜索词。

### 第 2 步：Safari 多页抓取

```bash
bash scripts/capture_multi_page_baidu.command "武汉市樱花节" 3 "2026-01-01,2026-12-31"
```

结果保存到 `~/Desktop/搜索文件夹/通用h5/`

### 第 3 步：合并处理

```bash
python3 scripts/process_search_h5_multi.py "武汉市樱花节"
```

### 第 4 步：批量抓详情

```bash
python3 scripts/fetch_detail_links_general.py "武汉市樱花节"
```

## 输出字段（12列）

标题、正文、摘要、发文机关、发布时间、原始链接、关键词、类型、地区、抓取状态、正文长度、是否需要浏览器兜底

## 环境依赖

- macOS + Safari + osascript
- Python 3 + openpyxl

## 修改记录

- 2026-04-03：SKILL.md 重写；补全 read_meta.py；文档与实际流程一致
