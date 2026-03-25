#!/usr/bin/env python3
"""
国家政策搜索方案
搜索各省份政府网站政策内容
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 省份配置
PROVINCES = [
    ("北京市", "https://www.beijing.gov.cn"),
    ("天津市", "https://www.tj.gov.cn"),
    ("河北省", "https://www.hebei.gov.cn"),
    ("山西省", "https://www.shanxi.gov.cn"),
    ("内蒙古", "https://www.nmg.gov.cn"),
    ("辽宁省", "https://www.ln.gov.cn"),
    ("吉林省", "https://www.jl.gov.cn"),
    ("黑龙江省", "https://www.hlj.gov.cn"),
    ("上海市", "https://www.shanghai.gov.cn"),
    ("江苏省", "https://www.jiangsu.gov.cn"),
    ("浙江省", "https://www.zj.gov.cn"),
    ("安徽省", "https://www.ah.gov.cn"),
    ("福建省", "https://www.fujian.gov.cn"),
    ("江西省", "https://www.jiangxi.gov.cn"),
    ("山东省", "http://www.shandong.gov.cn"),
    ("河南省", "https://www.henan.gov.cn"),
    ("湖北省", "https://www.hubei.gov.cn"),
    ("湖南省", "https://www.hunan.gov.cn"),
    ("广东省", "https://www.gd.gov.cn"),
    ("广西", "http://www.gxzf.gov.cn"),
    ("海南省", "https://www.hainan.gov.cn"),
    ("重庆市", "https://www.cq.gov.cn"),
    ("四川省", "https://www.sc.gov.cn"),
    ("贵州省", "https://www.guizhou.gov.cn"),
    ("云南省", "https://www.yn.gov.cn"),
    ("西藏", "https://www.xizang.gov.cn"),
    ("陕西省", "https://www.shaanxi.gov.cn"),
    ("甘肃省", "https://www.gansu.gov.cn"),
    ("青海省", "http://www.qinghai.gov.cn"),
    ("宁夏", "https://www.nx.gov.cn"),
    ("新疆", "https://www.xinjiang.gov.cn"),
]

DESKTOP = Path.home() / "Desktop"
OUTPUT_FOLDER = DESKTOP / "桌面政策文件夹"

def get_exa_key():
    """获取 EXA API Key"""
    # 从 TOOLS.md 读取
    tools_file = Path.home() / ".openclaw" / "workspace-search" / "TOOLS.md"
    if tools_file.exists():
        content = tools_file.read_text()
        for line in content.split('\n'):
            if 'EXA_API_KEY' in line:
                return line.split(':')[-1].strip()
    return os.environ.get("EXA_API_KEY", "")

def search_with_exa(query, site, num_results=10):
    """使用 Exa API 搜索"""
    api_key = get_exa_key()
    if not api_key:
        return None, "EXA_API_KEY 未设置"
    
    full_query = f'site:{site} {query}'
    
    payload = {
        "query": full_query,
        "type": "auto",
        "numResults": num_results,
        "text": True,
        "highlights": True,
        "summary": True
    }
    
    cmd = [
        "curl", "-s", "-X", "POST",
        "https://api.exa.ai/search",
        "-H", f"x-api-key: {api_key}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout), None
        return None, result.stderr or "请求失败"
    except Exception as e:
        return None, str(e)

def format_result(item, province):
    """格式化单条结果"""
    return {
        "标题": item.get("title", "无标题"),
        "正文": item.get("text", "")[:2000] + "..." if len(item.get("text", "")) > 2000 else item.get("text", ""),
        "摘要": item.get("summary", ""),
        "来源地方": province,
        "原文地址": item.get("url", "")
    }

def search_policy(keyword, num_per_province=5):
    """搜索政策内容"""
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keyword_safe = keyword.replace(" ", "_")
    
    print(f"🔍 开始搜索关键词: {keyword}")
    print(f"📁 输出文件夹: {OUTPUT_FOLDER}")
    print("-" * 50)
    
    for province, site in PROVINCES:
        print(f"📍 搜索 {province} ...", end=" ", flush=True)
        
        data, error = search_with_exa(keyword, site, num_per_province)
        
        if error:
            print(f"❌ {error}")
            continue
        
        results = data.get("results", []) if data else []
        
        if results:
            formatted = [format_result(r, province) for r in results]
            all_results.extend(formatted)
            print(f"✅ 获取 {len(formatted)} 条")
        else:
            print("⚪ 无结果")
    
    print("-" * 50)
    print(f"📊 共获取 {len(all_results)} 条政策内容")
    
    # 保存 JSON 结果
    json_file = OUTPUT_FOLDER / f"政策搜索结果_{keyword_safe}_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 报告
    md_file = OUTPUT_FOLDER / f"政策搜索报告_{keyword_safe}_{timestamp}.md"
    
    md_content = f"""# 国家政策搜索报告

## 搜索信息
- **关键词**: {keyword}
- **搜索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **涉及省份**: {len(PROVINCES)} 个
- **结果总数**: {len(all_results)} 条

---

"""
    
    for i, item in enumerate(all_results, 1):
        md_content += f"""## {i}. {item['标题']}

**来源地方**: {item['来源地方']}

**原文地址**: {item['原文地址']}

**摘要**:
{item['摘要']}

**正文预览**:
{item['正文'][:500]}{'...' if len(item['正文']) > 500 else ''}

---

"""
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"✅ 结果已保存到:")
    print(f"   - {json_file}")
    print(f"   - {md_file}")
    
    return all_results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python policy_search.py <搜索关键词> [每省结果数]")
        print("示例: python policy_search.py '科技创新政策' 10")
        sys.exit(1)
    
    keyword = sys.argv[1]
    num = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    search_policy(keyword, num)