#!/usr/bin/env python3
"""读取 ~/.search_meta.json 返回省份信息"""
import json, sys
from pathlib import Path

meta_file = Path.home() / ".search_meta.json"
if meta_file.exists():
    try:
        meta = json.loads(meta_file.read_text())
        print(meta.get("province", ""))
    except:
        print("")
else:
    print("")
