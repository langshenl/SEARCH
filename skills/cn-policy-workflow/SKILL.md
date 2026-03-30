---
name: cn-policy-workflow
description: 中国政策搜索完整工作流。自动判断是否需要扩展搜索词（省份政策扩展示程），调用exa-web-search-free执行精准搜索，每个扩展词保证至少20条结果，输出结构化Excel到桌面政策文件夹。
---

# 中国政策搜索完整工作流

## 核心流程

```
用户输入搜索词
     ↓
判断是否需要扩展（触发判断）
     ↓
提取年份（用于时间过滤）
     ↓
执行扩展或不扩展
     ↓
调用exa-web-search-free搜索（每个扩展词20条，限定年份）
     ↓
合并去重（保证≥20条）
     ↓
保存Excel到 ~/Desktop/政策文件夹/
```

## 第一步：触发判断

**需要扩展的条件（同时满足）：**
1. 搜索词包含省份/城市名称（如：湖北、上海、北京、武汉、深圳）
2. 搜索词包含"政策"一词
3. 搜索词是宽泛类型（无具体政策类型）

**不需要扩展的示例：**
- "2026湖北新能源汽车政策" → 包含具体政策类型"新能源汽车"，❌ 不扩展
- "2026人工智能政策" → 无省份/城市，❌ 不扩展
- "2026湖北产业政策" → 已有具体类型"产业"，❌ 不扩展

**需要扩展的示例：**
- "2026湖北政策" → 宽泛，✅ 扩展
- "2026年上海政策" → 宽泛，✅ 扩展
- "2026武汉政策" → 宽泛，✅ 扩展

## 第二步：提取年份

从搜索词中提取年份（如"2026年"），用于后续时间过滤：

| 用户输入 | 提取年份 |
|---------|---------|
| 2026年湖北政策 | 2026 |
| 2025年上海政策 | 2025 |

## 第三步：扩展搜索词

调用 cn-policy-search-expand 技能，加载 `references/policy_types.md` 获取扩展词：

**扩展原则：**
- 每个扩展词搜索保证 **20条以上** 结果
- 扩展词数量根据所需结果动态调整（一般10-20个扩展词）
- 如果扩展词不够，补充其他政策类型

**扩展模板：** `{年份}{省份}{政策类型}`

## 第四步：执行搜索（关键优化）

**⚠️ 重要：必须添加时间过滤，只搜索指定年份发布的政策**

### 使用 exa-full 高级搜索（推荐）

首先配置完整版Exa：
```bash
mcporter config add exa-full "https://mcp.exa.ai/mcp?tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,deep_search_exa,crawling_exa,company_research_exa,people_search_exa,deep_researcher_start,deep_researcher_check"
```

**搜索命令（不限定域名，带时间过滤）：**
```bash
mcporter call 'exa-full.web_search_advanced_exa(
  query: "2026年湖北财政政策",
  numResults: 25,
  startPublishedDate: "2026-01-01",
  endPublishedDate: "2026-12-31"
)'
```

**搜索策略：**
- 使用 `web_search_advanced_exa` 替代 `web_search_exa`
- 添加 `startPublishedDate` 和 `endPublishedDate` 限定发布时间范围
- **不限定域名** — 扩大搜索范围

**搜索参数：**
```python
search_config = {
    "query": "{年份}{省份}{政策类型}",
    "numResults": 25,           # 每扩展词25条
    "startPublishedDate": "{年份}-01-01",  # 年初
    "endPublishedDate": "{年份}-12-31",    # 年末
}
```

## 第五步：结果解析

**Exa返回结果字段：**
- `Title`：标题
- `URL`：原文地址
- `PublishedDate`：发布时间
- `Text`：正文内容

```python
def parse_result(raw_result):
    title = raw_result.get("title", "")
    url = raw_result.get("url", "")
    published = raw_result.get("publishedDate", "")
    text = raw_result.get("text", "")

    # 格式化日期
    date = published.split("T")[0] if published and "T" in published else ""
    # 提取摘要（正文前150字）
    summary = text[:150].replace("\n", " ").strip() if text else ""

    return {
        "title": title,
        "url": url,
        "date": date,
        "text": text[:500].replace("\n", " ") if text else "",
        "summary": summary
    }
```

## 第六步：省份过滤（关键）

**⚠️ 搜索时不限定域名，但结果必须根据URL过滤只保留目标省份**

**省份URL标识对照表：**

| 省份 | URL标识 | 示例 |
|------|---------|------|
| 湖北 | hubei.gov.cn, hb, wh, hub | www.hubei.gov.cn |
| 湖南 | hunan.gov.cn, hn, cs | www.hunan.gov.cn |
| 广东 | gd.gov.cn, gz.gov.cn, sz, guangd | www.gd.gov.cn |
| 河北 | hebei.gov.cn, hb, sjz | www.hebei.gov.cn |
| 上海 | shanghai.gov.cn, sh | www.shanghai.gov.cn |
| 北京 | beijing.gov.cn, bj | www.beijing.gov.cn |
| 四川 | sc.gov.cn, sc | www.sc.gov.cn |
| 浙江 | zj.gov.cn, zj | www.zj.gov.cn |
| 江苏 | jiangsu.gov.cn, js | www.jiangsu.gov.cn |

**过滤规则：**
```python
PROVINCE_DOMAINS = {
    "湖北": ["hubei.gov.cn", "hb", ".wh.", "hub"],
    "湖南": ["hunan.gov.cn", ".hn.", ".cs."],
    "广东": ["gd.gov.cn", "gz.gov.cn", ".sz.", "guangd"],
    "河北": ["hebei.gov.cn", ".sjz."],
    "上海": ["shanghai.gov.cn", ".sh."],
    "北京": ["beijing.gov.cn", ".bj."],
}

def filter_by_province(results, target_province):
    domains = PROVINCE_DOMAINS.get(target_province, [])
    filtered = []
    for r in results:
        url = r['url'].lower()
        if any(d in url for d in domains):
            r['source'] = get_source(url)
            filtered.append(r)
    return filtered
```

## 第七步：数据质量保证

**验证流程：**
1. Published字段必填
2. 年份必须匹配指定年份
3. URL中必须包含目标省份标识
4. 过滤无效日期和空结果

## 第八步：合并去重

**去重规则：**
1. **URL去重**：URL完全相同只保留一条
2. **标题去重**：标题相似度>80%去重

**⚠️ 注意**：不去除时间不同但内容相似的结果

## 第八步：输出Excel

**输出路径：** `~/Desktop/政策文件夹/{省份}_{年份}年政策_{时间戳}.xlsx`

**Excel格式：**

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| 标题 | 正文 | 摘要 | 来源地方 | 原文地址 | 发布时间 |

**字段说明：**
- **标题**：政策文件/文章的完整标题
- **正文**：正文摘要（100-300字），包含政策核心内容
- **摘要**：简短摘要（50字内），一句话说明政策要点
- **来源地方**：来源网站名称（如"湖北省人民政府"）
- **原文地址**：原始页面完整URL
- **发布时间**：政策发布日期（如"2026-01-15"）

## 第九步：结果展示

**终端输出：**
```
## 2026年湖北省政策搜索结果（共 X 条）

### 1. [标题](原文链接)
**来源**：xxx | **发布时间**：2026-01-15 | **摘要**：xxx

正文摘要...

---
```

## 时间词转换

| 用户输入 | 转换结果 |
|---------|---------|
| 今年 | 2026年 → 年份=2026 |
| 去年 | 2025年 → 年份=2025 |
| 明年 | 2027年 → 年份=2027 |

## 常见问题

### Q: 为什么搜到2024、2025年的政策？
**A**: 因为没有加时间过滤。请确保使用 `web_search_advanced_exa` 并设置 `startPublishedDate` 和 `endPublishedDate`。

### Q: Published字段为空怎么办？
**A**: 空Published的结果必须丢弃，不计入结果集。

## 注意事项

- **时间过滤是核心**：必须使用 `web_search_advanced_exa` 并设置日期范围
- **Published必填**：每条结果必须有有效的发布时间
- **年份匹配**：发布时间必须在指定年份
- **保存路径**：固定为 `~/Desktop/政策文件夹/`
