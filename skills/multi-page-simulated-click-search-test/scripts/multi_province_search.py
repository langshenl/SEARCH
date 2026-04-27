#!/usr/bin/env python3
"""
多省政策并行搜索调度脚本

用法:
    python3 multi_province_search.py "湖北省,湖南省,广东省" [页数]

示例:
    python3 multi_province_search.py "湖北省,湖南省,广东省" 3
    python3 multi_province_search.py "河北省,山西省,内蒙古" 3
"""
from __future__ import annotations
import subprocess, time, sys, json, glob, re
from pathlib import Path

EXPAND_SCRIPT   = Path(__file__).parent / "build_single_policy_query.py"
PROCESS_SCRIPT  = Path(__file__).parent / "process_search_h5_multi.py"   # 用自己的（已修复并行解析）
H5_DIR          = Path.home() / "Desktop" / "h5"
MAX_PAGES        = 3


def expand_one(province: str, year: str = None) -> dict | None:
    try:
        kw = f"搜索{province}政策" if not year else f"搜索{year}年{province}政策" if year else f"搜索{province}政策"
        r = subprocess.run(
            ["python3", str(EXPAND_SCRIPT), kw],
            capture_output=True, text=True, timeout=10
        )
        return json.loads(r.stdout.strip())
    except Exception as e:
        print(f"  ⚠️ 扩词失败 [{province}]: {e}")
        return None


def run_safari(query: str, pages: int, start_date: str = None, end_date: str = None) -> str:
    """接收完整日期字符串，如 '2023-01-01', '2026-12-31'"""
    """返回本次 Safari 生成的 h5 文件前缀（用于后续识别）"""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    cmd = [
        str(Path.home() / "Desktop" / "百度_Safari_H5抓取_多页.command"),
        query, str(pages), str(year or '')
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = r.stdout.strip()
        print(f"  Safari 完成: {output}")
        return stamp
    except Exception as e:
        print(f"  ⚠️ Safari 执行失败: {e}")
        return stamp


def main():
    if len(sys.argv) < 2:
        print("用法: python3 multi_province_search.py <省份列表> [页数]")
        print("示例: python3 multi_province_search.py \"湖北省,湖南省,广东省\" 3")
        sys.exit(1)

    provinces = [p.strip() for p in sys.argv[1].split(",")]
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_PAGES
    all_stamps = []
    all_h5_count = 0

    print(f"=" * 50)
    print(f"多省并行搜索启动")
    print(f"省份: {provinces}")
    print(f"每省页数: {pages}")
    print(f"=" * 50)

    for i, province in enumerate(provinces, 1):
        print(f"\n[{i}/{len(provinces)}] 处理: {province}")
        from datetime import datetime
        current_year = str(datetime.now().year)
        result = expand_one(province, current_year)
        if not result:
            continue
        query = result.get("最终搜索词", ""); print(f"  DEBUG: query from expand = {query}")
        print(f"  扩词结果: {query}")

        # 从扩词结果获取年份区间
        year_field = result.get('年份', '')
        if '到' in year_field:
            start_year, end_year = year_field.split('到')
        else:
            start_year = end_year = year_field
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        stamp = run_safari(query, pages, start_date, end_date)
        all_stamps.append(stamp)

        # 统计本次生成的文件
        count = len(list(H5_DIR.glob(f"{stamp[:13]}*")))
        all_h5_count += count
        print(f"  当前 H5 总计: {all_h5_count} 个")

    if not all_stamps:
        print("没有任何 H5 文件生成，退出。")
        sys.exit(1)

    # 用最早的 stamp 前缀传给处理脚本（它会找所有同名prefix文件）
    first_prefix = all_stamps[0][:13]
    print(f"\n{'=' * 50}")
    print(f"合并处理 H5 文件")
    print(f"前缀: {first_prefix}")
    print(f"{'=' * 50}")

    # 确认文件数量
    matching = sorted(H5_DIR.glob(f"{first_prefix}*"))
    print(f"待处理文件: {len(matching)} 个")

    cmd = ["python3", str(PROCESS_SCRIPT), first_prefix]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    print(f"\n处理脚本输出:\n{r.stdout}")
    if r.stderr:
        # 只打印关键错误
        lines = [l for l in r.stderr.splitlines() if "Error" in l or "error" in l or "Traceback" in l]
        if lines:
            print(f"错误:\n" + "\n".join(lines[-5:]))

    # 输出汇总
    excel = Path.home() / "Desktop" / "处理文件夹" / "搜索结果.xlsx"
    md    = Path.home() / "Desktop" / "处理文件夹" / "原文链接.md"
    print(f"\n✅ 多省搜索完成！")
    print(f"   省份: {', '.join(provinces)}")
    print(f"   H5 文件: ~/Desktop/h5/")
    print(f"   结果 Excel: {excel}")
    print(f"   原文链接: {md}")


if __name__ == "__main__":
    raise SystemExit(main())
