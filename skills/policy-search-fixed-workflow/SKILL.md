---
name: policy-search-fixed-workflow
description: 固定执行中国政策搜索工作流。用于处理“搜索某省政策”“搜索全国某主题政策”“按既定流程搜政策”“先扩词再搜索再去重”等请求。适用于需要： (1) 先按政策扩词规则生成搜索词，(2) 单省按原词+4个扩词共5条执行，(3) 全国按每省原词+2个扩词共3条执行，(4) 直接逐条调用桌面通用搜索脚本，(5) 将原始结果写入桌面搜索数据文件夹，(6) 再用 policy-dedup-curator 做去重清洗并输出最终政策库。
---

# Policy Search Fixed Workflow

## Overview

按固定链路执行政策搜索：

1. 解析自然语言需求
2. 先做扩词，并在对话中直接返回扩词结果
3. 不生成单独的扩词配置表 CSV
4. 逐条调用 `~/Desktop/通用搜索脚本.py`
5. 原始结果统一写入 `~/Desktop/搜索数据文件夹/任务目录/`
6. 再调用 `policy-dedup-curator` 做去重清洗
7. 最终将混合版、官方优先版和清洗日志输出到 `~/Desktop/政策库文件夹/`

## Fixed Workflow

### 1. 识别范围与默认值

先判断：
- 是否是政策搜索
- 是单省还是全国
- 是否有明确主题
- 是否写了年份

默认规则：
- 没写年份 → 默认当前年份
- 没写地区 → 默认湖北省
- 写了“全国” → 全国模式
- 写了具体省份/自治区/直辖市 → 单省模式

### 2. 扩词规则

#### 单省模式

固定采用：
- 原始搜索词 1 条
- 扩词 4 条
- 合计固定 5 条

泛政策示例：
1. 2026年 湖北省 政策 site:www.hubei.gov.cn
2. 2026年 湖北省 发展规划 site:www.hubei.gov.cn
3. 2026年 湖北省 实施意见 site:www.hubei.gov.cn
4. 2026年 湖北省 若干措施 site:www.hubei.gov.cn
5. 2026年 湖北省 管理办法 site:www.hubei.gov.cn

明确主题示例（农业）：
1. 2026年 湖北省 农业政策 site:www.hubei.gov.cn
2. 2026年 湖北省 农业发展规划 site:www.hubei.gov.cn
3. 2026年 湖北省 农业实施意见 site:www.hubei.gov.cn
4. 2026年 湖北省 农业若干措施 site:www.hubei.gov.cn
5. 2026年 湖北省 农业管理办法 site:www.hubei.gov.cn

#### 全国模式

固定采用：
- 每省原始搜索词 1 条
- 每省扩词 2 条
- 每省合计固定 3 条

示例（某省）：
1. 2026年 河北省 博物馆政策 site:www.hebei.gov.cn
2. 2026年 河北省 博物馆发展规划 site:www.hebei.gov.cn
3. 2026年 河北省 博物馆实施意见 site:www.hebei.gov.cn

注意：
- 全国模式必须拆到各省执行，不直接把“全国”当成一个搜索站点
- 只要是政策搜索，搜索词必须带对应省级政府官网域名锚点 `site:{host}`

### 3. 扩词展示规则

必须先把本次扩词结果在对话中返回给用户。

硬规则：
- 只在对话中展示扩词结果
- 不再生成 `~/Desktop/搜索配置文件夹/general-policy-expand-output.csv`
- 不要求用户手动复制或手动执行

### 4. 搜索执行规则

直接逐条调用：
- `~/Desktop/通用搜索脚本.py`

执行原则：
- 单省：按 5 条搜索词逐条执行
- 全国：按各省展开后，每省 3 条逐条执行
- 同一次任务的原始结果统一进入同一个任务目录
- 不再为同一次任务额外创建 01/02/03 编号子目录

### 5. 原始结果目录规则

原始结果根目录固定为：
- `~/Desktop/搜索数据文件夹/`

推荐任务目录格式：
- `~/Desktop/搜索数据文件夹/YYYY-HHMMSS_任务名/`

示例：
- `~/Desktop/搜索数据文件夹/2026-090032_湖北省政策/`

该目录通常包含：
- 每个搜索词对应的 `.json`
- 每个搜索词对应的 `.csv`
- `_run_summary.json`

### 6. 去重清洗规则

搜索完成后，必须调用：
- `~/.openclaw/workspace-search/skills/policy-dedup-curator/scripts/curate_policy_library.py`

硬规则：
- 记录必须同时具备：标题、摘要、原文链接
- 缺任一项直接丢弃
- 以原文链接为唯一去重键
- 默认输出两版：混合版、官方优先版

### 7. 最终输出目录规则

最终结果目录固定为：
- `~/Desktop/政策库文件夹/`

默认输出：
- `xxx_政策库_混合版.xlsx`
- `xxx_政策库_官方优先版.xlsx`
- `xxx_清洗日志.json`

## Key Paths

- 扩词技能：`~/.openclaw/workspace-search/skills/general-policy-expand/`
- 搜索执行脚本：`~/Desktop/通用搜索脚本.py`
- 原始结果目录：`~/Desktop/搜索数据文件夹/`
- 去重清洗脚本：`~/.openclaw/workspace-search/skills/policy-dedup-curator/scripts/curate_policy_library.py`
- 最终结果目录：`~/Desktop/政策库文件夹/`

## Operational Notes

- 政策搜索相关请求，优先按本技能执行，不再临时拼流程。
- 如果用户只说“搜索某省政策”，默认按单省泛政策的 5 条规则执行。
- 如果用户说“搜索全国某主题政策”，默认按全国模式逐省展开，每省 3 条执行。
- 如果流程规则有新变化，优先更新本技能，再让其他记忆文件引用本技能，而不是在多个地方分别维护一套流程。
