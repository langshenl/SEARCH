---
name: cn-policy-multi-search
description: 中国政策多引擎搜索技能。整合百度、Bing中国、搜狗微信等多个中文搜索引擎，批量搜索后合并去重，输出结构化结果（标题、正文、摘要、来源、原文链接），并保存为Excel文件到桌面政策文件夹。
---

# 中国政策多引擎搜索

## 核心能力

1. **多引擎批量搜索** — 百度、Bing CN、搜狗微信、头条搜索并发搜索
2. **政府官网限定** — 省份政策优先限定对应省份政府官网
3. **合并去重** — 多源结果去重后输出统一格式
4. **Excel导出** — 结果保存为Excel文件

## 输出格式（搜索结果）

每条结果包含：
- **标题**：文章/政策标题
- **正文**：正文摘要（100-200字）
- **摘要**：短摘要（50字内）
- **来源地方**：来源网站名称（如"湖北省人民政府"）
- **原文地址**：原始页面 URL

## 输出格式（Excel文件）

保存到 `~/Desktop/政策文件夹/` 目录下，文件名格式：
`{省份}_{关键词}_{时间戳}.xlsx`

Excel列结构：
| A | B | C | D | E |
|---|---|---|---|---|
| 标题 | 正文 | 摘要 | 来源地方 | 原文地址 |

## 搜索流程

### 第一步：判断搜索类型

识别搜索词是否包含省份/城市名称：
- ✅ 含省份："湖北政策"、"上海产业政策"
- ✅ 含城市："武汉政策"、"深圳补贴"
- ❌ 不含：不限定政府官网

### 第二步：构建搜索词

**省份政策搜索**（有省份名）：
```
原始：2026年湖北政策
转换：site:hubei.gov.cn 2026年湖北政策
```

**普通搜索**（无省份名）：
```
原始：新能源汽车政策
直接搜索
```

### 第三步：多引擎搜索

按优先级执行：

| 优先级 | 引擎 | 适用场景 |
|--------|------|---------|
| 1 | 政府官网限定搜索 | 省份政策 |
| 2 | 百度 | 综合政策 |
| 3 | Bing CN | 政府/新闻类 |
| 4 | 搜狗微信 | 政策解读、微信文章 |
| 5 | 头条搜索 | 最新资讯 |

### 第四步：合并去重

- URL去重（相同链接只保留一条）
- 按来源权威性排序（gov.cn > 新闻媒体 > 自媒体）
- 按时间排序（最新优先）

### 第五步：输出结构化结果 + Excel

**终端输出**：
```
## 搜索结果（共 X 条）

### 1. [标题](原文链接)
**来源**：xxx | **摘要**：xxx

正文摘要内容...

---
```

**Excel保存**：
- 保存路径：`~/Desktop/政策文件夹/{省份}_{关键词}_{时间戳}.xlsx`
- 示例：`~/Desktop/政策文件夹/湖北_2026年政策_20260326.xlsx`

### 第六步：Excel生成脚本

使用Python生成Excel：

```python
import openpyxl
from datetime import datetime

def save_to_excel(results, province, keyword, output_dir="~/Desktop/政策文件夹"):
    import os
    import pathlib
    
    output_dir = pathlib.Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    province_str = province if province else "全国"
    filename = f"{province_str}_{keyword}_{timestamp}.xlsx"
    filepath = output_dir / filename
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "政策搜索结果"
    
    # 表头
    headers = ["标题", "正文", "摘要", "来源地方", "原文地址"]
    ws.append(headers)
    
    # 数据行
    for item in results:
        ws.append([
            item.get("title", ""),
            item.get("content", ""),
            item.get("summary", ""),
            item.get("source", ""),
            item.get("url", "")
        ])
    
    wb.save(filepath)
    return str(filepath)
```

## 政府官网清单

省份政策搜索时，使用对应政府官网限定：

| 省份 | 域名 |
|------|------|
| 北京 | beijing.gov.cn |
| 上海 | shanghai.gov.cn |
| 湖北 | hubei.gov.cn |
| 广东 | gd.gov.cn |
| ... | （详见 references/search_engines.md）|

## 搜索优化

### 时间限定
```
site:hubei.gov.cn 2026年湖北政策
```

### 政策文件专用
```
site:gov.cn 湖北 政策 filetype:pdf
```

### 示例

**用户输入**：`2026年湖北政策`

**执行流程**：
1. 识别省份：湖北
2. 限定政府官网：`site:hubei.gov.cn 2026年湖北政策`
3. 多引擎搜索
4. 合并去重
5. 终端输出结构化结果
6. 保存Excel到 `~/Desktop/政策文件夹/`

## 注意事项

- 每个引擎最多取前10条
- 政府官网限定用 `site:gov.cn` 或 `site:{省份域名}`
- 合并时 gov.cn 来源优先展示
- Excel生成后返回文件路径给用户
