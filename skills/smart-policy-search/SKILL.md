---
name: smart-policy-search
description: 智能政策搜索工具。自动识别查询意图，选择最优数据源（CDP官网爬虫或Exa API），输出Excel或终端汇总。触发词含「官网搜索」、省份+政策类关键词、日常疑问词等。日常问题优先CDP爬百度，失败再降级Exa。
---

# 统一政策搜索

## 行为准则（强制）

**AI 总结和回复时：**
- 严格以实际搜索结果为依据，不捏造、不编造、不添油加醋
- 所有引用数据必须来源于实际返回结果，禁止脑补逻辑链条
- 不确定的信息必须明确说明"搜索结果未提供"，不得模糊推断
- 遇到 Exa 无 API Key 或搜索失败时，直接告知用户，不伪造结果

## 核心能力

自动识别查询意图，智能选择最优搜索策略：

| 场景 | 示例 | 数据源 | 降级 | 输出 |
|------|------|--------|------|------|
| 部门官网搜索 | "文旅部官网搜索社会力量" | CDP爬虫（21个部门） | 失败→Exa (site:gov.cn) | Excel |
| **多部门官网搜索** | "文旅部教育部财政部官网搜索社会力量" | CDP爬虫（每个部门单独一个Excel） | 失败→Exa | 多个Excel |
| 部门官网搜索（无URL） | "住建部官网搜索" | Exa API (site:gov.cn) | — | Excel |
| 日常问题 | "头很晕怎么办" | CDP爬百度 | 失败→Exa全网 | 终端汇总 |
| 省份+政策关键词 | "湖北文旅政策" | **Exa** (site:省.gov.cn) | 搜不到就不出 | 每省Excel |
| 省份非政策类 | "湖北科技创新" | **Exa** (site:省.gov.cn) | 搜不到就不出 | 每省Excel |
| 默认/泛搜索 | "碳中和政策" | CDP爬百度 | 失败→Exa全网降级 | 终端汇总 |

## 架构设计

```
用户输入（自然语言）
       ↓
自动路由：
  ├── 含"官网" → 多部门 → CDP多部门爬虫（每个部门一个Excel）
  │           → 单部门 → CDP部门爬虫
  │           → 无URL部门 → Exa (site:gov.cn) 降级
  ├── 日常问题（怎么/如何/是什么/为什么/哪里） → CDP爬百度 → 终端汇总（失败→Exa）
  ├── 省份 + 政策类关键词 → Exa (site:省.gov.cn)（每省一个Excel，搜不到就不出）
  ├── 有省份非政策类 → Exa (site:省.gov.cn)（每省一个Excel，搜不到就不出）
  └── 默认/泛搜索 → CDP百度 → Exa全网降级 → 终端总结
       ↓
输出：Excel文件 或 终端总结
```

## CDP部门爬虫（21个部门）

| 部门 | 简称 |
|------|------|
| 文化和旅游部 | 文旅部、文化部、旅游部 |
| 教育部 | 教育部 |
| 财政部 | 财政部 |
| 国家发展和改革委员会 | 发改委 |
| 公安部 | 公安部 |
| 民政部 | 民政部 |
| 商务部 | 商务部 |
| 人力资源和社会保障部 | 人社部 |
| 自然资源部 | 自然资源部 |
| 生态环境部 | 生态环境部 |
| 交通运输部 | 交通运输部 |
| 农业农村部 | 农业农村部 |
| 国家卫生健康委员会 | 卫健委 |
| 应急管理部 | 应急管理部 |
| 科学技术部 | 科技部 |
| 国家体育总局 | 体育总局 |
| 国家统计局 | 统计局 |
| 国家知识产权局 | 知识产权局 |
| 国家铁路局 | 铁路局 |
| 中国民用航空局 | 民航局 |
| 国务院 | 国务院 |

## 无法使用CDP的部门（自动降级Exa）

以下8个部门官网无法通过CDP爬取，自动降级到 Exa API（site:gov.cn）：

住房和城乡建设部（住建部）、水利部、工业和信息化部（工信部）、司法部、国家市场监督管理总局（市场监管总局）、国家烟草专卖局（烟草局）、国家邮政局（邮政局）、国家中医药管理局（中医药管理局）

## 翻页支持

CDP部门爬虫支持自动翻页，最多翻3页：
- 第1页提取链接 → 自动点击"下一页" → 等待加载 → 提取第2页 → ...
- 达到目标条数、最大页数或无下一页时停止
- 翻页方式：文字匹配（下一页/下页）+ CSS选择器（a.next等）
- 异常保护：程序退出时自动清理所有打开的CDP tab

## 使用方式

```bash
# 自动模式（推荐）
python3 unified_search.py "文旅部官网搜索社会力量"   # 部门官网 → CDP部门爬虫
python3 unified_search.py "文旅部教育部财政部官网搜索社会力量"  # 多部门 → CDP多部门爬虫
python3 unified_search.py "湖北文旅政策"            # 省份政策 → Exa
python3 unified_search.py "湖北湖南文旅政策"        # 多省政策 → Exa循环
python3 unified_search.py "头很晕怎么办"           # 日常问题 → CDP爬百度（汇总输出）

# 强制指定数据源
python3 unified_search.py "碳中和政策" --source exa
python3 unified_search.py "社会力量" --source cdp

# 指定输出目录
python3 unified_search.py "社会力量" --output ~/Desktop

# 指定最大条数（CDP爬虫，默认30，最多翻3页，Exa固定30条）
python3 unified_search.py "通知" --max-results 100
python3 unified_search.py "社会力量" --max-results 30  # 默认值
```

## 输出格式

### CDP / Exa API（政策类） → Excel文件

- 位置：`~/Desktop/smart搜索文件夹/`
- 文件名格式：
  - 单省：`湖北_文旅_20260421_103045.xlsx`
  - 多省：每个省各一个Excel
  - 部门：`文化和旅游部_社会力量_20260421_103045.xlsx`
- 列：标题 | 正文 | 摘要 | 发布时间 | 原始链接 | 关键词 | 类型 | 地区
- 原始链接带超链接

### CDP爬百度（日常问题） → 终端汇总

```
【汇总分析】
--- 来源1 ---
标题: xxx
时间: xxx
摘要: xxx...（百度摘要或正文前300字）
原始链接: https://...

--- 来源2 ---
标题: xxx
时间: xxx
摘要: xxx...
...
```

### Exa API（降级/默认/泛搜索） → 终端直接输出

Exa API 返回结果自带 AI 摘要（summary 字段），直接展示：

```
【总结分析】
针对您的问题「xxx」，搜索到 N 条参考信息：

1. 标题1
2. 标题2
...

【参考】
摘要内容（Exa AI 生成的要点摘要）...
```

## 路由规则

```
1. 含"官网" → 多部门 → CDP多部门爬虫（每个部门一个Excel）
             单部门 → CDP部门爬虫
             无URL部门 → Exa（site:gov.cn）
2. 日常问题（怎么/如何/是什么/为什么/哪里/限行/能不能/可以吗/好不好...） → CDP爬百度 → 终端汇总（失败→Exa降级）
3. 省份 + 政策类关键词 → Exa（site:省.gov.cn，多省循环）
4. 有省份但非政策类 → Exa（site:省.gov.cn）
5. 默认/泛搜索 → CDP爬百度 → 失败→Exa全网 → 终端汇总
```

## 依赖

```bash
pip3 install openpyxl
```

## 环境变量

```bash
export EXA_API_KEY="your-exa-api-key"  # Exa搜索需要（省份搜索、CDP降级）
```

## 服务依赖

CDP爬虫依赖两个服务，启动顺序：先 Chrome，再代理。

### 1. Chrome（远程调试端口）

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --no-first-run --user-data-dir=/tmp/chrome-debug &

# Linux
google-chrome --remote-debugging-port=9222 --no-first-run --user-data-dir=/tmp/chrome-debug &
```

### 2. CDP 代理（端口 3456）

```bash
node ~/.openclaw/workspace-search/skills/web-access/scripts/cdp-proxy.mjs &
```

### 健康检查

```bash
# 检查代理是否正常
curl -s http://localhost:3456/health
# 正常返回: {"status":"ok","connected":true,"sessions":0,"chromePort":9222}

# 检查 Chrome 是否正常
curl -s http://localhost:9222/json/version
```

### 自动恢复

如果代理返回空响应或连接失败：
1. 关闭残留 tab：`curl -s http://localhost:3456/targets` 查看，逐个 `/close`
2. 重启代理：`pkill -f cdp-proxy.mjs && node ~/.openclaw/workspace-search/skills/web-access/scripts/cdp-proxy.mjs &`
3. 如需重启 Chrome：先杀进程再按上述命令重新启动

## 更新记录

### 2026-04-23
- **修复**: `_fetch_articles` 函数中 `targets[batch_start + i] = None` 索引越界 bug
  - 原因：`targets` 是每批次独立创建的局部列表（长度 ≤ CONCURRENCY），但使用了全局偏移量 `batch_start + i` 索引
  - 当最后一批次数量不足5条时，`batch_start + i` 超出 `targets` 列表长度，导致 `IndexError`
  - 修复：改用批次内局部索引 `targets[i]`
- **优化**: 解决50篇正文爬取超时被系统 SIGTERM/SIGKILL 终止的问题
  - `CONCURRENCY`: 5 → 8（减少批次数量，50篇从10批降至7批）
  - `ARTICLE_WAIT`: 2.5s → 1.0s（每批次等待时间减半）
  - `SEARCH_WAIT`: 6s → 4s（搜索页等待优化）
  - `MAX_RETRIES`: 2 → 1（减少失败重试次数）
  - 页面状态等待循环: 10次×1s → 3次×0.5s（最坏从50s降至1.5s/批次）
  - `wait_for_page_load` 超时: 20s → 10s，轮询间隔: 1s → 0.5s
  - 预估优化后总耗时: ~80-100s（原 ~170-230s），基本在90s限制内
- **调整**: CDP爬虫默认最大条数 50 → 30，减少单次任务耗时
- **并行化**: cdp_new 打开tab、页面状态等待、正文提取全部改为 ThreadPoolExecutor 并行执行
- **超时保护**: `cdp_eval` 默认超时 35s → 15s，防止单次CDP调用卡死
- **文档**: 服务依赖章节补充 Chrome 启动、CDP 代理启动、健康检查、自动恢复流程
- **修复**: 关键词提取丢失政策意图词（"湖北文旅政策"→"文旅 政策"而非"文旅"）
  - 政策类意图词（政策/通知/公告/规定/办法/条例）从 noise_words 移至 policy_intent_words
  - 原查询包含则自动保留
- **增强**: `_fetch_articles` 添加失败重试机制（失败URL自动重试1次）
- **调整**: Exa API 超时 60s → 90s
- **修复**: 正文截断改为无表格不截断（上限32000），有表格截8000字
- **增强**: 添加信号处理（SIGTERM/SIGINT）+ atexit，进程被终止前自动清理残留 Chrome tab
- **增强**: 链接提取自动过滤下载链接（.pdf/.doc/.xls/.zip等 + download/attachment路径），避免触发下载卡死
- **优化**: 多部门搜索改为并行执行（ThreadPoolExecutor），避免串行累加超时
- **增强**: 支持表单提交搜索模式（教育部等不支持URL参数的搜索页）
  - 配置项：`search_mode: "form"`, `search_input`, `search_button`
  - 自动输入关键词 → 触发 input 事件 → 点击搜索按钮
- **增强**: 链接提取回退机制（通用选择器无有效结果时，用域名+文本长度过滤提取）
