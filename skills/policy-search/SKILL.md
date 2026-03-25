---
name: policy-search
description: "Search Chinese government policy documents across 31 provinces. Use for: (1) Searching national/local policies by keyword, (2) Filtering by year such as 2026, (3) Multi-engine search with Exa + Tavily + Baidu, (4) Outputting structured results (title, content, summary, source, URL). Triggers on phrases like search policy, find government documents, policy search, province policy."
---

# Policy Search - 国家政策搜索

## 快速开始

搜索指定年份的全国政策：
```
搜索 2026年 科技创新政策
```

## 核心参数

| 参数 | 示例 | 说明 |
|------|------|------|
| 关键词 | 科技创新政策 | 必填，政策关键词 |
| 年份 | 2026 | 可选，精确筛选 |
| 省份 | 广东省 | 可选，默认全国 |

## 搜索流程

1. **构建搜索语句** → site:域名 年份 关键词
2. **Exa 优先** → 精准语义 + 年份过滤
3. **Tavily 补漏** → 多源聚合去重
4. **百度兜底** → 确保政府网站全覆盖

## 输出格式

每条结果：
- 标题
- 正文（摘要）
- 摘要
- 来源地方（省份）
- 原文地址

## 详细参考

- 省份域名表 → references/provinces.md
- 搜索语法 → references/search-syntax.md
- API配置 → references/api-config.md

## 脚本执行

```bash
bash skills/policy-search/scripts/search.sh "2026年 科技创新政策" 10
```

输出位置：~/Desktop/桌面政策文件夹/