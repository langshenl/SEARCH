---
name: policy-harvest-orchestrator
description: 中国政策采集编排技能。用于按“年份 + 省份/城市 + 主题”组织政策数据采集，统一调度 jinzhen-policy-search、cn-policy-multi-search、exa-web-search-free 等搜索技能，把各自原始结果分层保存到桌面原始数据文件夹，并记录采集日志。适用于构建省级/全国政策原始数据池时使用。
---

# Policy Harvest Orchestrator

## 目标

把多个搜索技能的结果沉淀为可复用的原始数据层，而不是每次临时搜索后丢失上下文。

## 默认输出目录

原始结果统一保存到桌面原始数据文件夹，例如：
`~/Desktop/原始数据/{year}/{province}/{skill-name}/`

日志保存到：
`~/Desktop/原始数据/logs/`

## 推荐采集顺序

1. `jinzhen-policy-search`
   - 负责规则化、较干净的正式政策结果
2. `cn-policy-multi-search`
   - 负责多源广搜、官方站群扩展
3. `exa-web-search-free`
   - 负责 AI 搜索补漏、专题页/聚合页发现

## 执行步骤

### 1. 解析输入
至少识别：
- year
- province / city
- theme（默认“全部政策”）

### 2. 创建目录
按以下结构创建目录：
- `~/Desktop/原始数据/{year}/{province}/jinzhen-policy-search/`
- `~/Desktop/原始数据/{year}/{province}/cn-policy-multi-search/`
- `~/Desktop/原始数据/{year}/{province}/exa-web-search-free/`

### 3. 逐个技能采集
对每个技能：
- 运行对应搜索
- 保留其原始输出文件（Excel/JSON/Markdown/临时结果说明）
- 记录采集时间、技能名、输入参数、输出路径

### 4. 记录采集日志
每次采集至少记录：
- year
- province
- theme
- skill_name
- collected_at
- output_files
- note

可写入：
- `~/Desktop/原始数据/logs/harvest-history.jsonl`

## 采集原则

- 原始层不要做强去重
- 原始层允许重复、允许不同技能结果并存
- 必须保留 `source_skill` 信息
- 必须保留原文地址

## 交付结果

完成后至少告诉用户：
- 哪几个技能跑了
- 原始结果分别落在哪些目录
- 哪些技能成功 / 失败 / 部分成功

## 说明

这个技能只负责“采集编排”，不负责最终去重清洗。
去重、标准化、筛选交给 `policy-dedup-curator`。
