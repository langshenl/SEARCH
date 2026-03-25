# API 配置

## 已配置的 Keys

| 服务 | Key | 状态 |
|------|-----|------|
| EXA_API_KEY | 25eb2029-8225-48ab-8a74-ca18f3c75987 | ✅ 已配置 |
| TAVILY_API_KEY | tvly-dev-12K0bN-... | ✅ 已配置 |

## Exa API

- 官网：https://dashboard.exa.ai
- 端点：https://api.exa.ai/search
- 支持 site: 语法
- 支持 after:/before: 时间过滤

```bash
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: $EXA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "site:beijing.gov.cn 2026 政策", "numResults": 10}'
```

## Tavily API

- 官网：https://tavily.com
- 端点：https://api.tavily.com/search
- 多源聚合，自动去重

## 输出目录

```
~/Desktop/桌面政策文件夹/
├── 政策搜索结果_[关键词]_[时间戳].json
└── 政策搜索报告_[关键词]_[时间戳].md
```