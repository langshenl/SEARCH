---
name: policy-dedup-curator
description: 中国政策去重清洗技能。用于读取 policy-database/raw 或 normalized 中的多技能政策结果，统一字段、按原文地址去重、按标题相似度去重、按来源优先级排序，并输出到 policy-database/curated。适用于把多个政策搜索技能采集到的原始结果整理成可查询、可汇总的数据层时使用。
---

# Policy Dedup Curator

## 目标

把多个技能采集到的原始政策结果，整理成统一、可查询、可汇总的数据层。

## 输入层

优先读取：
- `policy-database/raw/{year}/{province}/`

可选读取：
- `policy-database/normalized/{year}/{province}/`

## 输出层

输出到：
- `policy-database/normalized/{year}/{province}/`
- `policy-database/curated/{year}/{province}/`

## 标准化字段

统一为以下字段：
- title
- content
- summary
- source_name
- source_url
- published_at
- province
- city
- year
- theme
- doc_type
- source_skill
- source_type
- hit_method
- collected_at
- raw_file
- note

## 去重流程

### 1. URL 去重
- 原文地址相同 → 视为同一条
- 优先保留来源更权威、字段更完整的那条

### 2. 标题相似度去重
- 标题高度相似时，判断是否为同一政策
- 原始政策正文优先于转载/解读
- 省政府/厅局优先于媒体/聚合页

### 3. 来源优先级排序
建议顺序：
1. 省政府 / 办公厅 / 政府公报
2. 厅局 / 委办局
3. 地市 / 区县政府
4. 官方平台 / 专题页
5. 官方媒体 / 权威转载
6. 其他来源

### 4. 分类保留
清洗后可至少分为：
- 正式政策
- 官方解读/转载

## 输出建议

每个省份至少输出：
- `normalized_records.xlsx` / `normalized_records.json`
- `curated_records.xlsx` / `curated_records.json`

## 说明

- `raw` 层永远保留，不覆盖
- 清洗规则可以反复演进
- 任何时候都要能从 `raw` 重新计算 `normalized` 和 `curated`
