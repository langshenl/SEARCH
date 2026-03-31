# Runtime Notes

## Current output paths

- 搜索页 H5 输出：`~/Desktop/h5/`
- 搜索结果输出：`~/Desktop/处理文件夹/`
- 政策详情输出：`~/Desktop/detail-h5/`

## Current defaults

- 默认扩词后选择第 1 条
- 默认目标页数：3 页
- 页码不够时，抓到哪里算哪里
- 多页搜索结束后，关闭当前搜索页，但保留 Safari 窗口

## Current known behavior

- 第 5 步统计的是多页合并后的搜索结果数
- 第 6 步会打印：RAW_LINK_COUNT / UNIQUE_LINK_COUNT / COUNT
- 不同政府站的政策 ID URL 规则不同，当前脚本已兼容多种常见 `.shtml` 结尾模式
