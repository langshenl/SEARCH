---
name: policy-search
description: "Search Chinese government policy documents across 31 provinces with real content extraction. Use for: (1) Searching national/local policies by keyword and year, (2) Multi-keyword coverage for comprehensive results, (3) Real government website content extraction, (4) Outputting structured Excel/JSON results. Triggers on phrases like search policy, 搜索政策, province policy search."
---

# Policy Search - 国家政策搜索 v2

## 快速开始

```
搜索 2026年 政策 全国省份
搜索 2026年 科技创新政策 湖北省
```

## 核心功能

- ✅ **多省份覆盖**: 支持31个省份政府网站
- ✅ **多关键词**: 12轮搜索关键词组合
- ✅ **真实正文**: 直接抓取政府网站原始内容
- ✅ **多格式输出**: Excel + JSON + CSV

## 搜索参数

| 参数 | 示例 | 说明 |
|------|------|------|
| 关键词 | 2026年 政策 | 必填 |
| 省份 | 湖北省/北京市/广东省 | 可选，默认前3个 |

## 搜索流程

```
1. 多关键词组合搜索 (12轮/省份)
   - 政策/通知公告/规划方案/工作要点
   - 产业发展/科技创新/民生保障/乡村振兴
   - 绿色发展/数字经济/扩大内需

2. Exa 精准搜索 + 真实正文抓取

3. 并行抓取 (20线程) + 去重

4. 输出 Excel (1行=1条政策)
```

## 输出格式

| 列 | 内容 |
|----|------|
| 序号 | 自动编号 |
| 标题 | 政策完整标题 |
| 正文摘要 | 政府网站真实正文 (前4000字) |
| 摘要 | AI摘要 (前400字) |
| 来源省份 | 湖北省/北京市等 |
| 原文地址 | 政府网站原始链接 |
| 发布时间 | YYYY-MM-DD |

## 脚本执行

### v2 完整版 (推荐)
```bash
cd ~/.openclaw/workspace-search/skills/policy-search/scripts
export EXA_API_KEY="your-key"
python3 search_policy_fast.py "2026年 政策" [省份]
```

参数：
- 第1个: 搜索关键词
- 第2个: 省份 (可选，默认湖北+北京+广东)

### 单省份搜索
```bash
python3 search_policy_fast.py "2026年 政策" "湖北省"
```

### 全国搜索 (全部31省)
```bash
# 修改脚本中的 PROVINCES 变量或传参
```

## 输出位置

```
~/Desktop/桌面政策文件夹/
├── 政策_湖北_北京_广东_2026年_政策_完整版_时间戳.xlsx
└── 政策_湖北_北京_广东_2026年_政策_完整版_时间戳.json
```

## 性能指标

- 3省份 × 12关键词 = 36轮搜索
- 原始结果: ~400条/3省
- 有效结果: ~330条 (82%成功率)
- 耗时: ~3-5分钟

## 详细参考

- 省份域名表 → references/provinces.md
- 搜索语法 → references/search-syntax.md
- API配置 → references/api-config.md