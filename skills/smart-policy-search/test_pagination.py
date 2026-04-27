#!/usr/bin/env python3
"""
测试CDP翻页功能
"""
import sys
import os

# 添加scripts目录到路径
script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, script_dir)

from unified_search import cdp_new, cdp_eval, cdp_close, cdp_click_next, cdp_wait_for_content, extract_links
from gov_config import DEPT_CONFIGS, GENERIC_LINK_SELECTORS

def test_pagination(dept_name="教育部", keyword="通知"):
    """测试指定部门的翻页功能"""
    if dept_name not in DEPT_CONFIGS:
        print(f"错误：未知部门 {dept_name}")
        return

    config = DEPT_CONFIGS[dept_name]
    search_url = config["search_url"].format(keyword=keyword)

    print(f"测试部门：{dept_name}")
    print(f"搜索URL：{search_url}")
    print("=" * 60)

    # 打开搜索页
    print("\n[1] 打开搜索页...")
    target_id = cdp_new(search_url)
    if not target_id:
        print("错误：无法打开搜索页")
        return
    print(f"  target_id: {target_id}")

    import time
    time.sleep(6)  # 等待页面加载

    # 提取第一页链接
    print("\n[2] 提取第一页链接...")
    dept_config = {
        "link_selectors": GENERIC_LINK_SELECTORS,
    }
    links1 = extract_links(target_id, dept_config)
    print(f"  第一页：{len(links1)} 条链接")
    for i, link in enumerate(links1[:5], 1):
        print(f"    {i}. {link['text'][:50]}")

    # 点击下一页
    print("\n[3] 点击下一页...")
    clicked = cdp_click_next(target_id)
    print(f"  点击结果：{'成功' if clicked else '失败'}")

    if clicked:
        # 等待内容加载
        print("\n[4] 等待内容加载...")
        loaded = cdp_wait_for_content(target_id)
        print(f"  加载结果：{'成功' if loaded else '失败'}")

        time.sleep(2)

        # 提取第二页链接
        print("\n[5] 提取第二页链接...")
        links2 = extract_links(target_id, dept_config)
        print(f"  第二页：{len(links2)} 条链接")
        for i, link in enumerate(links2[:5], 1):
            print(f"    {i}. {link['text'][:50]}")

        # 比较两页是否不同
        if links1 and links2:
            urls1 = set(l['href'] for l in links1)
            urls2 = set(l['href'] for l in links2)
            overlap = urls1 & urls2
            print(f"\n  两页重叠：{len(overlap)} 条")
            if len(overlap) < len(urls1) and len(overlap) < len(urls2):
                print("  ✓ 翻页成功！两页内容不同")
            else:
                print("  ✗ 翻页可能失败，两页内容相同")

    # 关闭页面
    cdp_close(target_id)
    print("\n测试完成！")

if __name__ == "__main__":
    dept = sys.argv[1] if len(sys.argv) > 1 else "教育部"
    kw = sys.argv[2] if len(sys.argv) > 2 else "通知"
    test_pagination(dept, kw)
