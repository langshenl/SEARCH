---
name: chrome-web-search
description: Chrome浏览器网页搜索工具。基于Chrome CDP协议，抓取任意网站搜索结果第1页，生成Word文档或AI摘要。触发词：「搜索」「全文搜索」「抓取第1页」「生成文档」「网页搜索」「Chrome搜索」等。
---

# Chrome网页搜索

对任意网站执行关键词搜索，抓取第1页全部结果，生成含超链接和正文的Word文档，或流式输出AI摘要。

## 使用方式

```
python3 general_search.py <搜索URL> <关键词> [输出目录] [链接选择器] [正文选择器] [analyze]
```

参数说明：
- `搜索URL`：搜索结果页URL，`{keyword}` 占位符会被替换为关键词
- `关键词`：要搜索的关键词
- `输出目录`（可选）：文档输出路径，默认桌面
- `链接选择器`（可选）：提取搜索结果链接的CSS选择器，默认 `.news-list a, .search-result a`
- `正文选择器`（可选）：提取文章正文的CSS选择器（多个用 `|` 分隔），默认 `TRS_Editor|bt-article|article-content|content|article|main|body`
- `analyze`（可选）：设为 `analyze` 时输出流式AI摘要（替代Word文档）

## 示例

```bash
# 搜索百度（Word文档）
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "人工智能"

# 搜索百度（AI摘要）
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "人工智能" ~/Desktop/output "" "" "analyze"

# 自定义选择器
python3 general_search.py "https://example.com/search?q={keyword}" "新闻" ~/Desktop/output ".result a" "article|.content"
```

## 执行脚本

```bash
python3 ~/.openclaw/workspace-search/skills/chrome-search/scripts/general_search.py <搜索URL> <关键词> [输出目录] [链接选择器] [正文选择器] [analyze]
```

## Chrome CDP

- 地址：`http://localhost:3456`
- 每次搜索后关闭搜索页tab，避免资源占用
- 支持并发抓取（10个tab并行）
- 动态等待页面加载

## 核心原则

- **只用页面结构选择器**：通过指定的选择器提取链接和正文
- **禁止全页提取**：避免混入导航/页脚/相关推荐
- **第1页判定**：由选择器自动确定，不数字条数
- **不过滤**：提取到什么都保留
- **URL去重**：自动去除重复链接（含百度跳转链接）
- **摘要去噪**：取正文中间段落，避免导航栏噪音
