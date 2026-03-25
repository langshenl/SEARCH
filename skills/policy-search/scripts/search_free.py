#!/usr/bin/env python3
"""
政策搜索免费版 - 组合多种免费方式
注意: 免费搜索受限于反爬机制，建议重要用途使用付费API版
"""
import os
import sys
import json
import time
import random
import re
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict
from urllib.parse import quote, urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "-q"])
    import requests
    from bs4 import BeautifulSoup

# 省份配置
PROVINCES = OrderedDict([
    ("湖北省", "hubei.gov.cn"),
    ("北京市", "beijing.gov.cn"),
    ("广东省", "gd.gov.cn"),
    ("上海市", "shanghai.gov.cn"),
    ("浙江省", "zj.gov.cn"),
])

# 搜索关键词
SEARCH_KEYWORDS = [
    "2026年 政策",
    "2026 通知 公告",
    "2026 规划 方案",
    "2026 工作要点",
    "2026 管理办法",
    "2026 产业发展",
    "2026 科技创新",
    "2026 民生保障",
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)

def search_bing_api(query, domain, num_results=10):
    """Bing搜索"""
    results = []
    try:
        encoded_query = quote(f"site:{domain} {query}")
        url = f"https://cn.bing.com/search?q={encoded_query}"
        
        resp = session.get(url, timeout=10)
        resp.encoding = 'utf-8'
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        for item in soup.select('li.b_algo')[:num_results]:
            link = item.select_one('a[href]')
            if link:
                href = link.get('href', '')
                if domain in href and 'microsoft' not in href:
                    title = link.get_text(strip=True)
                    results.append({
                        'title': title[:100] if title else '政府政策文件',
                        'url': href.split('?')[0],
                        'source': 'bing'
                    })
    except Exception as e:
        pass
    return results

def search_direct_government(query, domain, num_results=10):
    """直接搜索政府网站"""
    results = []
    search_urls = [
        f"https://www.{domain}/search?q={quote(query)}",
        f"https://{domain}/search?q={quote(query)}",
    ]
    
    for search_url in search_urls:
        try:
            resp = session.get(search_url, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for link in soup.find_all('a', href=True)[:num_results]:
                    href = link.get('href', '')
                    if domain in href and '/202' in href:
                        title = link.get_text(strip=True)
                        if title and len(title) > 5:
                            results.append({
                                'title': title[:100],
                                'url': urljoin(resp.url, href).split('?')[0],
                                'source': f'direct_{domain}'
                            })
                break
        except:
            continue
    return results

def fetch_content(url, timeout=10):
    """获取政府网站真实正文"""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            tag.decompose()
        
        article = (
            soup.select_one('article') or
            soup.select_one('div.article') or
            soup.select_one('div.content') or
            soup.select_one('div.main-content') or
            soup.select_one('div#zoom') or
            soup.select_one('div.con')
        )
        
        if article:
            text = article.get_text(separator=' ', strip=True)
        else:
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:4000] if len(text) > 100 else ""
    except:
        return ""

def main():
    keyword = sys.argv[1] if len(sys.argv) > 1 else "2026年 政策"
    
    if len(sys.argv) > 2:
        p_name = sys.argv[2]
        p_domain = PROVINCES.get(p_name, p_name + '.gov.cn')
        target_provinces = OrderedDict([(p_name, p_domain)])
    else:
        target_provinces = OrderedDict(list(PROVINCES.items())[:2])
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║       政策搜索免费版 (无API Key)                           ║
╠════════════════════════════════════════════════════════════╣
║  ⚠️ 注意: 免费搜索受反爬限制，结果可能不完整              ║
║  ✅ 推荐: 使用 search_policy_fast.py (需要Exa API Key)    ║
╠════════════════════════════════════════════════════════════╣
║  关键词: {keyword}
║  省份: {', '.join(target_provinces.keys())}
╚════════════════════════════════════════════════════════════╝
    """)
    
    all_results = []
    
    for province_name, domain in target_provinces.items():
        print(f"\n🔍 搜索 {province_name} ({domain})...")
        seen_urls = {}
        
        for kw in SEARCH_KEYWORDS[:5]:
            print(f"   📌 {kw}...", end=" ", flush=True)
            count = 0
            
            try:
                results = search_bing_api(kw, domain, num_results=8)
                for r in results:
                    if r['url'] not in seen_urls:
                        seen_urls[r['url']] = r
                        count += 1
            except:
                pass
            
            try:
                results = search_direct_government(kw, domain, num_results=5)
                for r in results:
                    if r['url'] not in seen_urls:
                        seen_urls[r['url']] = r
                        count += 1
            except:
                pass
            
            print(f"+{count}", end=" ")
            time.sleep(random.uniform(1, 2))
        
        results_list = list(seen_urls.values())
        for r in results_list:
            r['province'] = province_name
        
        print(f"\n   ✅ {province_name}: {len(results_list)} 条")
        all_results.extend(results_list)
    
    if not all_results:
        print("\n⚠️ 免费搜索被拦截，建议:")
        print("   1. 使用付费API版: python3 search_policy_fast.py")
        print("   2. 手动访问政府网站搜索")
        print("   3. 使用搜索引擎的API服务")
        return
    
    print(f"\n📊 总计: {len(all_results)} 条")
    print("📥 抓取正文...")
    
    fetched = [0]
    for r in all_results:
        content = fetch_content(r['url'])
        if content:
            r['real_text'] = content
            r['real_summary'] = content[:400] + "..."
            r['has_content'] = True
            fetched[0] += 1
        else:
            r['has_content'] = False
    
    valid_results = [r for r in all_results if r.get('has_content')]
    print(f"✅ 有效结果: {len(valid_results)} 条")
    
    output_dir = Path.home() / "Desktop" / "桌面政策文件夹"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    province_str = "_".join(p[:2] for p in target_provinces.keys())
    
    json_file = output_dir / f"政策免费_{province_str}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "搜索时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "方式": "免费版 (Bing+直接搜索)",
            "有效数": len(valid_results),
            "结果": valid_results
        }, f, ensure_ascii=False, indent=2)
    
    xlsx_file = output_dir / f"政策免费_{province_str}_{timestamp}.xlsx"
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["序号", "标题", "正文", "来源", "地址"])
        for i, r in enumerate(valid_results, 1):
            ws.append([i, r.get('title',''), r.get('real_text','')[:500], r.get('province',''), r.get('url','')])
        wb.save(xlsx_file)
        print(f"✅ Excel: {xlsx_file}")
    except:
        pass
    
    print(f"\n📊 结果: {len(valid_results)} 条政策")

if __name__ == "__main__":
    main()