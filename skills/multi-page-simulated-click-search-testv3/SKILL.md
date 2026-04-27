---
name: multi-page-simulated-click-search-testv3
description: 多页模拟点击搜索工作流测试版 v3。核心功能同 testv2，支持单省和多省搜索。区别：v3 使用 Playwright（Chromium）作为 JS 渲染页面的兜底方案——HTTP 抓取正文不足 100 字时自动触发 Playwright 渲染，比纯 Safari AppleScript 更稳定。完整流程：单结果扩词 → Safari 新建窗口抓取多页百度搜索结果（含年份筛选，默认3页） → 合并解析 → 批量直抓政策详情（正文保留段落结构，5线程并发，Playwright 兜底） → 输出 Excel + 原文链接。所有输出文件统一存放在 ~/Desktop/搜索文件夹/ 下，便于管理。
---

# Multi-Page Simulated Click Search Test v3

## 概述

政策/官方文件搜索的完整自动化流水线，功能同 testv2。**核心区别：v3 在 fetch_detail_links.py 中内置了 Playwright 兜底逻辑**，当 HTTP 抓取的正文不足 100 字时，自动使用 Playwright 渲染 JS 后重新抓取。

**Playwright 兜底条件：**
- HTTP 抓取正文长度 < 100 字
- 自动使用 Chromium headless 浏览器渲染 JS
- 反检测配置：禁用 AutomationControlled、模拟真实 Chrome UA

**testv3 vs testv2：**
| | testv2 | testv3 |
|---|---|---|
| Safari 多页抓取 | ✅ | ✅ |
| 多省搜索 | ✅ | ✅ |
| HTTP 详情抓取 | ✅ | ✅ |
| Playwright 兜底 | ❌ | ✅ |
| Excel 样式 | ✅ | ✅ |
| 固定9字段 | ✅ | ✅ |

## 目录结构

```
~/Desktop/搜索文件夹/
├── h5/{省份}+{搜索词}_{时间戳}/
│   └── {时间戳}_{搜索词}_page{N}.md
├── 处理文件夹/
│   ├── 搜索结果.xlsx
│   └── 原文链接.md
└── detail-h5/{关键词}_{时间戳}.xlsx
```

## 脚本列表

| 脚本 | 说明 |
|------|------|
| `scripts/build_single_policy_query.py` | 单结果扩词（支持多省拆分） |
| `scripts/capture_multi_page_baidu.command` | Safari 多页抓取（新建窗口） |
| `scripts/process_search_h5_multi.py` | 合并解析多页 H5（支持多省合并） |
| `scripts/fetch_detail_links.py` | 批量直抓政策详情（5线程并发 + Playwright 兜底） |
| `scripts/multi_province_search.py` | 多省搜索调度器 |

## 流程详解

### 第 1 步：单结果扩词

```bash
python3 scripts/build_single_policy_query.py "2020-2026年湖北省农村振兴"
```

### 第 2 步：Safari 多页抓取

```bash
bash scripts/capture_multi_page_baidu.command "农村振兴 site:www.hubei.gov.cn" 3 "2020-01-01,2026-12-31"
```

### 第 3 步：合并处理多页结果

```bash
python3 scripts/process_search_h5_multi.py <搜索词前缀>
```

### 第 4 步：批量直抓详情（含 Playwright 兜底）

```bash
python3 scripts/fetch_detail_links.py <搜索关键词>
```

**Playwright 兜底逻辑：**
```
HTTP 抓取正文
    ↓
正文长度 >= 100 字？ → ✅ 直接用
    ↓ 否
触发 Playwright 兜底：
  - 启动 Chromium（headless，模拟真实 Chrome UA）
  - 等待 JS 渲染（wait_until='load' + 3秒）
  - 提取渲染后 HTML
  - 用同样解析逻辑提取正文
    ↓
正文 > 原HTTP正文？ → 替换
```

## 环境依赖

- macOS
- Safari
- osascript
- Python 3
- openpyxl
- playwright (`pip3 install playwright && python3 -m playwright install chromium`)
- Chromium（约 150MB，首次安装后常驻）

## 固定 9 字段

标题、正文、摘要、发文机关、发布时间、原始链接、关键词、类型、地区

**（不允许增删字段）**

## Hard Rules

- 只走单结果扩词主路径，不混单页逻辑
- 不返回扩词候选列表
- 页数上限只是上限
- 详情抓取先去重再抓
- Playwright 兜底条件：HTTP 正文 < 100 字
- 政府网站正文若为附件格式（PDF/DOC）则无法解析，保留空值
