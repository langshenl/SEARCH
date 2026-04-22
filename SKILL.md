---
name: chrome-web-search
description: Chrome浏览器网页搜索工具。基于Chrome CDP协议，抓取任意网站搜索结果第1页，默认5条，输出正文片段供主agent用内置模型生成AI总结，可选生成Word文档。触发词：「搜索」「全文搜索」「抓取第1页」「网页搜索」「Chrome搜索」等。
---

# Chrome网页搜索

对任意网站执行关键词搜索，抓取第1页结果，默认流式输出正文片段（每篇带标题+链接），主agent用内置模型生成AI总结。

## 整体流程

```
Step 1：脚本抓取正文片段
        │
        └→ 输出：标题 + 百度链接 + 正文片段（算法摘要，非LLM）
        │
Step 2：主agent调用内置模型生成AI总结
        │
        └→ 输出格式：标题、时间、链接地址、总结内容
```

## 执行方式

```
python3 general_search.py <搜索URL> <关键词> [输出目录] [链接选择器] [正文选择器] [数量]
```

参数说明：
- `搜索URL`：搜索结果页URL，`{keyword}` 占位符会被替换为关键词
- `关键词`：要搜索的关键词
- `输出目录`（可选）：Word文档输出路径，默认 ~/Desktop
- `链接选择器`（可选）：逗号分隔的多个CSS选择器，会依次尝试并合并结果
- `正文选择器`（可选）：提取文章正文的CSS选择器（多个用 `|` 分隔），默认 `TRS_Editor|bt-article|article-content|content|article|main|body`
- `数量`（可选）：抓取条数，默认5条；设为 `doc` 时生成Word文档

## 示例

```bash
# 百度搜索（默认5条）
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "光谷AI动态"

# 限制10条
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "关键词" "" "" "" 10

# 生成Word文档
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "关键词" ~/Desktop "" "" "doc"
```

## Chrome CDP

- 地址：`http://localhost:3456`（由 OpenClaw web-access 技能管理）
- Chrome 调试端口 `--remote-debugging-port=9222`：脚本自动检测，未启动则自动拉起（macOS `open -a`）
- 5并发tab并行抓取（Phase1创建空白tab → Phase2并发导航 → Phase3等待加载）
- 动态等待页面加载
- 失败自动重试（最多2次）

## 核心原则

- **多选择器合并**：链接选择器支持逗号分隔多选择器，逐个尝试后合并去重
- **禁止全页提取**：避免混入导航/页脚/相关推荐
- **URL去重**：自动去除重复链接
- **摘要去噪**：取正文中间段落，避免导航栏噪音
- **失败重试**：抓取失败自动重试2次，提升整体成功率

## 输出说明

**脚本不调用LLM**，分两步：

**Step 1 — 脚本输出**（流式）：
- 每篇：标题 + 百度链接 + 正文片段（约100字）
- 用于主agent读取全文

**Step 2 — 主agent生成AI总结**（调用内置模型）：
```
格式：标题、时间、链接地址、总结内容
```
