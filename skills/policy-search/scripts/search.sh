#!/bin/bash
# 国家政策搜索脚本
# 用法: bash search.sh "关键词" [每省结果数] [年份]

QUERY="$1"
NUM_RESULTS="${2:-5}"
YEAR="${3:-}"

# API Key 检查
if [ -z "${EXA_API_KEY:-}" ]; then
    echo "Error: EXA_API_KEY is not set" >&2
    exit 1
fi

if [ -z "$QUERY" ]; then
    echo "Usage: $0 \"关键词\" [每省结果数] [年份]" >&2
    echo "Example: $0 \"科技创新政策\" 10 2026" >&2
    exit 1
fi

# 年份处理
if [ -n "$YEAR" ]; then
    QUERY="$YEAR年 $QUERY"
fi

echo "🔍 搜索: $QUERY"
echo "📊 每省结果: $NUM_RESULTS"
echo ""

# 省份列表
PROVINCES=(
    "北京市|beijing.gov.cn"
    "天津市|tj.gov.cn"
    "河北省|hebei.gov.cn"
    "山西省|shanxi.gov.cn"
    "内蒙古|nmg.gov.cn"
    "辽宁省|ln.gov.cn"
    "吉林省|jl.gov.cn"
    "黑龙江省|hlj.gov.cn"
    "上海市|shanghai.gov.cn"
    "江苏省|jiangsu.gov.cn"
    "浙江省|zj.gov.cn"
    "安徽省|ah.gov.cn"
    "福建省|fujian.gov.cn"
    "江西省|jiangxi.gov.cn"
    "山东省|shandong.gov.cn"
    "河南省|henan.gov.cn"
    "湖北省|hubei.gov.cn"
    "湖南省|hunan.gov.cn"
    "广东省|gd.gov.cn"
    "广西|gxzf.gov.cn"
    "海南省|hainan.gov.cn"
    "重庆市|cq.gov.cn"
    "四川省|sc.gov.cn"
    "贵州省|guizhou.gov.cn"
    "云南省|yn.gov.cn"
    "西藏|xizang.gov.cn"
    "陕西省|shaanxi.gov.cn"
    "甘肃省|gansu.gov.cn"
    "青海省|qinghai.gov.cn"
    "宁夏|nx.gov.cn"
    "新疆|xinjiang.gov.cn"
)

# 创建输出目录
OUTPUT_DIR="$HOME/Desktop/桌面政策文件夹"
mkdir -p "$OUTPUT_DIR"

# 搜索函数
search_province() {
    local province="$1"
    local domain="$2"
    local full_query="site:$domain $QUERY"
    
    local payload=$(jq -n \
        --arg query "$full_query" \
        --argjson numResults "$NUM_RESULTS" \
        '{
            query: $query,
            type: "auto",
            numResults: $numResults,
            text: true,
            highlights: true,
            summary: true
        }')
    
    curl -s -X POST 'https://api.exa.ai/search' \
        -H "x-api-key: $EXA_API_KEY" \
        -H 'Content-Type: application/json' \
        -d "$payload"
}

# 遍历搜索
all_results=()
for entry in "${PROVINCES[@]}"; do
    IFS='|' read -r province domain <<< "$entry"
    echo "📍 $province ($domain)..."
    
    response=$(search_province "$province" "$domain")
    
    if [ -n "$response" ]; then
        count=$(echo "$response" | jq '.results | length' 2>/dev/null || echo "0")
        echo "   ✅ 获取 $count 条"
        
        # 格式化结果
        echo "$response" | jq -c '.results[]' 2>/dev/null | while read -r item; do
            title=$(echo "$item" | jq -r '.title // "无标题"' 2>/dev/null)
            url=$(echo "$item" | jq -r '.url // ""' 2>/dev/null)
            summary=$(echo "$item" | jq -r '.summary // ""' 2>/dev/null)
            text=$(echo "$item" | jq -r '.text // ""' 2>/dev/null | head -c 1000)
            
            # 只输出结果，不保存到文件（流式）
            echo "TITLE:$title"
            echo "URL:$url"
            echo "SUMMARY:$summary"
            echo "TEXT:$text"
            echo "SOURCE:$province"
            echo "---"
        done
    else
        echo "   ⚪ 无结果"
    fi
done

echo ""
echo "✅ 搜索完成"