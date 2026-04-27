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
python3 general_search.py <搜索URL> <关键词> [输出目录] [链接选择器] [正文选择器] [数量|doc]
```

参数说明：
- `搜索URL`：搜索结果页URL，`{keyword}` 占位符会被替换为关键词
- `关键词`：要搜索的关键词
- `输出目录`（可选）：Word文档输出路径，默认 ~/Desktop
- `链接选择器`（可选）：逗号分隔的多个CSS选择器，会依次尝试并合并结果
- `正文选择器`（可选）：提取文章正文的CSS选择器（多个用 `|` 分隔），默认 `TRS_Editor|bt-article|article-content|content|article|main|body`
- `数量|doc`（可选）：数字=抓取条数（默认5条），`doc`=生成Word文档

## 示例

```bash
# 百度搜索（默认5条）
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "光谷AI动态"

# 百度搜索，指定链接选择器（推荐，显式传参避免位置错位）
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "光谷 今天 重大新闻" ~/Desktop "h3 a" "" 5

# 限制10条
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "关键词" "" "" "" 10

# 生成Word文档
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "关键词" ~/Desktop "h3 a" "" doc
```

## 百度搜索说明

百度页面结构可能随时变化，当前默认选择器已更新为 `h3 a`。如果提取失败，可通过 Chrome 开发者工具手动检查页面 CSS 选择器，调整 link_selectors 参数。

**查找选择器方法**：
1. Chrome 打开百度搜索页
2. 按 F12 打开开发者工具
3. 点击 Elements 面板左上角的箭头图标
4. 点击任意搜索结果标题
5. 查看 `<h3>` 或 `<li class="...">` 等外层元素的 class/id 作为选择器

## CDP 脚本

**cdp-proxy.mjs** — 通过 HTTP API 操控 Chrome 浏览器

### 启动 CDP Proxy

```bash
# 直接运行（端口 3456）
node ~/.openclaw/workspace-search/skills/chrome-search/scripts/cdp-proxy.mjs

# 指定端口
CDP_PROXY_PORT=3456 node ~/.openclaw/workspace-search/skills/chrome-search/scripts/cdp-proxy.mjs
```

### 前提条件

Chrome 必须开启远程调试端口：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

### HTTP API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/targets` | GET | 列出所有页面 tab |
| `/new?url=xxx` | GET | 创建新后台 tab（自动等待加载） |
| `/close?target=xxx` | GET | 关闭 tab |
| `/navigate?target=xxx&url=yyy` | GET | 导航（自动等待加载） |
| `/back?target=xxx` | GET | 后退 |
| `/info?target=xxx` | GET | 页面标题/URL/状态 |
| `/eval?target=xxx` | POST | 执行 JS 表达式 |
| `/click?target=xxx` | POST | 点击元素（POST body 为 CSS 选择器） |
| `/clickAt?target=xxx` | POST | CDP 真实鼠标点击 |
| `/scroll?target=xxx&y=3000` | GET | 滚动页面 |
| `/screenshot?target=xxx&file=/tmp/x.png` | GET | 截图 |

### 示例

```bash
# 健康检查
curl http://localhost:3456/health

# 列出所有 tab
curl http://localhost:3456/targets

# 新建空白 tab
curl "http://localhost:3456/new?url=about:blank"

# 导航到百度
curl "http://localhost:3456/navigate?target=xxx&url=https://www.baidu.com"

# 点击元素
curl -X POST "http://localhost:3456/click?target=xxx" -d "h3 a"

# 执行 JS
curl -X POST "http://localhost:3456/eval?target=xxx" -d "document.title"
```

## 核心原则

- **多选择器合并**：链接选择器支持逗号分隔多选择器，逐个尝试后合并去重
- **禁止全页提取**：避免混入导航/页脚/相关推荐
- **URL去重**：自动去除重复链接
- **摘要有噪**：取正文中间段落，避免导航栏噪音
- **失败重试**：抓取失败自动重试2次，提升整体成功率
- **显式传参**：除搜索URL和关键词外，建议用空字符串 `""` 占位，显式传递后续参数，避免位置错位

## 输出说明

**脚本不调用LLM**，分两步：

**Step 1 — 脚本输出**（流式）：
- 每篇：标题 + 百度链接 + 正文片段（约100字）
- 用于主agent读取全文

**Step 2 — 主agent生成AI总结**（调用内置模型）：
```
格式：标题、时间、链接地址、总结内容
```
