---
name: exa-policy-search
description: 使用 Exa 搜索并按 v5 政策搜索技能的最终 9 字段格式输出结果。适用于"用 Exa 搜索政策/机构/主题内容""按 v5 格式返回""保存到桌面 exa搜索文件夹""导出 Excel""搜索湖北省…""搜索全国…"这类请求。默认搜索 30 条结果，支持自然语言输入，自动调用 Exa 搜索工具并直接产出 Excel。
---

# Exa Policy Search

## 整体流程概述

```
用户输入（自然语言）
    ↓
第1步：意图识别 → 判断地区 + 是否加域名
    ↓
第2步：构造 Exa 查询词（含域名、年份过滤）
    ↓
第3步：调用 Exa API（POST https://api.exa.ai/search，含 contents 参数）
    ↓
第4步：URL 校验（3秒超时，剔除404）
    ↓
第5步：正文清洗 + 9字段映射
        - 去HTML/导航残留
        - 正文<50字 → 整条过滤
    ↓
第6步：写入 Excel（~/Desktop/exa搜索文件夹/）
    ↓
第7步：输出深度总结（内容概要+主题方向+代表性内容+来源说明）
```

---

## 输入规范

自然语言输入，支持3种模式：

| 输入模式 | 示例 | 地区字段 |
|----------|------|----------|
| 单省搜索 | `湖北省博物馆` / `河北乡村振兴政策` | 用户输入中识别的省份 |
| 全国搜索 | `全国新能源汽车政策` / `碳中和政策` | 全国 |
| 纯主题搜索 | `乡村振兴` | 尝试识别，未识别写"全国" |

- **关键词**：直接使用用户输入内容作为搜索词
- **默认条数**：30条（用户未指定时）

## 各省域名映射

| 省份 | 域名 |
|------|------|
| 北京市 | site:beijing.gov.cn |
| 天津市 | site:tj.gov.cn |
| 河北省 | site:hebei.gov.cn |
| 山西省 | site:shanxi.gov.cn |
| 内蒙古 | site:nmg.gov.cn |
| 辽宁省 | site:ln.gov.cn |
| 吉林省 | site:jl.gov.cn |
| 黑龙江省 | site:hlj.gov.cn |
| 上海市 | site:shanghai.gov.cn |
| 江苏省 | site:jiangsu.gov.cn |
| 浙江省 | site:zj.gov.cn |
| 安徽省 | site:ah.gov.cn |
| 福建省 | site:fujian.gov.cn |
| 江西省 | site:jiangxi.gov.cn |
| 山东省 | site:shandong.gov.cn |
| 河南省 | site:henan.gov.cn |
| 湖北省 | site:hubei.gov.cn |
| 湖南省 | site:hunan.gov.cn |
| 广东省 | site:gd.gov.cn |
| 广西 | site:gxz.gov.cn |
| 海南省 | site:hainan.gov.cn |
| 重庆市 | site:cq.gov.cn |
| 四川省 | site:sc.gov.cn |
| 贵州省 | site:guizhou.gov.cn |
| 云南省 | site:yn.gov.cn |
| 西藏 | site:xizang.gov.cn |
| 陕西省 | site:shaanxi.gov.cn |
| 甘肃省 | site:gansu.gov.cn |
| 青海省 | site:qinghai.gov.cn |
| 宁夏 | site:nx.gov.cn |
| 新疆 | site:xinjiang.gov.cn |
| 全国 | site:gov.cn |

## 工作流程

### 第1步：解析输入 + 意图识别

从自然语言中识别地区和搜索主题，同时判断是否需要限定域名：

**地区识别（优先级：省份 > 城市 > 全国）**：
- 输入含省份名（湖北/河北等）→ 地区=该省份，域名=对应省份域名
- 输入含"全国" → 地区=全国，域名=site:gov.cn
- 输入含城市/县级名称（如武汉/深圳/成都）→ 地区=该城市，域名=所属省份域名（根据城市映射表推断），**搜索词中该城市用引号包裹**实现强制匹配
- 其他情况 → 地区=全国，域名=site:gov.cn

**城市→省份映射（常见城市）**：
武汉→hubei.gov.cn，深圳/广州/珠海→gd.gov.cn，成都/绵阳→sc.gov.cn，南京→jiangsu.gov.cn，杭州→zj.gov.cn，西安→shaanxi.gov.cn，长沙→hunan.gov.cn，郑州→henan.gov.cn，济南→shandong.gov.cn，青岛→shandong.gov.cn，合肥→ah.gov.cn，南昌→jiangxi.gov.cn，昆明→yn.gov.cn，贵阳→guizhou.gov.cn，哈尔滨→hlj.gov.cn，长春→jl.gov.cn，沈阳→ln.gov.cn，石家庄→hebei.gov.cn，太原→shanxi.gov.cn，兰州→gansu.gov.cn，福州→fujian.gov.cn，南宁→gxz.gov.cn，海口→hainan.gov.cn，乌鲁木齐→xinjiang.gov.cn，银川→nx.gov.cn，西宁→qinghai.gov.cn，拉萨→xizang.gov.cn，重庆→cq.gov.cn，北京→beijing.gov.cn，天津→tj.gov.cn，上海→shanghai.gov.cn

**域名意图识别规则（必须严格执行）**：

当识别到以下关键词时，必须追加域名：

1. **显性政策词**（任意出现即触发）：
   政策、通知、意见、方案、公告、规划、条例、规定、细则、指引、办法、标准、项目申报、管理办法、实施意见

2. **能源/产业主题词**（无论是否有省份）：
   新能源、碳中和、补贴、指标、消纳、装机、发电、并网、绿电、电价、储能、氢能、光伏、风电、清洁能源、双碳、能耗、能效、减排、绿色发展

3. **省份/城市 + 任意主题词**

**域名匹配规则**：

| 主题类型 | 追加域名 |
|----------|----------|
| 含显性政策词 | 对应省份域名；全国则 site:gov.cn |
| 含能源/产业主题词（无论是否有省份） | 对应省份域名；全国则 site:gov.cn |
| 省/城市+主题组合 | 对应省份域名 |
| 纯新闻/活动/人物/企业介绍 | 不限定域名 |

**多角度分析类问题（如：从国家安全角度分析…、从…角度分析…）**：
- 识别主语+核心事件（如"武汉市萝卜快跑宕机"）
- 提取主要搜索词后，构造一个综合查询词做一次搜索
- 搜索结果存入 Excel 后做总结
- 不做多轮搜索

### 第2步：构造 Exa 查询词

将域名意图加入 query，**城市名用引号包裹**实现强制匹配：
- 省份+主题：`湖北省新能源 site:hubei.gov.cn`
- 城市+主题：`"武汉市" 新能源 2025 site:hubei.gov.cn`
- 全国：`碳中和政策 site:gov.cn`
- 不需要域名：`岚图汽车公司介绍`

### 第3步：调用 Exa 搜索（POST）

**必须用 POST 方法**，用 curl 发送 JSON 请求：

```bash
curl -s -X POST "https://api.exa.ai/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <EXA_API_KEY>" \
  -d '{
    "query": "<完整搜索词（含域名限定）>",
    "numResults": 30,
    "type": "auto",
    "startPublishedDate": "<起始年-01-01>",
    "endPublishedDate": "<结束年-12-31>",
    "contents": {
      "text": true,
      "summary": true
    }
  }'
```

⚠️ **必须加 `contents: {text: true, summary: true}`**，否则 API 只返回 id、title、url、publishedDate，无正文内容。

**API 响应处理**：
- Exa 返回完整 JSON 对象，有效数据在 `results` 字段（数组）
- 需要用 Python 提取：`items = json_data.get('results', [])`

**年份提取规则**：
- 用户输入含年份（如"2025年"）→ 提取该年份，设置 `startPublishedDate` 和 `endPublishedDate`
- 用户输入含年份区间（如"2023到2026年"）→ 设置对应区间
- 用户未指定年份 → 不设置日期过滤参数（返回全部）

**临时文件保存**：
- 将 API 响应保存为临时 JSON 文件，如 `/tmp/exa_results.json`
- 后续步骤传入该文件路径

### 第4步：URL 校验

对每条结果 URL 发起 HEAD 请求（**3秒超时**），剔除 HTTP 404/410 等无效链接。

这一步在 Python 脚本内自动完成。

### 第5步：正文清洗 + 字段映射

将 Exa 返回的每条结果清洗并映射为 9 个字段：

| 字段 | 来源 |
|------|------|
| 标题 | `title`；无则取正文第一句 |
| 正文 | `text`（清洗后）；为空或<50字则整条过滤 |
| 摘要 | 从正文中提取 1~2 句；无则用 `summary` |
| 发文机关 | 从标题+摘要+正文中用正则提取机构名；无则留空 |
| 发布时间 | 从 `publishedDate` 字段或文本中用正则抽取；无则留空 |
| 原始链接 | `url` |
| 关键词 | 用户原始输入 |
| 类型 | 项目申报/发展规划/工作部署/产业扶持/管理规范/建设实施/政策解读/统计报告/资金预算/人才引进/综合管理 |
| 地区 | 第1步识别的地区（省级） |

**正文清洗规则**：
- 去 HTML 标签、script/style、Markdown 图片、fragment
- 去掉导航/菜单/模板词残留
- 去掉离站提示截断后的噪音
- 正文清洗后为空或字数<50字 → 整条结果过滤，不写 Excel

### 第6步：写入 Excel

调用 Python 脚本（**必须传 3 个参数**）：

```bash
python3 <脚本所在目录>/write_exa_results.py <临时json路径> "<关键词>" "<地区>"
```

示例：
```bash
python3 scripts/write_exa_results.py /tmp/exa_results.json "2025年湖北省新能源" "湖北"
```

脚本自动在 `~/Desktop/exa搜索文件夹/` 下创建时间戳目录，生成 `搜索结果.xlsx`（9列）。

**Excel 格式**：
- 列宽：正文/摘要列不窄于30，标题列不窄于25，其他列不窄于15
- 行高：基础行高 20
- 超链接：原始链接列设为可点击 URL

### 第7步：返回用户

先输出深度总结（直接输出文本）：

```
本次检索共获得 N 项结果，

【内容概要】萝卜快跑、回复、趴窝、武汉萝卜快跑…

【主题方向】事件/事故、技术/产品、政策/监管、市场/商业、舆情/争议

【代表性内容】
  代表性摘要内容1...
  代表性摘要内容2...
  代表性摘要内容3...

【来源说明】其中约 X% 来源于权威媒体或政府官网，建议引用前核实链接有效性。
```

然后换行输出 Excel 保存路径。

## 9列字段

标题、正文、摘要、发文机关、发布时间、原始链接、关键词、类型、地区

## 注意

- API 是 **POST** 方法，不是 GET
- `contents: {text: true, summary: true}` 必须加，否则无正文
- 脚本调用必须传 3 个参数：`<json路径> <关键词> <地区>`
- 临时文件建议放 `/tmp/` 下
- URL 验证：剔除 404/无效链接（3秒超时）
- 正文清洗后为空或字数<50字则整条过滤
- 标题为空时 fallback 到正文第一句话
