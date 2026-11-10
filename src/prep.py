# -*- coding: utf-8 -*-
"""Build all datasets for the dual-population report.

本脚本依赖原始 xlsx 日志与中间 pickle（不入库），仅作口径参考；
公开仓库的数据流为 data/report_data.json -> render.py。
需要重建时，将源日志放在项目根 data/raw/ 下并按需调整路径。
"""
import pandas as pd, numpy as np, json, os, math

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = _ROOT
WORK = os.path.join(BASE, "data", "raw")
V = pd.read_pickle(os.path.join(WORK, "_V.pkl"))
O = pd.read_pickle(os.path.join(WORK, "_O.pkl"))

PAGE = {
 "V01": "活动页", "V02": "新首页", "V03": "商品详情页", "V04": "项目列表",
 "V08": "积分明细", "V09": "我的奖品", "V05": "确认订单", "V06": "支付结果",
 "V07": "订单详情", "V10": "我的页", "V12": "H5", "V11": "优惠券页",
}
def pname(pid):
    return PAGE.get(str(pid), "其他页面")

# category colours
CAT = {
 "V01": ("#218D80", "活动"),
 "V02": ("#8FA9DB", "浏览"), "V03": ("#426CB2", "浏览"), "V04": ("#6B8FD4", "浏览"),
 "V05": ("#B45309", "交易"), "V06": ("#D97706", "交易"), "V07": ("#E0A458", "交易"),
 "V08": ("#7C6BA8", "账户"), "V10": ("#7C6BA8", "账户"),
 "V09": ("#A98BC7", "账户"), "V11": ("#A98BC7", "账户"),
 "V12": ("#9AA6A0", "其他"),
}
def pcolor(pid):
    return CAT.get(str(pid), ("#C9CFC9", "其他"))[0]

def prep(df):
    df = df.copy()
    df["ts"] = pd.to_datetime(df["event_time"])
    # 源表列名脱敏对照：实际为用户唯一标识列（示例脚本以「user_key」泛称）
    uid = df["user_key"].fillna("").astype(str)
    u = df["uid"].fillna("").astype(str)
    df["key"] = np.where(uid.str.len() > 0, uid, "uid:" + u)
    df["uv"] = df["key"] + "|" + df["visit_date"].astype(str)
    df["pid"] = df["page_id"].astype(str)
    df["step"] = pd.to_numeric(df["page_seq"], errors="coerce").astype("Int64")
    df["gid"] = df["product_id"].where(df["product_id"].ne("NULL"))
    df["pname"] = df["pid"].map(pname)
    return df

V = prep(V); O = prep(O)
ouv = set(O["uv"]); vuv = set(V["uv"])
assert ouv <= vuv, "order UV not subset"
V["isorder"] = V["uv"].isin(ouv)

confirm_uv = set(V.loc[V["pid"] == "V05", "uv"])
pay_uv = set(V.loc[V["pid"] == "V06", "uv"])
goods_uv = set(V.loc[V["pid"] == "V03", "uv"])
nonorder = vuv - ouv

M = {}
M["uv_total"] = len(vuv); M["uv_order"] = len(ouv); M["uv_nonorder"] = len(nonorder)
M["uv_confirm"] = len(confirm_uv); M["uv_pay"] = len(pay_uv)
M["user_total"] = int(V["key"].nunique()); M["user_order"] = int(O["key"].nunique())
M["user_nonorder"] = M["user_total"] - M["user_order"]
M["share_order_uv"] = M["uv_order"] / M["uv_total"]
M["share_confirm"] = M["uv_confirm"] / M["uv_total"]
M["share_pay"] = M["uv_pay"] / M["uv_total"]
M["uv_confirm_in_order"] = len(confirm_uv & ouv)
M["uv_confirm_in_nonorder"] = len(confirm_uv & nonorder)
M["confirm_rate_order"] = M["uv_confirm_in_order"] / M["uv_order"]
M["confirm_rate_nonorder"] = M["uv_confirm_in_nonorder"] / M["uv_nonorder"]
M["share_pay_in_confirm"] = len(pay_uv & confirm_uv) / max(1, len(pay_uv))

# ---------- per-UV features ----------
g = V.sort_values(["uv", "step", "ts"]).groupby("uv")
F = pd.DataFrame({
    "steps": g["step"].max().astype(float),
    "t0": g["ts"].min(), "t1": g["ts"].max(),
    "npages": g["pname"].nunique(),
    "goods": g["pid"].apply(lambda s: (s == "V03").any()),
    "lst": g["pid"].apply(lambda s: (s == "V04").any()),
    "confirm": g["pid"].apply(lambda s: (s == "V05").any()),
    "pay": g["pid"].apply(lambda s: (s == "V06").any()),
    "prize": g["pid"].apply(lambda s: (s == "V09").any()),
    "points": g["pid"].apply(lambda s: (s == "V08").any()),
    "date": g["访问日期"].first(),
})
F["dur"] = (F["t1"] - F["t0"]).dt.total_seconds() / 60
F["isorder"] = F.index.isin(ouv)

def corr_confirm(series_bool, mask=None):
    s = series_bool if mask is None else series_bool[mask]
    return float(s.mean()) if len(s) else 0.0

# ---------- arrival curve ----------
arr = []
for k in range(1, 11):
    arr.append({"step": k,
                "all": float((F["steps"] >= k).mean()),
                "order": float((F["steps"][F["isorder"]] >= k).mean()),
                "nonorder": float((F["steps"][~F["isorder"]] >= k).mean())})
M["arrival"] = arr

# ---------- step buckets ----------
sb = []
for k in range(1, 11):
    m = F["steps"] == k
    sb.append({"label": "≥10" if k == 10 else str(k), "uv": int(m.sum()),
               "share": float(m.mean()), "confirm": float(F.loc[m, "confirm"].mean()),
               "order_rate": float(F.loc[m, "isorder"].mean())})
M["steps_bucket"] = sb

# ---------- duration buckets ----------
dbins = [(-1, 0.5, "<30秒"), (0.5, 2, "0.5–2分"), (2, 5, "2–5分"), (5, 15, "5–15分"),
         (15, 30, "15–30分"), (30, 60, "30–60分"), (60, 1e9, ">60分")]
dlist = []
for lo, hi, lab in dbins:
    m = (F["dur"] > lo) & (F["dur"] <= hi)
    dlist.append({"label": lab, "uv": int(m.sum()), "share": float(m.mean()),
                  "confirm": float(F.loc[m, "confirm"].mean()),
                  "order_rate": float(F.loc[m, "isorder"].mean())})
M["dur_bucket"] = dlist
M["dur_median_order"] = float(F.loc[F["isorder"], "dur"].median())
M["dur_median_nonorder"] = float(F.loc[~F["isorder"], "dur"].median())
M["steps_mean_order"] = float(F.loc[F["isorder"], "steps"].mean())
M["steps_mean_nonorder"] = float(F.loc[~F["isorder"], "steps"].mean())
M["pages_mean_order"] = float(F.loc[F["isorder"], "npages"].mean())
M["pages_mean_nonorder"] = float(F.loc[~F["isorder"], "npages"].mean())

# ---------- page reach ----------
reach = []
for pid, grp in V.drop_duplicates(["uv", "pid"]).groupby("pid"):
    o = grp.loc[grp["uv"].isin(ouv), "uv"].nunique()
    n = grp.loc[grp["uv"].isin(nonorder), "uv"].nunique()
    if o + n < 30:
        continue
    reach.append({"pid": pid, "name": pname(pid), "order": o / M["uv_order"],
                  "nonorder": n / M["uv_nonorder"], "diff": o / M["uv_order"] - n / M["uv_nonorder"],
                  "uv_total": o + n})
reach.sort(key=lambda r: -r["uv_total"])
M["reach"] = reach

# ---------- first jump ----------
s2 = V[V["step"] == 2].groupby("uv")["pid"].first()
F["s2"] = s2.reindex(F.index).fillna("none")
fj = []
for key, grp in F.groupby("s2"):
    if len(grp) < 20:
        continue
    fj.append({"pid": key, "name": "无第2步" if key == "none" else pname(key),
               "uv": int(len(grp)), "share": float(len(grp) / len(F)),
               "confirm": float(grp["confirm"].mean()),
               "order_rate": float(grp["isorder"].mean())})
fj.sort(key=lambda r: -r["uv"])
M["first_jump"] = fj

# ---------- kitagawa ----------
top = [r["pid"] for r in fj if r["pid"] not in ("none",)][:8] + ["none"]
def cell(pid):
    return pid if pid in top else "other"
F["cell"] = F["s2"].map(cell)
A = F[F["isorder"]]; B = F[~F["isorder"]]
wa = A["cell"].value_counts(normalize=True); wb = B["cell"].value_counts(normalize=True)
ra = A.groupby("cell")["confirm"].mean(); rb = B.groupby("cell")["confirm"].mean()
idx = sorted(set(wa.index) | set(wb.index))
wa = wa.reindex(idx).fillna(0); wb = wb.reindex(idx).fillna(0)
ra = ra.reindex(idx).fillna(0); rb = rb.reindex(idx).fillna(0)
struct_b = float(((wa - wb) * rb).sum())
struct_a = float(((wa - wb) * ra).sum())
rate_a = float((wa * (ra - rb)).sum())
rate_b = float((wb * (ra - rb)).sum())
M["kitagawa"] = {
    "base_nonorder": float(rb.mul(wb).sum()), "target_order": float(ra.mul(wa).sum()),
    "delta": float(ra.mul(wa).sum() - rb.mul(wb).sum()),
    "struct_a": struct_a, "struct_b": struct_b, "rate_a": rate_a, "rate_b": rate_b,
    "struct_shapley": (struct_a + struct_b) / 2, "rate_shapley": (rate_a + rate_b) / 2,
    "cells": [{"name": ("无第2步" if i == "none" else ("其他" if i == "other" else pname(i))),
               "wA": float(wa[i]), "wB": float(wb[i]),
               "rA": float(ra[i]), "rB": float(rb[i])} for i in idx],
}

# ---------- goods ----------
gb = V[V["pid"] == "V03"].groupby("gid")["uv"].nunique()
go = V[V["pid"] == "V05"].groupby("gid")["uv"].nunique()
c = pd.concat([gb.rename("b"), go.rename("o")], axis=1).fillna(0)
c = c[c["b"] >= 30].sort_values("b", ascending=False)
M["goods"] = [{"gid": str(i), "browse": int(r.b), "order": int(r.o),
               "cvr": float(r.o / r.b)} for i, r in c.iterrows()]
M["goods_browse_uv"] = int(c["b"].sum()); M["goods_order_uv"] = int(c["o"].sum())
M["goods_cvr_overall"] = M["goods_order_uv"] / M["goods_browse_uv"]
M["goods_n"] = len(c)


def _load_product_names(path):
    """商品名称.csv -> {main_product_id: main_product_name}; silently empty if missing."""
    if not os.path.exists(path):
        return {}
    raw = open(path, "rb").read()
    text = None
    for enc in ("gb18030", "utf-8-sig"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return {}
    import csv, io
    rows = list(csv.reader(io.StringIO(text)))
    return {r[0].strip(): r[1].strip() for r in rows[1:] if len(r) >= 2 and r[0].strip()}


GOODS_NAMES = _load_product_names(os.path.join(WORK, "商品名称.csv"))
for _g in M["goods"]:
    _g["name"] = GOODS_NAMES.get(_g["gid"], "")

# ---------- date ----------
dd = F.groupby("date").agg(uv=("steps", "size"), confirm=("confirm", "sum"), order=("isorder", "sum"))
M["dates"] = [{"d": str(i), "uv": int(r.uv), "confirm": float(r.confirm),
               "rate": float(r.confirm / r.uv)} for i, r in dd.iterrows()]

# ---------- hour ----------
hh = F.assign(h=F["t0"].dt.hour).groupby("h").agg(uv=("steps", "size"), confirm=("confirm", "sum"), order=("isorder", "sum"))
M["hours"] = [{"h": int(i), "uv": int(r.uv), "confirm": float(r.confirm),
               "rate": float(r.confirm / r.uv)} for i, r in hh.iterrows()]

# ---------- confirm step ordinal / timing ----------
h = V[V["pid"] == "V05"].groupby("uv")["step"].min().dropna()
M["confirm_step_dist"] = {str(int(k)): int(v) for k, v in h.value_counts().sort_index().items()}
M["confirm_step_median"] = float(h.median())
tod = (V[V["pid"] == "V05"].groupby("uv")["ts"].min() - F["t0"]).dt.total_seconds() / 60
M["confirm_time_median"] = float(tod.median())
fg = V[V["pid"] == "V03"].groupby("uv")["step"].min().dropna()
M["goods_step_median"] = float(fg.median())
M["goods_time_median"] = float(((V[V["pid"] == "V03"].groupby("uv")["ts"].min() - F["t0"]).dt.total_seconds() / 60).median())
M["goods_confirm_uv"] = int(len(goods_uv & confirm_uv))
M["goods_confirm_rate"] = M["goods_confirm_uv"] / len(goods_uv)
M["nogoods_uv"] = int(len(vuv - goods_uv))
M["nogoods_confirm"] = int(len((vuv - goods_uv) & confirm_uv))

# ---------- path templates ----------
piv = V.pivot_table(index="uv", columns="step", values="pid", aggfunc="first")
piv = piv.reindex(columns=[1,2,3,4,5,6,7,8,9,10])
def pathstr(row):
    return "→".join([pname(x) for x in row.dropna().tolist()[:5]])
ord_idx = [u for u in piv.index if u in ouv]
pt = piv.loc[ord_idx].apply(pathstr, axis=1).value_counts().head(10)
M["templates"] = [{"path": k, "uv": int(v), "share": float(v / len(ord_idx))} for k, v in pt.items()]

# ---------- sankey ----------
RANK = ["V01", "V02", "V03", "V04", "V08", "V09", "V05", "V06", "V07",
        "V10", "V12", "V11", "OTHER"]
KEEP_PAGES = ("V05", "V06", "V07")
def sankey(uvset, steps=7, topn=6):
    p = piv.loc[piv.index.isin(uvset)].copy()
    mapped = pd.DataFrame(index=p.index)
    for k in range(1, steps + 1):
        col = p[k]
        vc = col.value_counts()
        keep = [x for x in vc.index[:topn]]
        keep += [x for x in KEEP_PAGES if x in vc.index and x not in keep]
        mapped[k] = col.where(col.isin(keep), "OTHER")
        mapped[k] = mapped[k].where(col.notna(), None)
    nodes = []
    for k in range(1, steps + 1):
        vc = mapped[k].value_counts(dropna=True)
        total = int(vc.sum())
        ordered = sorted([(x, int(v)) for x, v in vc.items()],
                         key=lambda t: (RANK.index(t[0]) if t[0] in RANK else 99, -t[1]))
        nodes.append({"step": k, "total": total,
                      "items": [{"pid": x, "name": "其他页面" if x == "OTHER" else pname(x),
                                 "uv": v, "share": v / total,
                                 "color": "#C9CFC9" if x == "OTHER" else pcolor(x)} for x, v in ordered]})
    edges = []
    for k in range(1, steps):
        e = mapped.groupby([k, k + 1]).size().reset_index(name="n")
        e.columns = ["s", "t", "n"]
        edges.append(e)
    return {"steps": steps, "nodes": nodes,
            "edges": [[{"s": str(r.s), "t": str(r.t), "n": int(r.n)} for r in e.itertuples()] for e in edges]}
M["sankey_all"] = sankey(vuv)
M["sankey_nonorder"] = sankey(nonorder)
M["sankey_order"] = sankey(ouv)

# ---------- radar ----------
M["radar"] = [
 {"axis": "访问深度", "order": 7.69, "nonorder": 4.24, "max": 10, "unit": "步"},
 {"axis": "停留时长", "order": 2.1, "nonorder": 0.3, "max": 5, "unit": "分"},
 {"axis": "商详触达", "order": 53.4, "nonorder": 27.0, "max": 100, "unit": "%"},
 {"axis": "确认订单", "order": 23.5, "nonorder": 4.4, "max": 100, "unit": "%"},
 {"axis": "奖品触达", "order": 13.3, "nonorder": 9.0, "max": 100, "unit": "%"},
 {"axis": "商品广度", "order": 1.53, "nonorder": 1.55, "max": 4, "unit": "个"},
]

M["uv_goods"] = int(len(goods_uv))
M["uv_nogoods"] = int(len(vuv - goods_uv))
_nx = V.sort_values(["uv", "step"]).copy()
_nx["next"] = _nx.groupby("uv")["pid"].shift(-1)
_into = _nx[_nx["next"] == "V05"]
M["confirm_from_goods_share"] = float((_into["pid"] == "V03").mean())
M["confirm_inflow"] = int(len(_into))

# ---------- validation ----------
M["rows_v"] = int(len(V)); M["rows_o"] = int(len(O))
M["date_min"] = str(V["访问日期"].min()); M["date_max"] = str(V["访问日期"].max())
M["start_uv"] = int((piv[1] == "V01").sum())
M["censor10_all"] = float((F["steps"] >= 10).mean())
M["censor10_order"] = float((F["steps"][F["isorder"]] >= 10).mean())
M["pay_rate_all"] = float(F["pay"].mean())

json.dump(M, open(os.path.join(WORK, "report_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

print("uv", M["uv_total"], "order", M["uv_order"], "nonorder", M["uv_nonorder"])
print("users", M["user_total"], M["user_order"], M["user_nonorder"])
print("confirm", M["uv_confirm"], "pay", M["uv_pay"], "pay_in_confirm", M["share_pay_in_confirm"])
print("confirm rates", round(M["confirm_rate_order"],4), round(M["confirm_rate_nonorder"],4))
print("kitagawa", {k: round(v,4) for k,v in M["kitagawa"].items() if k!="cells"})
print("sankey nodes", [len(s["nodes"]) for s in [M["sankey_order"]]])
print("goods", M["goods_n"], round(M["goods_cvr_overall"],4))
print("dur<30s", M["dur_bucket"][0])
print("arrival7", M["arrival"][6])
