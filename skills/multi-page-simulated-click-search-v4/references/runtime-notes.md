# Runtime Notes

## Current verified defaults

- 第一步使用单结果扩词脚本：`build_single_policy_query.py`
- 不再生成扩词候选列表
- 不再默认选第 1 条，因为只返回一个最终搜索词
- 默认多页目标页数：3 页
- 页码不够时，抓到哪里算哪里
- 多页搜索结束后，关闭当前搜索页，但保留 Safari 窗口

## Current output paths

- 搜索页 H5 输出：`~/Desktop/h5/`
- 搜索结果输出：`~/Desktop/处理文件夹/`
- 政策详情输出：`~/Desktop/detail-h5/`

## Current verified detail-output behavior

- 第 4 步详情抓取文件名规则：`搜索词_YYYYMMDD_HHMMSS.xlsx`
- Excel 中 `原始链接` 字段写为可点击超链接
- 如果 `附件链接` 有值，也会写为超链接（多链接时当前优先首条）
- 结果表中只保留一个分类字段：`类型`
- `政策类型` 与 `政策用途` 字段不再保留
- `类型` 字段承载“这篇政策是干什么的”的分类语义

## Current known behavior

- 第 3 步统计的是多页合并后的搜索结果数
- 第 4 步会打印：RAW_LINK_COUNT / UNIQUE_LINK_COUNT / COUNT
- 不同政府站的政策 ID URL 规则不同，当前脚本已兼容多种常见 `.shtml` 结尾模式
- 当前在用流程里，`搜索配置文件夹` 不是必要输出目录
- 某些聚合页/栏目页/发布会页可能导致政策ID或正文抽取不稳定，后续可继续收敛标准政策页识别
