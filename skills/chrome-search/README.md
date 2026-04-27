# chrome-search

Chrome 浏览器网页搜索工具。基于 Chrome CDP 协议，对任意网站执行关键词搜索，抓取第1页结果，流式输出正文片段，由主 agent 调用内置模型生成 AI 总结。

## 特性

- **CDP Proxy 内置**：自带 `cdp-proxy.mjs`，无需依赖其他技能
- **自动 Chrome**：检测 Chrome 调试端口，未启动则自动拉起（macOS / Linux）
- **5 并发抓取**：Phase1 并行创建空白 tab → Phase2 并行导航 → Phase3 并行等待加载
- **多选择器**：链接/正文支持逗号分隔多选择器，自动合并去重
- **失败重试**：单篇失败自动重试最多 2 次
- **两步输出**：脚本输出正文片段 → 主 agent 生成 AI 总结

## 安装

```bash
# 复制到 OpenClaw skills 目录
cp -r chrome-search ~/.openclaw/workspace-search/skills/

# 安装依赖（仅 doc 模式需要）
pip install python-docx
```

## 前置依赖

| 依赖 | 说明 |
|------|------|
| Chrome | 脚本自动检测并启动，需开启 `--remote-debugging-port=9222` |
| python-docx | 可选，仅 doc 模式需要 |

## CDP Proxy 启动

```bash
# 直接运行（默认端口 3456）
node ~/.openclaw/workspace-search/skills/chrome-search/scripts/cdp-proxy.mjs

# 指定端口
CDP_PROXY_PORT=3456 node ~/.openclaw/workspace-search/skills/chrome-search/scripts/cdp-proxy.mjs
```

### 启动 Chrome 调试模式

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

## 使用方式

```bash
python3 general_search.py <搜索URL> <关键词> [输出目录] [链接选择器] [正文选择器] [数量|doc]
```

### 示例

```bash
# 百度搜索（默认5条）
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "光谷AI动态"

# 限制10条
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "关键词" "" "" "" 10

# 生成Word文档
python3 general_search.py "https://www.baidu.com/s?wd={keyword}" "关键词" ~/Desktop "" "" "doc"
```

## 输出格式

**脚本输出**（流式）：
```
【1】文章标题
🔗 百度链接
📝 算法摘要（正文中间段落，约100字）
---
正文片段（前1500字）
```

**主 agent AI 总结**（调用内置模型）：
```
【标题】xxx
【时间】2026-04-22
【链接】https://...
【总结】xxx
```

## 工作流程

```
Step 1：脚本抓取
  ├─ 打开搜索页（1个tab）
  ├─ 提取链接 → 去重 → 限取N条
  └─ 5并发抓取正文 → 流式输出

Step 2：主agent生成AI总结
  └─ 调用内置模型，按「标题/时间/链接/总结」格式输出
```

## 文件结构

```
chrome-search/
├── SKILL.md                  # OpenClaw skill 说明
├── README.md                 # 本文件
└── scripts/
    ├── general_search.py     # 主脚本
    └── cdp-proxy.mjs         # CDP Proxy（HTTP API 操控 Chrome）
```
