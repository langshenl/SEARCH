# 搜索语法参考

## 年份筛选

### 方法1：搜索词直接包含年份
```
site:beijing.gov.cn 2026年 科技创新政策
site:gd.gov.cn 2026 产业政策
```

### 方法2：时间过滤器

| 搜索引擎 | 语法 | 示例 |
|----------|------|------|
| Exa | `after:2026-01-01` | `after:2026-01-01 site:gov.cn 政策` |
| Baidu | `DATE:2026` | `DATE:2026 site:gov.cn 政策` |
| Bing | `tbs=qdr:y` | 近一年 |

### 方法3：组合年份+关键词
```
# Exa
site:beijing.gov.cn 2026 AND 科技创新政策

# 百度
site:gov.cn 2026年 科技创新政策 filetype:pdf
```

## Exa 搜索（推荐）

```bash
# 基础搜索
site:beijing.gov.cn 科技创新政策

# 限定2026年
site:beijing.gov.cn 2026 AND 科技创新政策

# 时间范围
after:2026-01-01 before:2027-01-01 site:gov.cn 产业政策
```

## Tavily 搜索

```bash
"2026年科技创新政策" + site:gov.cn
```

## 百度搜索

```bash
site:gov.cn 2026年 科技创新政策 inurl:zwgk
site:beijing.gov.cn 2026 产业政策 filetype:pdf
```

## 必应搜索

```bash
site:gov.cn "2026" "政策" tbs=qdr:y
site:gd.gov.cn 2026 科技创新
```

## 多引擎组合策略

```
第一轮：Exa 精准搜索 → 获取高质量语义相关结果
第二轮：Tavily 补漏 → 补充 Exa 遗漏
第三轮：百度兜底 → 确保政府网站旧页面不遗漏
```