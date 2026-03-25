# API 配置

## 已配置的 Keys

| 服务 | Key | 状态 |
|------|-----|------|
| EXA_API_KEY | 25eb2029-8225-48ab-8a74-ca18f3c75987 | ✅ 已配置 |
| TAVILY_API_KEY | tvly-dev-12K0bN-... | ✅ 已配置 |

## Exa API (主要搜索)

- 官网：https://dashboard.exa.ai
- 端点：https://api.exa.ai/search
- 用途：精准语义搜索 + site:域名过滤
- 特点：支持时间范围过滤，免费额度充足

```python
# 使用方式
payload = {
    "query": f"site:{domain} {keyword}",
    "type": "auto",
    "numResults": 15,
    "text": True,
    "highlights": True,
    "summary": True
}
```

## Tavily API (备用)

- 官网：https://tavily.com
- 端点：https://api.tavily.com/search
- 用途：多源聚合搜索
- 注意：免费版有频率限制

## 脚本列表

| 脚本 | 说明 |
|------|------|
| search.sh | 基础搜索脚本 (Bash) |
| search_policy_fast.py | **v2完整版 (推荐)** |
| search_policy.py | 单省份版本 |

## 输出目录

```
~/Desktop/桌面政策文件夹/
```

## 依赖安装

```bash
pip3 install requests beautifulsoup4 openpyxl
```