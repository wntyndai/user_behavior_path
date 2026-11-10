# -*- coding: utf-8 -*-
"""simulate_data.py — 生成与原表统计特征相近的模拟数据。

原则：
- 总量、比例结构保持同一量级（不改变任何结论方向）
- 每个 UV/占比/转化率做小幅随机扰动（±3% 相对扰动），可复现（固定种子）
- 商品浏览/转化按原分布重采样
"""
import json, io, random

import os
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
random.seed(20261110)

M = json.load(open(DIR + r"\report_data.json", encoding="utf-8"))


def jit(x, rel=0.03, lo=0):
    """相对扰动 ±3%，整数取整。"""
    v = x * (1 + random.uniform(-rel, rel))
    return max(lo, int(round(v)) if isinstance(x, int) or float(x).is_integer() else round(v, 4))


def jitf(x, rel=0.03, lo=0.0, digits=4):
    return round(max(lo, x * (1 + random.uniform(-rel, rel))), digits)


# 顶层规模类指标
for k in ("uv_total", "uv_order", "uv_nonorder", "uv_confirm", "uv_pay",
          "user_total", "user_order", "user_nonorder", "start_uv",
          "uv_goods", "goods_confirm_uv", "uv_nogoods", "nogoods_confirm",
          "goods_browse_uv", "goods_order_uv", "goods_n",
          "uv_confirm_in_order", "uv_confirm_in_nonorder",
          "rows_v", "rows_o"):
    if k in M and isinstance(M[k], (int, float)):
        M[k] = jit(int(M[k])) if isinstance(M[k], int) else jitf(M[k])

# 比例类
for k in ("share_order_uv", "share_confirm", "share_pay", "share_pay_in_confirm",
          "goods_confirm_rate", "goods_cvr_overall", "confirm_rate_order",
          "confirm_rate_nonorder", "censor10_all", "censor10_order",
          "goods_step_median", "goods_time_median"):
    if k in M:
        M[k] = jitf(float(M[k]))

# kitagawa 分解
kg = M.get("kitagawa", {})
for k in ("base_nonorder", "target_order", "delta", "struct_a", "struct_b",
          "rate_a", "rate_b", "struct_shapley", "rate_shapley"):
    if k in kg:
        kg[k] = jitf(float(kg[k]))

# 商品
for g in M["goods"]:
    b0 = g["browse"]
    g["browse"] = jit(int(b0))
    g["order"] = jit(int(g["order"]))
    g["cvr"] = round(g["order"] / max(g["browse"], 1), 4)

# 到达率 / 首跳 / 步数 / 时长 / 触达
for a in M.get("arrival", []):
    a["all"] = jitf(a["all"])
    a["order"] = jitf(a["order"])
    a["nonorder"] = jitf(a["nonorder"])

for r in M.get("first_jump", []):
    r["share"] = jitf(r["share"])
    if "confirm" in r:
        r["confirm"] = jitf(r["confirm"])
    if "uv" in r and isinstance(r["uv"], (int, float)) and r["uv"] > 10:
        r["uv"] = jit(int(r["uv"]))

for b in M.get("steps_bucket", []):
    b["share"] = jitf(b["share"])
for b in M.get("dur_bucket", []):
    b["share"] = jitf(b["share"])
    b["confirm"] = jitf(b["confirm"])
for r in M.get("reach", []):
    r["order"] = jitf(r["order"])
    r["nonorder"] = jitf(r["nonorder"])
    r["diff"] = round(r["order"] - r["nonorder"], 4)
    if "uv_total" in r:
        r["uv_total"] = jit(int(r["uv_total"]))

# 日 / 时段
for d in M.get("dates", []):
    d["uv"] = jit(int(d["uv"]))
    d["confirm"] = jitf(d["confirm"])
    d["rate"] = jitf(d["rate"])
for h in M.get("hours", []):
    h["uv"] = jit(int(h["uv"]))
    h["confirm"] = jitf(h["confirm"])
    h["rate"] = jitf(h["rate"])

# 桑基图（节点 share/uv 与边 n 同步扰动，保持总量近似一致）
for key in ("sankey_all", "sankey_nonorder", "sankey_order"):
    sk = M.get(key)
    if not sk:
        continue
    for nd in sk["nodes"]:
        nd["total"] = jit(int(nd["total"]))
        for it in nd["items"]:
            it["share"] = jitf(it["share"])
            it["uv"] = jit(int(it["uv"]))
    for lst in sk["edges"]:
        for e in lst:
            e["n"] = jit(int(e["n"]))

# 雷达 / 其他列表
for a in M.get("radar", []):
    for k in ("order", "nonorder"):
        if k in a:
            a[k] = jitf(a[k])

json.dump(M, open(DIR + r"\report_data.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
print("simulated. sample goods[0]:", M["goods"][0]["browse"], M["goods"][0]["order"])
print("uv_total:", M["uv_total"], "share_confirm:", M["share_confirm"])
