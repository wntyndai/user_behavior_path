# -*- coding: utf-8 -*-
"""desensitize_data.py — 数据层脱敏 report_data.json。

商品名 → 商品A/B/C…；真实商品 ID → G001…；保留数字统计值不变。
"""
import json, io, re

import os
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
M = json.load(open(DIR + r"\report_data.json", encoding="utf-8"))

# 1) 商品：按浏览量降序稳定编号
goods = sorted(M["goods"], key=lambda g: -g["browse"])
letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
alias = {}
for i, g in enumerate(goods):
    gid = str(g["gid"])
    if i < 26:
        alias[gid] = "P%02d" % (i + 1)          # P01..P26
    else:
        alias[gid] = "P%03d" % (i + 1)
    g["gid"] = alias[gid]
    g["name"] = "商品%s" % letters[i % 26] + ("" if i < 26 else str(i + 1))
    g["label"] = g["name"]

json.dump(M, open(DIR + r"\report_data.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

# 别名表（本地留存对照，不进 HTML）
io.open(DIR + r"\_alias_map.json", "w", encoding="utf-8").write(
    json.dumps({"goods": alias}, ensure_ascii=False, indent=1))
print("goods anonymized:", len(alias))
