# -*- coding: utf-8 -*-
"""postprocess.py — HTML 后处理：确认页面 ID 已是脱敏编号。

数据层（report_data.json）的 pid 已统一为 V01…V12，
本脚本原职责是把真实页面 ID 映射为编号；现在数据已预脱敏，
保留为空操作（no-op）以保证流水线兼容，同时做一次断言校验。
"""
import io, re, os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
P = os.path.join(BASE, "营销活动用户行为路径分析_脱敏版.html")
s = io.open(P, encoding="utf-8").read()

# 校验：data 属性中不应再出现纯数字页面 ID
REAL = re.compile(r'(data-(?:pid|s|t|npid))="(\d+)"')
left = REAL.findall(s)
assert not left, f"发现未脱敏页面 ID: {left[:5]}"

io.open(P, "w", encoding="utf-8").write(s)
print("postprocess ok: 页面 ID 均为脱敏编号（V01…V12）")
