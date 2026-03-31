---
name: cnki-simulated-search
description: 中国知网模拟点击搜索与摘要抓取技能。用于处理“去中国知网搜索某个主题”“抓知网搜索结果列表”“提取知网标题、作者、来源、年份、详情链接”“进一步抓取可访问详情页的摘要、关键词、作者机构、文献类型等基础信息”等需求。适用于第一阶段只做：(1) 搜索结果页抓取与解析，(2) 详情页/摘要页基础信息抓取；不承诺全文 PDF 下载。
---

# CNKI Simulated Search

## Overview

这个技能只做第一阶段：
- 模拟点击打开中国知网搜索
- 抓搜索结果页 H5
- 解析结果列表
- 逐条抓可访问详情页/摘要页基础信息

当前不承诺：
- 全文 PDF 下载
- 绕过权限限制
- 稳定获取所有详情页完整正文

## Bundled Scripts

- `scripts/capture_cnki_search.command`
  - 用 Safari 打开知网并执行搜索，保存搜索结果页 H5
- `scripts/process_cnki_search_h5.py`
  - 解析知网搜索结果页，输出结果列表 Excel + md
- `scripts/fetch_cnki_detail_pages.py`
  - 按结果列表逐条抓取可访问详情页，提取摘要信息并输出详情 Excel

## Workflow

### 1. 搜索页抓取

运行：
- `scripts/capture_cnki_search.command <搜索词>`

目标：
- 打开知网搜索
- 输入搜索词
- 保存当前搜索结果页 H5 到桌面目录

### 2. 搜索结果解析

运行：
- `python3 scripts/process_cnki_search_h5.py <h5文件路径>`

目标：
- 提取标题、作者、来源、年份、详情链接等
- 输出结构化结果表

### 3. 详情页基础抓取

运行：
- `python3 scripts/fetch_cnki_detail_pages.py`

目标：
- 从结果列表读取详情链接
- 抓摘要、关键词、作者机构、文献类型等
- 输出详情表

## Output Paths

默认输出目录：
- `~/Desktop/cnki-h5/`
- `~/Desktop/cnki-output/`

## Hard Rules

- 当前只做搜索结果列表与详情摘要信息抓取
- 不把全文 PDF 下载作为第一阶段硬目标
- 如果遇到权限页、登录页、验证码页，要如实保留状态，不伪造内容
