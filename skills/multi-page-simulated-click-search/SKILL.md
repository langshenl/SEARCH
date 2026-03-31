---
name: multi-page-simulated-click-search
description: 多页模拟点击搜索工作流。用于把政策/官方文件搜索需求，按“单结果扩词 → Safari 百度搜索并设置本年时间筛选 → 连续翻页抓取多页 H5 → 合并解析搜索结果 → 原文链接去重后批量直抓详情 → 标记浏览器兜底候选”这条流程执行。适用于需要迁移、复用、打包当前这套最新已验证的多页政策搜索能力时使用。
---

# Multi-Page Simulated Click Search

## Overview

这是当前**最新已验证**的多页政策搜索流程。

它只保留这条主路径：
- 单结果扩词
- 直接使用唯一最终搜索词
- Safari 百度搜索并设置本年时间筛选
- 连续抓取多页搜索结果页 H5
- 关闭当前搜索页面但保留 Safari 窗口
- 合并处理多页 H5
- 输出搜索结果 Excel + 原文链接 md
- 结果非 0 时自动进入详情抓取
- 原文链接去重后批量直抓详情
- 输出政策详情 Excel
- 标记需要浏览器兜底的条目

## Bundled Scripts

- `scripts/build_single_policy_query.py`
  - 单结果扩词脚本
  - 作用：把自然语言搜索需求清洗成唯一一个最终搜索词

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

### 1. 单结果扩词

运行：
- `scripts/build_single_policy_query.py`

规则：
- 如果明确给了年份，就使用该年份
- 如果没给年份，就默认当前年份
- 清洗口语残片，如“帮我搜索一下”“搜索”“相关内容”等
- 识别省份并匹配对应省级政府域名
- 单省输出：`年份 + 搜索关键词 + site:对应省份域名`
- 全国输出：`年份 + 搜索关键词 + site:gov.cn`
- 只输出一个最终结果对象
- 不返回多候选
- 不执行“默认选第 1 条”
- 不生成 CSV
- 不写桌面 `搜索配置文件夹`

### 2. 多页抓取

运行：
- `scripts/capture_multi_page_baidu.command`

输入参数：
- 第 1 个参数：最终搜索词
- 第 2 个参数：目标页数上限，默认 3

规则：
- 用 Safari 打开百度搜索结果页
- 点击“时间不限”并设置本年时间范围
- 逐页保存 H5 到 `~/Desktop/h5/`
- 自动点击“下一页”继续翻页
- 如果页码不够，就抓到哪里算哪里
- 没有下一页时正常停止，不报错
- 结束时关闭当前搜索页，但保留 Safari 窗口

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
- 如果结果数为 0，返回：`暂未搜索到相关内容`

### 4. 直抓原文详情

运行：
- `scripts/fetch_detail_links.py`

输入：
- `~/Desktop/处理文件夹/原文链接.md`

输出：
- `~/Desktop/detail-h5/` 下的政策详情 Excel

规则：
- 先统计原始链接数，再按唯一链接去重
- 串行抓取，每条间隔 1 秒
- 输出固定字段，不允许删列
- 对正文过短、缺时间、抓取失败等情况标记兜底候选
- 当前脚本会输出 `RAW_LINK_COUNT / UNIQUE_LINK_COUNT / COUNT`

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

## Hard Rules

- 默认走单结果扩词 + 多页搜索主路径
- 不混单页逻辑
- 不返回扩词候选列表
- 页数上限只是上限，不保证抓满
- 页码不够时，抓到哪里算哪里
- 第 5 步结果为 0 时，返回 `暂未搜索到相关内容`
- 第 6 步先按原文链接去重，再抓详情
- 政策 ID 提取需兼容多种政府站 URL 模式
- 当前测试阶段仍可以继续沿用用户已验证的旧入口执行；此 skill 用于完整同步最新已验证流程
