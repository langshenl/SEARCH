#!/bin/bash
# 政策搜索完整版 - 支持获取真实正文内容
# 使用方法: bash search_full.sh "关键词" "省份关键词" [每轮结果数]

set -e

QUERY="$1"
PROVINCE_KEY="$2"
NUM_RESULTS="${3:-20}"

# API Keys
EXA_API_KEY="${EXA_API_KEY:-25eb2029-8225-48ab-8a74-ca18f3c75987}"
TAVILY_API_KEY="${TAVILY_API_KEY:-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}"

# 输出目录
OUTPUT_DIR="$HOME/Desktop/桌面政策文件夹"
mkdir -p "$OUTPUT_DIR"

echo "🔍 开始搜索: $QUERY"
echo "📊 每轮结果: $NUM_RESULTS"
echo ""

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python3"
    exit 1
fi

# 搜索函数 - 使用 Exa
search_exa() {
    local keyword="$1"
    local domain="$2"
    
    curl -s -X POST 'https://api.exa.ai/search' \
        -H "x-api-key: $EXA_API_KEY" \
        -H 'Content-Type: application/json' \
        -d "$(jq -n \
            --arg query "site:$domain $keyword" \
            --argjson numResults "$NUM_RESULTS" \
            '{
                query: $query,
                type: "auto",
                numResults: $numResults,
                text: true,
                highlights: true,
                summary: true
            }')"
}

# Tavily 搜索
search_tavily() {
    local keyword="$1"
    
    curl -s -X POST 'https://api.tavily.com/search' \
        -H 'Content-Type: application/json' \
        -d "$(jq -n \
            --arg query "$keyword" \
            --argjson maxResults "$NUM_RESULTS" \
            --arg apiKey "$TAVILY_API_KEY" \
            '{
                api_key: $apiKey,
                query: $query,
                search_depth: "advanced",
                max_results: $maxResults,
                include_answer: true,
                include_raw_content: true
            }')"
}

# 主搜索流程
echo "📡 第一轮: 综合政策搜索..."
RESULT1=$(search_exa "$QUERY" "$PROVINCE_KEY")
echo "   获取 $(echo $RESULT1 | jq -r '.results | length') 条结果"

echo "📡 第二轮: 产业发展搜索..."
RESULT2=$(search_exa "产业 经济 $QUERY" "$PROVINCE_KEY")
echo "   获取 $(echo $RESULT2 | jq -r '.results | length') 条结果"

echo "📡 第三轮: 民生社会搜索..."
RESULT3=$(search_exa "民生 社会 教育 医疗 $QUERY" "$PROVINCE_KEY")
echo "   获取 $(echo $RESULT3 | jq -r '.results | length') 条结果"

echo "📡 第四轮: 科技创新搜索..."
RESULT4=$(search_exa "科技 创新 数字 $QUERY" "$PROVINCE_KEY")
echo "   获取 $(echo $RESULT4 | jq -r '.results | length') 条结果"

# 合并去重
echo ""
echo "🔄 合并去重..."

# 提取所有URL去重
ALL_URLS=$(echo "$RESULT1 $RESULT2 $RESULT3 $RESULT4" | \
    jq -r '.results[] | select(.url != null) | .url' | \
    sort -u | \
    wc -l)
echo "   去重后: $ALL_URLS 条唯一URL"

# 生成 Python 脚本处理数据
cat > /tmp/process_results.py << 'PYEOF'
import json
import sys
import subprocess
import re
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

# 简单HTML正文提取器
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'head'}
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in self.skip_tags:
            return
            
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_tag = None
            
    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.text.append(text)
                
    def get_text(self):
        return ' '.join(self.text)

def extract_text_from_html(html):
    try:
        parser = TextExtractor()
        parser.feed(html)
        text = parser.get_text()
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text)
        return text[:2000]  # 限制长度
    except:
        return ""

# 读取所有搜索结果
all_data = []
seen_urls = set()

search_results = [
    json.loads(open('/tmp/hubei_s1.json').read() if Path('/tmp/hubei_s1.json').exists() else '{"results":[]}'),
    json.loads(open('/tmp/hubei_s2.json').read() if Path('/tmp/hubei_s2.json').exists() else '{"results":[]}'),
    json.loads(open('/tmp/hubei_s3.json').read() if Path('/tmp/hubei_s3.json').read() else '{"results":[]}'),
    json.loads(open('/tmp/hubei_s4.json').read() if Path('/tmp/hubei_s4.json').read() else '{"results":[]}'),
]

# 实际上我们通过stdin传入
input_data = json.load(sys.stdin)
for item in input_data:
    url = item.get('url', '')
    if url and url not in seen_urls:
        seen_urls.add(url)
        all_data.append(item)

print(f"📊 处理 {len(all_data)} 条结果")

# 输出JSON供后续处理
output = {
    "search_time": datetime.now().isoformat(),
    "query": "湖北 2026 政策",
    "total": len(all_data),
    "results": all_data
}

print(json.dumps(output, ensure_ascii=False))
PYEOF

echo ""
echo "✅ 搜索完成"
echo "📁 结果已准备，请运行 Python 脚本生成 Excel"