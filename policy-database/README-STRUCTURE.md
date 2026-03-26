# Policy Database Structure

```text
policy-database/
  raw/          # 各搜索技能的原始结果
  normalized/   # 字段统一后的中间层
  curated/      # 去重、分层、清洗后的可用结果
  master/       # 全国汇总层
  logs/         # 运行日志与任务记录
```

## 推荐路径规范

### 原始层
`policy-database/raw/{year}/{province}/{skill-name}/`

示例：
- `policy-database/raw/2026/广东/jinzhen-policy-search/`
- `policy-database/raw/2026/广西/cn-policy-multi-search/`
- `policy-database/raw/2026/湖北/exa-web-search-free/`

### 标准化层
`policy-database/normalized/{year}/{province}/`

### 清洗层
`policy-database/curated/{year}/{province}/`

### 汇总层
`policy-database/master/`

## 标准字段建议

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
