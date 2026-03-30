#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用独立搜索脚本
- 不依赖 OpenClaw skill API
- 直接请求多个搜索引擎 HTML 页面
- 抽取标题、链接、摘要
- 去重后输出到桌面 JSON / CSV

示例：
  python3 general_search.py "湖北省 博物馆"
  python3 general_search.py "河北省 政策" --engines bing,ddg,baidu --limit 20
  python3 general_search.py "site:gov.cn 人工智能" --output-dir ~/Desktop/通用搜索结果
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Callable, Dict, List, Optional

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)
TIMEOUT = 20
DEFAULT_ENGINES = ["bing", "ddg", "baidu"]
DESKTOP_DEFAULT_DIR = Path.home() / "Desktop" / "通用搜索结果"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str


class SearchError(Exception):
    pass


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="ignore")


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(url: str) -> str:
    url = unescape((url or "").strip())
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    filtered = [(k, v) for k, v in query_pairs if not k.lower().startswith("utm_")]
    query = urllib.parse.urlencode(filtered)
    return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))


def decode_ddg_redirect(url: str) -> str:
    if "duckduckgo.com/l/?" not in url:
        return url
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    return qs.get("uddg", [url])[0]


def search_bing(query: str, max_results: int) -> List[SearchResult]:
    url = "https://cn.bing.com/search?" + urllib.parse.urlencode({"q": query, "ensearch": 0})
    html = fetch_text(url)
    results: List[SearchResult] = []
    pattern = re.compile(
        r'<li class="b_algo"[\s\S]*?<h2><a href="(.*?)"[^>]*>([\s\S]*?)</a></h2>[\s\S]*?(?:<p>([\s\S]*?)</p>)?',
        flags=re.S,
    )
    for href, title_html, snippet_html in pattern.findall(html)[:max_results]:
        title = strip_html(title_html)
        snippet = strip_html(snippet_html or "")
        final_url = normalize_url(href)
        if title and final_url.startswith("http"):
            results.append(SearchResult(title=title, url=final_url, snippet=snippet, engine="bing"))
    return results


def search_ddg(query: str, max_results: int) -> List[SearchResult]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    html = fetch_text(url)
    results: List[SearchResult] = []
    blocks = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)".*?>(.*?)</a>', html, flags=re.S)
    snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html, flags=re.S)
    for i, (href, title_html) in enumerate(blocks[:max_results]):
        title = strip_html(title_html)
        snippet = strip_html(snippets[i]) if i < len(snippets) else ""
        href = decode_ddg_redirect(unescape(href))
        final_url = normalize_url(href)
        if title and final_url.startswith("http"):
            results.append(SearchResult(title=title, url=final_url, snippet=snippet, engine="ddg"))
    return results


def search_baidu(query: str, max_results: int) -> List[SearchResult]:
    url = "https://www.baidu.com/s?" + urllib.parse.urlencode({"wd": query})
    html = fetch_text(url)
    results: List[SearchResult] = []

    block_pattern = re.compile(r'<div class="result[\s\S]*?</div>\s*</div>', flags=re.S)
    link_pattern = re.compile(r'<h3[\s\S]*?<a[^>]*href="(.*?)"[^>]*>([\s\S]*?)</a>', flags=re.S)
    snippet_pattern = re.compile(r'<div class="c-abstract[\s\S]*?">([\s\S]*?)</div>|<span class="content-right_8Zs40">([\s\S]*?)</span>', flags=re.S)

    for block in block_pattern.findall(html):
        m = link_pattern.search(block)
        if not m:
            continue
        href, title_html = m.groups()
        sm = snippet_pattern.search(block)
        snippet_html = ""
        if sm:
            snippet_html = sm.group(1) or sm.group(2) or ""
        title = strip_html(title_html)
        snippet = strip_html(snippet_html)
        final_url = normalize_url(href)
        if title and final_url.startswith("http"):
            results.append(SearchResult(title=title, url=final_url, snippet=snippet, engine="baidu"))
        if len(results) >= max_results:
            break
    return results


ENGINE_MAP: Dict[str, Callable[[str, int], List[SearchResult]]] = {
    "bing": search_bing,
    "ddg": search_ddg,
    "baidu": search_baidu,
}


def dedupe_results(rows: List[SearchResult]) -> List[SearchResult]:
    merged: Dict[str, SearchResult] = {}
    for row in rows:
        key = row.url
        if key not in merged:
            merged[key] = row
            continue
        current = merged[key]
        if len(row.snippet) > len(current.snippet):
            current.snippet = row.snippet
        if row.engine not in current.engine.split(","):
            current.engine = current.engine + "," + row.engine
    return list(merged.values())


def run_search(query: str, engines: List[str], limit: int, pause: float) -> List[SearchResult]:
    collected: List[SearchResult] = []
    for engine in engines:
        fn = ENGINE_MAP.get(engine)
        if not fn:
            print(f"[WARN] 跳过未知搜索引擎: {engine}")
            continue
        try:
            rows = fn(query, limit)
            print(f"[OK] {engine}: {len(rows)} 条")
            collected.extend(rows)
        except Exception as e:
            print(f"[ERR] {engine}: {e}")
        time.sleep(pause)
    return dedupe_results(collected)


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:80] or "search"


def save_json(path: Path, rows: List[SearchResult], query: str, engines: List[str]) -> None:
    payload = {
        "query": query,
        "engines": engines,
        "count": len(rows),
        "generated_at": dt.datetime.now().isoformat(),
        "results": [r.__dict__ for r in rows],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv(path: Path, rows: List[SearchResult]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "snippet", "engine"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r.__dict__)


def main() -> int:
    parser = argparse.ArgumentParser(description="通用独立搜索脚本")
    parser.add_argument("query", help="搜索关键词，例如：河北省 政策")
    parser.add_argument("--engines", default=",".join(DEFAULT_ENGINES), help="使用哪些搜索引擎，逗号分隔：bing,ddg,baidu")
    parser.add_argument("--limit", type=int, default=10, help="每个引擎最多抓多少条，默认 10")
    parser.add_argument("--pause", type=float, default=0.5, help="引擎间暂停秒数，默认 0.5")
    parser.add_argument("--output-dir", default=str(DESKTOP_DEFAULT_DIR), help="输出目录，默认桌面/通用搜索结果")
    args = parser.parse_args()

    engines = [x.strip() for x in args.engines.split(",") if x.strip()]
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔍 查询: {args.query}")
    print(f"🧭 引擎: {', '.join(engines)}")
    results = run_search(args.query, engines, args.limit, args.pause)
    print(f"✅ 去重后结果数: {len(results)}")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = sanitize_filename(args.query)
    json_path = output_dir / f"{base}_{stamp}.json"
    csv_path = output_dir / f"{base}_{stamp}.csv"

    save_json(json_path, results, args.query, engines)
    save_csv(csv_path, results)

    print(f"📄 JSON: {json_path}")
    print(f"📄 CSV:  {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
