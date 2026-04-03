---
name: general-search-test
description: 通用多页搜索技能（测试版）。对任意话题进行百度搜索，Safari 模拟点击抓取多页结果，批量提取详情。不限政府网站，支持任意关键词搜索。触发词：搜索/查找/查询任意话题。
---

# General Search Test - 通用多页搜索（测试版）

## 概述

通用搜索技能，不做域名限制。对任意话题进行百度搜索，保留与 testv4 相同的多页 Safari 模拟点击流程。

**与 testv4 的区别：**

| | testv4 | general-search |
|--|--------|---------------|
| 搜索范围 | `site:gov.cn` 政府官网 | 百度全网 |
| 关键词 | 政策相关 | 任意话题 |
| 适用场景 | 政府政策文件采集 | 事件、人物、话题、行业等普通搜索 |

## 流程

### 第 1 步：扩词

```bash
python3 scripts/build_single_policy_query.py "2025年人工智能发展至少50页"
```

支持：
- 年份区间：`2020-2026年`
- 纯数字年份紧跟省份：`2025湖北省AI发展`
- 最低结果数：`至少50条` / `不少于30页`
- 默认3页，上限10页

### 第 2 步：Safari 多页抓取

```bash
bash scripts/capture_multi_page_baidu.command "人工智能 发展" 3 "2025-01-01,2025-12-31"
```

与 testv4 完全相同的 Safari 模拟点击流程。

### 第 3 步：合并处理

```bash
python3 scripts/process_search_h5_multi.py "<h5目录路径>"
```

### 第 4 步：批量抓详情

```bash
python3 scripts/fetch_detail_links_general.py "<关键词>"
```

## 输出字段（12列）

标题、正文、摘要、发文机关、发布时间、原始链接、关键词、类型、地区、抓取状态、正文长度、是否需要浏览器兜底

## 环境依赖

- macOS
- Safari
- osascript
- Python 3
- openpyxl
