---
name: simulated-click-search-workflow
description: 模拟点击搜索总控技能。用于处理“按整套流程搜索政策/官方文件”“先扩词再模拟点击百度搜索”“抓搜索结果页 H5、解析结果、批量直抓原文详情”等请求。适用于需要： (1) 从自然语言搜索需求开始，(2) 先生成扩词候选并等待用户选择，(3) 用 Safari 模拟点击百度搜索并设置本年时间筛选，(4) 保存搜索结果页 H5 到桌面，(5) 解析搜索结果并输出 Excel 与原文链接 md，(6) 批量直抓原文链接并输出结构化政策详情 Excel，(7) 对缺失严重的条目标记浏览器兜底。
---

# Simulated Click Search Workflow

## Overview

这是当前整套“模拟点击搜索”主流程技能。

它把下面这些步骤串起来：
- 扩词
- 用户选词
- Safari 打开百度并设置时间筛选
- 保存搜索结果页 H5
- 处理搜索结果页 H5
- 输出搜索结果 Excel + 原文链接 md
- 批量直抓原文链接
- 输出政策详情 Excel
- 标记需要浏览器兜底的条目

## Full Workflow

### 1. 输入原始搜索需求

用户输入自然语言需求，例如：
- 搜索湖北省政策
- 搜索河北省博物馆政策

### 2. 扩词

先调用扩词/搜索流程层，返回候选搜索词。

规则：
- 扩词只在对话中展示
- 不自动继续执行
- 等用户从候选扩词中选定一条

### 3. 用户选定一条扩词

用户明确选定某一条搜索词后，后续流程才继续。

### 4. 模拟点击百度搜索并设置时间筛选

使用桌面正式脚本：
- `~/Desktop/百度_Safari_H5抓取.command`

脚本动作：
- Safari 打开百度
- 输入用户选中的搜索词
- 进入搜索结果页
- 点击“时间不限”
- 填入本年的第一天和最后一天
- 点击“确认”
- 保存搜索结果页 H5/HTML 到 `~/Desktop/h5/`

### 5. 处理搜索结果页 H5

调用：
- `search-h5-processor`

脚本：
- `~/.openclaw/workspace-search/skills/search-h5-processor/scripts/process_search_h5.py`

输入：
- `~/Desktop/h5/` 中最新或指定的搜索结果页文件

输出到：
- `~/Desktop/处理文件夹/`

固定输出文件：
- `搜索结果.xlsx`
- `原文链接.md`

规则：
- 覆盖上次结果
- 不做追加
- `搜索结果.xlsx` 只保留以下字段：
  - 标题
  - 简介
  - 原始百度链接
  - 原文链接
- `原文链接.md` 优先写入真实政府落地链接

### 6. 批量直抓原文链接

调用：
- `detail-link-fetcher`

脚本：
- `~/.openclaw/workspace-search/skills/detail-link-fetcher/scripts/fetch_detail_links.py`

输入：
- `~/Desktop/处理文件夹/原文链接.md`

规则：
- 串行抓取
- 每条间隔 1 秒
- 优先采用直抓，不默认打开 Safari

输出到：
- `~/Desktop/detail-h5/政策详情抓取结果.xlsx`

### 7. 政策详情输出字段

第六步输出的 Excel 中必须始终包含这些字段：
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
- 政策类型
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

规则：
- 抓不到的数据留空
- 不允许删列

### 8. 浏览器兜底策略

如果第六步结果中：
- 抓取状态为 `PARTIAL` 或 `POOR`
- 或 `是否需要浏览器兜底 = 是`

则这些条目属于第七步浏览器兜底候选。

当前兜底技能保留为：
- `detail-page-capture`

## Key Paths

- 搜索页抓取脚本：`~/Desktop/百度_Safari_H5抓取.command`
- 搜索结果页目录：`~/Desktop/h5/`
- 搜索结果处理目录：`~/Desktop/处理文件夹/`
- 政策详情输出目录：`~/Desktop/detail-h5/`
- 搜索结果处理脚本：`~/.openclaw/workspace-search/skills/search-h5-processor/scripts/process_search_h5.py`
- 原文详情抓取脚本：`~/.openclaw/workspace-search/skills/detail-link-fetcher/scripts/fetch_detail_links.py`

## Hard Rules

- 整套流程默认先扩词，再等待用户选词。
- 第四步必须使用模拟点击百度搜索页的方式执行。
- 第五步结果必须覆盖上次执行结果。
- 第五步的原文链接优先输出真实政府落地链接。
- 第六步默认优先采用直抓。
- 第七步浏览器兜底只处理缺失严重的条目，不默认全量再跑 Safari。
