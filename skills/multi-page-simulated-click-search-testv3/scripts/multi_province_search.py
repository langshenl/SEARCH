#!/usr/bin/env python3
"""
多省搜索调度器
1. 运行 build 扩词（支持多省，结果保存到 ~/.search_meta.json）
2. 对每个省依次运行 capture
3. 合并所有省的 H5 到临时目录
4. 运行合并处理
5. 运行详情抓取
"""
import subprocess, sys, json, shutil
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
HOME = Path.home()
BUILD_SCRIPT  = SCRIPT_DIR / 'build_single_policy_query.py'
CAPTURE_SCRIPT = SCRIPT_DIR / 'capture_multi_page_baidu.command'
PROCESS_SCRIPT = SCRIPT_DIR / 'process_search_h5_multi.py'
FETCH_SCRIPT   = SCRIPT_DIR / 'fetch_detail_links.py'
H5_DIR = HOME / 'Desktop' / '搜索文件夹' / 'h5'
META_FILE = HOME / '.search_meta.json'

def run_step(cmd, desc, timeout=300):
    print(f"\n{'='*50}\n[{desc}]")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    out = r.stdout.strip()
    if out: print(out[:500])
    if r.returncode != 0:
        print(f"ERROR: {r.stderr[:200] if r.stderr else 'unknown'}")
        sys.exit(1)
    return out

def main():
    if len(sys.argv) < 2:
        print("用法: multi_province_search.py <自然语言需求>")
        sys.exit(1)

    raw_query = sys.argv[1]
    print(f"多省搜索启动: {raw_query}")

    # ── Step 1: 扩词 ──
    out = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), raw_query],
        capture_output=True, text=True
    )
    raw = out.stdout.strip()
    if not raw:
        print(f"扩词失败: {out.stderr}"); sys.exit(1)

    # 解析多省结果（用正则匹配 JSON 对象，更鲁棒）
    import re
    provinces = []
    for block in re.finditer(r'\{[^{}]*"地区"[^}]*\}', raw):
        try:
            provinces.append(json.loads(block.group()))
        except: pass
    if not provinces:
        # 尝试整体解析（单省）
        try: provinces.append(json.loads(raw))
        except: pass
    if not provinces:
        print(f"解析省份失败"); sys.exit(1)

    print(f"\n共 {len(provinces)} 个省份: {[p['地区'] for p in provinces]}")

    # ── Step 2: 每个省依次抓取 ──
    h5_dirs = []
    for p in provinces:
        # 写 meta（capture 依赖此文件）
        meta = {
            'province': p['地区'],
            'keyword':  p.get('清洗后关键词', ''),
            'year_range': p['年份'],
            'stamp': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        META_FILE.write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
        print(f"\n[Step2] {p['地区']} 开始抓取 | 搜索词: {p['最终搜索词']}")

        r = subprocess.run(
            ['bash', str(CAPTURE_SCRIPT), p['最终搜索词'], '3', p['年份']],
            capture_output=True, text=True, timeout=300
        )
        if r.stdout: print(r.stdout[:300])
        if r.returncode != 0:
            print(f"capture 失败: {r.stderr[:200]}")

        # 找本次产生的 H5 目录
        province_prefix = p['地区']
        candidates = sorted(H5_DIR.glob(f'{province_prefix}+*'), key=lambda x: x.stat().st_mtime, reverse=True)
        if candidates:
            h5_dirs.append(candidates[0])
            print(f"  → H5目录: {candidates[0].name}")
        else:
            print(f"  → 未找到 H5 目录")

    if not h5_dirs:
        print("没有任何 H5 目录，退出"); sys.exit(1)

    # ── Step 3: 合并到临时目录 ──
    merge_dir = H5_DIR / '_MERGE_TEMP'
    if merge_dir.exists():
        shutil.rmtree(merge_dir)
    merge_dir.mkdir(parents=True)

    for d in h5_dirs:
        for f in d.glob('*.md'):
            dst = merge_dir / f.name
            if not dst.exists():
                shutil.copy2(f, dst)
    print(f"\n[Step3] 合并完成，共 {len(list(merge_dir.glob('*.md')))} 个文件")

    # ── Step 4: 合并处理（传入 merge_dir 路径）──
    print(f"\n[Step4] 合并处理...")
    r = subprocess.run(
        [sys.executable, str(PROCESS_SCRIPT), str(merge_dir)],
        capture_output=True, text=True, timeout=120, cwd=str(SCRIPT_DIR)
    )
    if r.stdout: print(r.stdout[:500])
    if r.returncode != 0:
        print(f"process 失败: {r.stderr[:200]}")

    # ── Step 5: 详情抓取 ──
    print(f"\n[Step5] 详情抓取...")
    kw = '+'.join(p['地区'] for p in provinces)
    r = subprocess.run(
        [sys.executable, str(FETCH_SCRIPT), kw],
        capture_output=True, text=True, timeout=600, cwd=str(SCRIPT_DIR)
    )
    if r.stdout: print(r.stdout[:500])

    # 清理
    if merge_dir.exists():
        shutil.rmtree(merge_dir, ignore_errors=True)

    print(f"\n{'='*50}\n全部完成！{len(provinces)} 个省份")

if __name__ == '__main__':
    main()
