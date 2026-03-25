#!/usr/bin/env python3
"""
政策搜索快速版 - 兼顾数量与质量
- Exa 搜索（已知有效）
- 多关键词覆盖
- 真实正文抓取
"""
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "-q"])
    import requests
    from bs4 import BeautifulSoup

# 配置
EXA_API_KEY = os.environ.get("EXA_API_KEY", "25eb2029-8225-48ab-8a74-ca18f3c75987")

# 省份配置
PROVINCES = OrderedDict([
    ("湖北省", "hubei.gov.cn"),
    ("北京市", "beijing.gov.cn"),
    ("广东省", "gd.gov.cn"),
    ("上海市", "shanghai.gov.cn"),
    ("浙江省", "zj.gov.cn"),
])

# 搜索关键词组合
SEARCH_KEYWORDS = [
    "2026年 政策",
    "2026 通知 公告",
    "2026 规划 方案",
    "2026 工作要点",
    "2026 管理办法",
    "2026 产业发展",
    "2026 科技创新",
    "2026 民生保障",
    "2026 乡村振兴",
    "2026 绿色发展",
    "2026 数字经济",
    "2026 扩大内需",
]

def search_exa(query, domain, num_results=20):
    """使用 Exa 搜索"""
    url = "https://api.exa.ai/search"
    payload = {
        "query": f"site:{domain} {query}",
        "type": "auto",
        "numResults": num_results,
        "text": True,
        "highlights": True,
        "summary": True
    }
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("results", [])
    except Exception as e:
        pass
    return []

def fetch_content(url, timeout=10):
    """获取页面真实正文"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.encoding = resp.apparent_encoding
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        article = (
            soup.find('article') or
            soup.find('div', class_=lambda x: x and 'content' in str(x).lower()) or
            soup.find('div', id=lambda x: x and 'content' in str(x).lower()) or
            soup.find('div', class_='main') or
            soup.find('div', class_='text')
        )
        
        if article:
            text = article.get_text(separator=' ', strip=True)
        else:
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        
        text = ' '.join(text.split())
        
        if len(text) < 100:
            return ""
        
        return text[:4000]
    except:
        return ""

def main():
    keyword = sys.argv[1] if len(sys.argv) > 1 else "2026年 政策"
    
    # 搜索省份
    if len(sys.argv) > 2:
        p_name = sys.argv[2]
        p_domain = PROVINCES.get(p_name, p_name + '.gov.cn')
        target_provinces = OrderedDict([(p_name, p_domain)])
    else:
        target_provinces = OrderedDict()
        for i, (p_name, p_domain) in enumerate(PROVINCES.items()):
            if i >= 3:
                break
            target_provinces[p_name] = p_domain
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           政策搜索系统 v2 - 兼顾数量与质量                    ║
╠════════════════════════════════════════════════════════════╣
║  关键词: {keyword}
║  省份: {', '.join(target_provinces.keys())}
║  搜索轮次: {len(SEARCH_KEYWORDS)} 轮/省份
╚════════════════════════════════════════════════════════════╝
    """)
    
    all_results = []
    
    for province_name, domain in target_provinces.items():
        print(f"\n🔍 搜索 {province_name} ({domain})...")
        
        seen_urls = {}
        
        for kw in SEARCH_KEYWORDS:
            results = search_exa(kw, domain, num_results=15)
            for r in results:
                url = r.get('url', '')
                if url and url not in seen_urls:
                    seen_urls[url] = r
            time.sleep(0.2)
        
        results_list = list(seen_urls.values())
        for r in results_list:
            r['province'] = province_name
        
        print(f"   ✅ 获取 {len(results_list)} 条结果")
        all_results.extend(results_list)
    
    print(f"\n📊 总计获取: {len(all_results)} 条原始结果")
    print("📥 抓取真实正文内容...")
    
    # 并行抓取
    urls_to_fetch = [(r['url'], r) for r in all_results]
    fetched = [0]
    failed = [0]
    
    def fetch_with_url(item):
        url, result = item
        content = fetch_content(url)
        if content and len(content) > 50:
            result['real_text'] = content
            result['real_summary'] = content[:400] + "..." if len(content) > 400 else content
            result['has_content'] = True
            fetched[0] += 1
        else:
            result['has_content'] = False
            failed[0] += 1
        return result
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_with_url, item): item for item in urls_to_fetch}
        for i, future in enumerate(as_completed(futures), 1):
            if i % 20 == 0 or i == len(futures):
                print(f"   进度: {i}/{len(all_results)} | 成功: {fetched[0]} | 失败: {failed[0]}", end="\r")
            future.result()
    
    valid_results = [r for r in all_results if r.get('has_content', False)]
    
    print(f"\n\n✅ 完成! 有效结果: {len(valid_results)} 条")
    
    # 保存
    output_dir = Path.home() / "Desktop" / "桌面政策文件夹"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = keyword.replace(" ", "_")[:15]
    province_str = "_".join(p[:2] for p in target_provinces.keys())
    
    # JSON
    json_file = output_dir / f"政策_{province_str}_{safe_keyword}_完整版_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "搜索时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "关键词": keyword,
            "省份": list(target_provinces.keys()),
            "原始总数": len(all_results),
            "有效总数": len(valid_results),
            "结果": valid_results
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON: {json_file}")
    
    # Excel
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "政策搜索结果"
        
        headers = ["序号", "标题", "正文摘要", "摘要", "来源省份", "原文地址", "发布时间"]
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        for idx, r in enumerate(valid_results, 2):
            ws.cell(row=idx, column=1, value=idx-1)
            ws.cell(row=idx, column=2, value=r.get('title', ''))
            ws.cell(row=idx, column=3, value=r.get('real_text', ''))
            ws.cell(row=idx, column=4, value=r.get('real_summary', ''))
            ws.cell(row=idx, column=5, value=r.get('province', ''))
            ws.cell(row=idx, column=6, value=r.get('url', ''))
            ws.cell(row=idx, column=7, value=r.get('publishedDate', '')[:10] if r.get('publishedDate') else '')
            
            for col in range(1, 8):
                ws.cell(row=idx, column=col).alignment = Alignment(vertical="top", wrap_text=True)
        
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 60
        ws.column_dimensions['D'].width = 40
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 55
        ws.column_dimensions['G'].width = 12
        
        xlsx_file = output_dir / f"政策_{province_str}_{safe_keyword}_完整版_{timestamp}.xlsx"
        wb.save(xlsx_file)
        print(f"✅ Excel: {xlsx_file}")
        
    except Exception as e:
        print(f"⚠️ Excel生成失败: {e}")
    
    print(f"\n🎉 搜索完成! 共 {len(valid_results)} 条有效政策")

if __name__ == "__main__":
    main()