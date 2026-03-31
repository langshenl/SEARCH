---
name: multi-page-simulated-click-search
description: 多页模拟点击搜索工作流。用于把政策/官方文件搜索需求，按“扩词 → 默认选第1条 → Safari 百度搜索并设置本年时间筛选 → 连续翻页抓取多页 H5 → 合并解析搜索结果 → 原文链接去重后批量直抓详情 → 标记浏览器兜底候选”这条流程执行。适用于需要迁移、复用、打包当前这套多页政策搜索能力时使用。
---

# Multi-Page Simulated Click Search

## Overview

把当前稳定可用的多页政策搜索流程收拢为一个可迁移 skill。

这个 skill 只保留多页流程相关内容，不混单页逻辑。

## Bundled Scripts

- `scripts/capture_multi_page_baidu.command`
  - Safari 多页模拟点击抓取脚本
  - 作用：打开百度、设置本年时间筛选、连续抓取多页搜索结果页 H5，并在结束后关闭当前搜索页但保留 Safari 窗口

- `scripts/process_search_h5_multi.py`
  - 多页搜索结果合并处理脚本
  - 作用：读取同一批次前缀的多页 H5，合并解析，输出 `搜索结果.xlsx` 和 `原文链接.md`

- `scripts/fetch_detail_links.py`
  - 原文详情直抓脚本
  - 作用：读取 `原文链接.md`，先按原文链接去重，再批量抓详情并输出政策详情 Excel

## Workflow

### 1. 扩词

先用扩词技能或脚本生成候选搜索词。

规则：
- 默认自动选择第 1 条扩词
- 用户明确指定第 2 条、第 3 条时再覆盖

### 2. 多页抓取

运行：
- `scripts/capture_multi_page_baidu.command`

输入参数：
- 第 1 个参数：搜索词
- 第 2 个参数：目标页数上限，默认 3

规则：
- 用 Safari 打开百度搜索结果页
- 点击“时间不限”并设置本年时间范围
- 逐页保存 H5 到 `~/Desktop/h5/`
- 自动点击“下一页”继续翻页
- 如果页码不够，就抓到哪里算哪里
- 没有下一页时正常停止，不报错
- 关闭当前搜索页时保留 Safari 窗口存在

### 3. 合并处理多页结果

运行：
- `scripts/process_search_h5_multi.py <同批次文件前缀>`

输入：
- `~/Desktop/h5/` 中的同一批次多页 H5 文件

输出：
- `~/Desktop/处理文件夹/搜索结果.xlsx`
- `~/Desktop/处理文件夹/原文链接.md`

规则：
- 覆盖输出，不追加
- 合并后去重
- `搜索结果.xlsx` 只保留：标题、简介、原始百度链接、原文链接

### 4. 直抓原文详情

运行：
- `scripts/fetch_detail_links.py`

输入：
- `~/Desktop/处理文件夹/原文链接.md`

输出：
- `~/Desktop/detail-h5/YYYYMMDD_HHMMSS_关键词_政策详情抓取结果.xlsx`

规则：
- 先统计原始链接数，再按唯一链接去重
- 串行抓取，每条间隔 1 秒
- 输出固定字段，不允许删列
- 对正文过短、缺时间、抓取失败等情况标记兜底候选

## Environment

迁移到另一台机器时，至少需要：
- macOS
- Safari
- osascript
- Python 3
- openpyxl

说明：
- 第 2 步依赖 Safari + AppleScript，所以当前版本是 Mac 专用
- 如果目标机器不是 macOS，需要重写多页抓取脚本

## Migration Guidance

迁移时优先复制整个 skill 目录：
- `skills/multi-page-simulated-click-search/`

如果还想兼容现有工作区流程，可以保留桌面脚本；但正式迁移时优先使用本 skill 内的脚本副本，不依赖桌面散落脚本。

## Hard Rules

- 默认走多页流程，不混单页逻辑
- 目标页数是上限，不保证抓满
- 页数不够时，抓到哪里算哪里
- 第 5 步结果为 0 时，返回 `暂未搜索到相关内容`
- 第 6 步先按原文链接去重，再抓详情
- 不要修改用户当前正在使用的原入口脚本，迁移时以复制、打包、并行保留为主
