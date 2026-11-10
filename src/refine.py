# -*- coding: utf-8 -*-
"""refine.py — 重新生成后需要再次执行的日期与文案清理。

数据层的 pid 已在 data/report_data.json 中脱敏为 V01…，
本脚本只负责：日期 → D01…、品牌词兜底清理、字典脚注精简。
"""
import io, os, re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
P = os.path.join(BASE, "营销活动用户行为路径分析_脱敏版.html")
s = io.open(P, encoding="utf-8").read()

# 日期 → 序号（逐日图 data-tip 等）
dates = sorted(set(re.findall(r'20\d{2}-\d{2}-\d{2}', s)))
for i, d in enumerate(dates):
    s = s.replace(d, "D%02d" % (i + 1))
s = s.replace("9/26", "D12").replace("10/25", "D41").replace("10/11", "D27")
s = s.replace("9–10 月", "观察期内")

# 品牌词兜底（正常情况下数据层已清理，这里是双保险）
s = s.replace("大转盘活动页", "活动页").replace("大转盘", "营销活动")

# 页面字典脚注精简
s = s.replace(
    "早期报告曾把 29564 写作“我的订单详情”、21066 写作“抽奖结果页”、21065 写作“商品列表页”，与源表不一致，本报告全部改回源表名称。其余长尾页面合并为“其他页面”。",
    "长尾页面已合并为“其他页面”。")

io.open(P, "w", encoding="utf-8").write(s)
print("done | dates left:", len(re.findall(r'20\d{2}-', s)),
      "| brand words left:", s.count("大转盘"))
