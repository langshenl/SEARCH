---
name: policy-harvest-orchestrator
description: 中国政策采集编排技能。用于先对“年份 + 省份/城市 + 政策需求”做政策主题扩充，再按“年份 + 省份/城市 + 主题”组织政策数据采集，统一调度 cn-policy-search-expand、jinzhen-policy-search、cn-policy-multi-search、exa-web-search-free 等搜索技能，把各自原始结果分层保存到桌面原始数据文件夹，并记录采集日志。适用于构建省级/全国政策原始数据池时使用。
---

# Policy Harvest Orchestrator

## 目标

先把用户的政策需求扩展成更全面的主题搜索集合，再把多个搜索技能的结果沉淀为可复用的原始数据层，而不是每次临时搜索后丢失上下文。

## 默认输出目录

原始结果统一保存到桌面原始数据文件夹，例如：
`~/Desktop/原始数据/{year}/{province}/{theme}/{skill-name}/`

日志保存到：
`~/Desktop/原始数据/logs/`

## 推荐执行顺序

1. `cn-policy-search-expand`
   - 负责将用户输入扩展为多个具体政策主题搜索词
2. `jinzhen-policy-search`
   - 负责规则化、较干净的正式政策结果
3. `cn-policy-multi-search`
   - 负责多源广搜、官方站群扩展
4. `exa-web-search-free`
   - 负责 AI 搜索补漏、专题页/聚合页发现

## 执行步骤

### 1. 解析输入
至少识别：
- year
- province / city
- policy_need（原始政策需求）
- theme（若用户已明确给出，则可直接使用）

### 2. 先做政策扩充
优先调用 `cn-policy-search-expand`，将原始需求扩展为多个更具体的政策主题搜索词。

例如：
- 用户输入：`2026年湖北政策`
- 可扩展为：财政政策、产业政策、人才政策、科技政策、招商政策、就业政策等

若用户已经给出非常明确的主题，或不需要扩展，可跳过此步骤并直接进入采集。

### 3. 创建目录
按以下结构创建目录：
- `~/Desktop/原始数据/{year}/{province}/{theme}/jinzhen-policy-search/`
- `~/Desktop/原始数据/{year}/{province}/{theme}/cn-policy-multi-search/`
- `~/Desktop/原始数据/{year}/{province}/{theme}/exa-web-search-free/`

若存在多个扩充主题，则每个 theme 单独建目录。

### 4. 按主题逐个技能采集
对每个扩充后的 theme，依次调用各搜索技能：
- 运行对应搜索
- 保留其原始输出文件（Excel/JSON/Markdown/临时结果说明）
- 记录采集时间、技能名、输入参数、输出路径

### 5. 记录采集日志
每次采集至少记录：
- year
- province
- policy_need
- theme
- expanded_from
- skill_name
- collected_at
- output_files
- note

可写入：
- `~/Desktop/原始数据/logs/harvest-history.jsonl`

## 采集原则

- 先扩充、后采集，尽量降低主题漏检
- 原始层不要做强去重
- 原始层允许重复、允许不同技能结果并存
- 必须保留 `source_skill` 信息
- 必须保留原文地址
- 必须保留扩充来源关系（原始需求 → 扩充主题）

## 交付结果

完成后至少告诉用户：
- 原始需求被扩充成了哪些主题
- 哪几个技能跑了
- 原始结果分别落在哪些目录
- 哪些技能成功 / 失败 / 部分成功

## 说明

这个技能负责“政策扩充 + 采集编排”，不负责最终去重清洗。
去重、标准化、筛选交给 `policy-dedup-curator`。
