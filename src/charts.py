# -*- coding: utf-8 -*-
import json, os, html, math

# 数据文件在项目根的 data/ 目录
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(_ROOT, "data", "report_data.json"), encoding="utf-8"))

INK = "#081F5C"; PAPER = "#F7F2EB"; ACCENT = "#218D80"; BLUE = "#426CB2"
RULE = "#DBE2DD"; MUTED = "#5D6E7A"; CLAY = "#B4653F"
C_ORDER = "#218D80"; C_NON = "#AEBAB4"

def esc(s): return html.escape(str(s), quote=True)
def n(x): return f"{int(round(x)):,}"
def pc(x, d=1): return f"{x*100:.{d}f}%"
def pcs(x):
    """整数百分号形式：100%、89.1%、0.4%。"""
    v = x*100
    if 0 < v < 0.1:
        return f"{v:.2f}%"
    return f"{v:.1f}".rstrip("0").rstrip(".") + "%"
def pp(x, d=1): return f"{x*100:+.{d}f}pp"

def t(x, y, s, size=12, fill=INK, anchor="start", weight=400, opacity=1, cls="", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" opacity="{opacity}" '
            f'class="{cls}" {extra}>{esc(s)}</text>')

def rect(x, y, w, h, fill, rx=0, opacity=1, extra=""):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w,0):.1f}" height="{max(h,0):.1f}" '
            f'rx="{rx}" fill="{fill}" opacity="{opacity}" {extra}/>')

def line(x1, y1, x2, y2, stroke=RULE, w=1, dash="", opacity=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{w}" opacity="{opacity}"{d}/>')

def poly(pts, fill, opacity=1, extra=""):
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{s}" fill="{fill}" opacity="{opacity}" {extra}/>'

def pline(pts, stroke, w=2, dash="", opacity=1):
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{s}" fill="none" stroke="{stroke}" stroke-width="{w}" '
            f'stroke-linejoin="round" stroke-linecap="round" opacity="{opacity}"{d}/>')

def fig(fid, title, sub, svg, note="", tall=False):
    cls = "chart tall" if tall else "chart"
    return f'''<figure class="{cls}" id="{fid}">
  <div class="chart-head"><div><h3>{title}</h3><p>{sub}</p></div>
  <button class="dl" data-dl="1" title="下载此图 SVG">SVG</button></div>
  <div class="chart-wrap">{svg}</div>
  {f'<figcaption>{note}</figcaption>' if note else ''}
</figure>'''

# ============================================================ funnel
def chart_funnel():
    W, H = 980, 322
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    rows = [
        ("g", "人群口径（用户级）", 0, ""),
        ("r", "访问 UV", M["uv_total"], ACCENT, "100%"),
        ("r", "下单用户 UV", M["uv_order"], C_ORDER, pc(M["share_order_uv"])),
        ("g", "行为口径（同期、可归因）", 0, ""),
        ("r", "访问 UV", M["uv_total"], ACCENT, "100%"),
        ("r", "触达确认订单页", M["uv_confirm"], "#B45309", pc(M["share_confirm"])),
        ("r", "触达支付结果页", M["uv_pay"], "#D97706", pc(M["share_pay"])),
    ]
    y = 18
    for row in rows:
        if row[0] == "g":
            s.append(line(0, y+4, W, y+4, RULE, 1))
            s.append(t(0, y+22, row[1], 11.5, MUTED, "start", 700))
            y += 34
            continue
        _, lab, v, col, note = row
        share = v / M["uv_total"]
        w = 520 * math.sqrt(share)
        s.append(t(150, y+19, lab, 12.5, INK, "end", 600))
        s.append(rect(162, y+5, 520, 26, "#EDE6D9", 6))
        s.append(rect(162, y+5, max(w, 5), 26, col, 6,
                      1, f'data-tip="{esc(lab + "：" + n(v) + " UV（占访问 " + pc(share) + "）")}"'))
        s.append(t(700, y+23, n(v), 14, INK, "start", 700))
        s.append(t(766, y+23, note, 11, MUTED, "start"))
        y += 40
    s.append(t(0, H-6, "条形长度按平方根缩放，仅为看清末段；数值为准。两条轨道不是嵌套关系。", 10.3, MUTED))
    s.append("</svg>")
    return "".join(s)

# ============================================================ radar
def chart_radar():
    W, H = 520, 400
    cx, cy, r = 250, 196, 100
    axes = M["radar"]; k = len(axes)
    def pt(i, v):
        a = -math.pi/2 + 2*math.pi*i/k
        return cx + r*v*math.cos(a), cy + r*v*math.sin(a)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for ring in (0.25, 0.5, 0.75, 1.0):
        s.append(poly([pt(i, ring) for i in range(k)], "none", 1,
                      f'stroke="{RULE}" stroke-width="1" fill="none"'))
    for i in range(k):
        x, y = pt(i, 1.0)
        s.append(line(cx, cy, x, y, RULE, 1))
    po, pn = [], []
    for i, a in enumerate(axes):
        po.append(pt(i, min(a["order"]/a["max"], 1)))
        pn.append(pt(i, min(a["nonorder"]/a["max"], 1)))
    s.append(poly(pn, C_NON, .30))
    s.append(poly(po, C_ORDER, .20))
    s.append(poly(pn, "none", 1, f'stroke="{C_NON}" stroke-width="2"'))
    s.append(poly(po, "none", 1, f'stroke="{C_ORDER}" stroke-width="2.4"'))
    for i, a in enumerate(axes):
        x, y = pt(i, 1.30)
        anchor = "middle"
        if x > cx + 12: anchor = "start"
        elif x < cx - 12: anchor = "end"
        s.append(t(x, y+3, a["axis"], 11.5, INK, anchor, 700))
        s.append(t(x, y+17, f'{a["order"]:g} / {a["nonorder"]:g}', 10, MUTED, anchor))
    # legend
    s.append(rect(cx-112, H-20, 12, 3, C_ORDER, 1))
    s.append(t(cx-94, H-14, "下单用户", 10.5, INK, "start", 600))
    s.append(rect(cx+4, H-20, 12, 3, C_NON, 1))
    s.append(t(cx+22, H-14, "未下单", 10.5, INK, "start", 600))
    pass
    s.append("</svg>")
    return "".join(s)

# ============================================================ sankey
# 实现在 sankey.py（独立模块，便于单独预览与迭代）
from sankey import sankey_svg  # noqa: E402

# ============================================================ arrival
def chart_arrival():
    W, H = 980, 330
    L, R, T, B = 54, 20, 30, 38
    pw, ph = W-L-R, H-T-B
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, 25, 50, 75, 100):
        y = T + ph*(1-v/100)
        s.append(line(L, y, W-R, y, RULE, 1))
        s.append(t(L-8, y+4, f"{v}%", 10.5, MUTED, "end"))
    xs = [L + pw*(i/9) for i in range(10)]
    s.append(rect(xs[7]-8, T, W-R-(xs[7]-8), ph, "#EFE7DA", 6, .85))
    s.append(t(xs[7]+8, T+16, "第 8–10 步：窗口截断区（≥10 步）", 10.5, CLAY, "start", 600))
    for i, a in enumerate(M["arrival"]):
        s.append(t(xs[i], H-B+17, str(a["step"]), 10.5, MUTED, "middle"))
    s.append(t(W-R, H-6, "步骤", 10.5, MUTED, "end"))
    for key, col, wid in (("nonorder", C_NON, 2.2), ("order", C_ORDER, 2.6)):
        pts = [(xs[i], T + ph*(1-a[key])) for i, a in enumerate(M["arrival"])]
        s.append(pline(pts, col, wid))
        for x, y in pts:
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{PAPER}" stroke="{col}" stroke-width="2"/>')
    a2, a7 = M["arrival"][1], M["arrival"][6]
    s.append(t(xs[1]+13, T+ph*(1-a2["order"])-13, f'下单 {pc(a2["order"])}', 10.5, C_ORDER, "start", 700))
    s.append(t(xs[1]+9, T+ph*(1-a2["nonorder"])+17, f'未下单 {pc(a2["nonorder"])}', 10.5, "#6E7E78", "start", 700))
    s.append(t(xs[6]+9, T+ph*(1-a7["order"])-12, pc(a7["order"]), 10.5, C_ORDER, "start", 700))
    s.append(t(xs[6]+9, T+ph*(1-a7["nonorder"])+17, pc(a7["nonorder"]), 10.5, "#6E7E78", "start", 700))
    s.append("</svg>")
    return "".join(s)

# ============================================================ reach dumbbell
def chart_reach():
    rows = sorted([r for r in M["reach"] if r["uv_total"] >= 200],
                  key=lambda r: -r["diff"])[:16]
    W = 1000; rh = 27; T = 38; B = 22; L = 116; R = 286
    H = T + rh*len(rows) + B
    pw = W - L - R; mx = 70
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, 20, 40, 60):
        x = L + pw*v/mx
        s.append(line(x, T-10, x, T+rh*len(rows), RULE, 1))
        s.append(t(x, T-16, f"{v}%", 10, MUTED, "middle"))
    for i, r in enumerate(rows):
        y = T + i*rh + rh/2
        x1 = L + pw*min(r["nonorder"]*100, mx)/mx
        x2 = L + pw*min(r["order"]*100, mx)/mx
        s.append(line(x1, y, x2, y, "#CFD8D2", 3))
        s.append(f'<circle cx="{x1:.1f}" cy="{y:.1f}" r="4" fill="{C_NON}"/>')
        s.append(f'<circle cx="{x2:.1f}" cy="{y:.1f}" r="5" fill="{C_ORDER}"/>')
        s.append(t(L-10, y+4, r["name"], 11.5, INK, "end", 600))
        s.append(t(W-R+10, y+4, pp(r["diff"]), 11.5, ACCENT if r["diff"] > 0 else CLAY, "start", 700))
        s.append(t(W-R+78, y+4, f'{pc(r["nonorder"])} → {pc(r["order"])}', 10.3, MUTED, "start"))
    s.append(t(W-R+10, T-16, "差值", 10, MUTED, "start", 700))
    s.append(t(W-R+78, T-16, "未下单 → 下单用户", 10, MUTED, "start", 700))
    s.append("</svg>")
    return "".join(s)

# ============================================================ first jump
def chart_first_jump():
    rows = M["first_jump"][:10]
    W = 1000; rh = 30; T = 42; B = 26; L = 108; R = 196
    H = T + rh*len(rows) + B
    pw = W-L-R; mx = 28
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, 5, 10, 15, 20, 25):
        x = L + pw*v/mx
        s.append(line(x, T-10, x, T+rh*len(rows), RULE, 1))
        s.append(t(x, T-16, f"{v}%", 10, MUTED, "middle"))
    overall = M["share_confirm"]
    xo = L + pw*(overall*100)/mx
    s.append(line(xo, T-10, xo, T+rh*len(rows), "#B45309", 1.4, "4 4"))
    s.append(t(xo+4, T-16, f"全站 {pc(overall)}", 10, "#B45309", "start", 600))
    for i, r in enumerate(rows):
        y = T + i*rh
        col = CLAY if r["confirm"] < overall else ACCENT
        w = pw*(r["confirm"]*100)/mx
        s.append(rect(L, y+6, w, 17, col, 4, .85,
                      f'data-tip="{esc(r["name"] + "：" + pc(r["confirm"]) + "，样本 " + n(r["uv"]) + " UV")}"'))
        s.append(t(L-10, y+19, r["name"], 11.5, INK, "end", 600))
        s.append(t(L+w+6, y+19, pc(r["confirm"]), 11, col, "start", 700))
        s.append(t(W-R+10, y+19, f'{n(r["uv"])} UV · {pc(r["share"])}', 10.3, MUTED, "start"))
    s.append(t(W-R+10, T-16, "流量规模", 10, MUTED, "start", 700))
    s.append("</svg>")
    return "".join(s)

# ============================================================ waterfall
def chart_waterfall():
    kg = M["kitagawa"]
    W, H = 980, 386
    L, R, T, B = 62, 30, 38, 74
    pw, ph = W-L-R, H-T-B
    mx = 0.28
    def yv(v): return T + ph*(1-v/mx)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, .05, .10, .15, .20, .25):
        s.append(line(L, yv(v), W-R, yv(v), RULE, 1))
        s.append(t(L-10, yv(v)+4, f"{v*100:.0f}%", 10.5, MUTED, "end"))
    bw = 112; gap = 60; x0 = L + 26
    st = kg["struct_shapley"]; ra = kg["rate_shapley"]
    bars = [("未下单 UV", 0, kg["base_nonorder"], "#B9C4BE", "基线"),
            ("首跳结构", kg["base_nonorder"], kg["base_nonorder"]+st, "#7FA8D9", "结构效应"),
            ("路径强度", kg["base_nonorder"]+st, kg["base_nonorder"]+st+ra, ACCENT, "率效应"),
            ("下单用户 UV", 0, kg["target_order"], "#1F7A6E", "结果")]
    for i, (lab, lo, hi, col, kind) in enumerate(bars):
        x = x0 + i*(bw+gap)
        s.append(rect(x, yv(hi), bw, max(yv(lo)-yv(hi), 2), col, 5, .92))
        s.append(t(x+bw/2, yv(hi)-9, f"{hi*100:.1f}%", 12, INK, "middle", 700))
        s.append(t(x+bw/2, T+ph+19, lab, 11.5, INK, "middle", 600))
        s.append(t(x+bw/2, T+ph+33, kind, 9.8, MUTED, "middle"))
        if i < 3:
            s.append(line(x+bw, yv(hi), x+bw+gap, yv(hi), "#9FB0AA", 1, "3 3"))
    s.append(t(x0+(bw+gap)+bw/2, yv(kg["base_nonorder"]+st)-24, f'+{st*100:.1f}pp', 11, "#3F6FA8", "middle", 700))
    s.append(t(x0+(bw+gap)*2+bw/2, yv(kg["base_nonorder"]+st+ra)-24, f'+{ra*100:.1f}pp', 11, ACCENT, "middle", 700))
    s.append(t(L, H-10, "对称（Shapley）分解：结构 5.0pp、强度 14.1pp。以未下单侧为权重是 2.4 / 16.7，以下单侧是 7.7 / 11.4。", 10.3, MUTED))
    s.append("</svg>")
    return "".join(s)

# ============================================================ step / duration
def chart_steps():
    sb = M["steps_bucket"]
    W, H = 470, 300; L, R, T, B = 42, 12, 36, 34
    pw, ph = W-L-R, H-T-B
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, .1, .2, .3):
        y = T+ph*(1-v/.4)
        s.append(line(L, y, W-R, y, RULE, 1))
        s.append(t(L-6, y+4, f"{v*100:.0f}%", 9.5, MUTED, "end"))
    bw = pw/len(sb)*0.42
    for i, b in enumerate(sb):
        cx = L + pw*(i+.5)/len(sb)
        h1 = ph*(b["share"]/.4)
        s.append(rect(cx-bw/2, T+ph-h1, bw, h1, "#AEBAB4" if i != 9 else "#7C8C86", 2, .95,
                      f'data-tip="{esc(b["label"]+" 步："+pc(b["share"])+" UV")}"'))
        s.append(t(cx, H-B+15, b["label"], 9.5, MUTED, "middle"))
    s.append(t(L, T-14, "未下单 UV 的步数分布", 10.3, MUTED, "start", 600))
    s.append(t(W-R, T-14, "第 10 步含截断", 9.5, CLAY, "end"))
    s.append("</svg>")
    return "".join(s)

def chart_dur():
    db = M["dur_bucket"]
    W, H = 470, 300; L, R, T, B = 42, 12, 36, 36
    pw, ph = W-L-R, H-T-B
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    mx = 0.55
    for v in (0, .2, .4):
        y = T+ph*(1-v/mx)
        s.append(line(L, y, W-R, y, RULE, 1))
        s.append(t(L-6, y+4, f"{v*100:.0f}%", 9.5, MUTED, "end"))
    bw = pw/len(db)*0.5
    for i, b in enumerate(db):
        cx = L + pw*(i+.5)/len(db)
        h = ph*(b["share"]/mx)
        s.append(rect(cx-bw/2, T+ph-h, bw, h, "#C9A27E" if i == 0 else "#8FA9DB", 2, .9,
                      f'data-tip="{esc(b["label"]+"："+pc(b["share"])+" UV，确认订单率 "+pc(b["confirm"]))}"'))
        s.append(t(cx, H-B+14, b["label"], 8.8, MUTED, "middle"))
    # confirm line on 0-30% scale mapped to ph
    pts = [(L + pw*(i+.5)/len(db), T+ph*(1-b["confirm"]/0.30)) for i, b in enumerate(db)]
    s.append(pline(pts, "#B45309", 2))
    for x, y in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{PAPER}" stroke="#B45309" stroke-width="1.8"/>')
    s.append(t(L, T-14, "UV 占比", 10.3, MUTED, "start", 600))
    s.append(t(W-R, T-14, "线＝确认订单率", 9.5, "#B45309", "end", 600))
    s.append("</svg>")
    return "".join(s)

# ============================================================ gate
def chart_gate():
    W, H = 980, 268
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    rows = [("访问 UV", M["uv_total"], ACCENT),
            ("触达商品详情页", M["uv_goods"], BLUE),
            ("触达确认订单页", M["goods_confirm_uv"], "#B45309")]
    for i, (lab, v, col) in enumerate(rows):
        share = v / M["uv_total"]
        y = 26 + i*58
        w = 430*share
        s.append(t(150, y+20, lab, 12.3, INK, "end", 600))
        s.append(rect(162, y+4, 430, 26, "#EDE6D9", 6))
        s.append(rect(162, y+4, max(w, 4), 26, col, 6, 1,
                      f'data-tip="{esc(lab + "：" + n(v) + " UV（占访问 " + pc(share) + "）")}"'))
        s.append(t(606, y+22, f"{n(v)} · {pc(share)}", 13.5, INK, "start", 700))
    s.append(t(736, 48, "没碰过商详的 " + n(M["uv_nogoods"]) + " UV", 11.5, INK, "start", 700))
    s.append(t(736, 68, f"其中触达确认订单：{M['nogoods_confirm']} 个（{pc(M['nogoods_confirm']/M['uv_nogoods'],2)}）", 11, MUTED))
    s.append(t(736, 112, "确认订单的前一步", 12, INK, "start", 700))
    s.append(t(736, 132, f"商详占 {pc(M['confirm_from_goods_share'])}，其余页面合计 <1%", 10.6, MUTED))
    s.append(t(736, 180, "进入商详的时点", 12, INK, "start", 700))
    s.append(t(736, 200, f"中位第 {M['goods_step_median']:.0f} 步、首步后 {M['goods_time_median']:.1f} 分钟", 11, MUTED))
    s.append(t(162, 250, f"商详 → 确认订单 {pc(M['goods_confirm_rate'])}（按 UV 计）", 12, "#B45309", "start", 700))
    s.append("</svg>")
    return "".join(s)

# ============================================================ goods scatter
# 脱敏版：商品一律显示「商品X + 编号」，不再引用真实名称
def gname(g):
    """完整名称（脱敏后即 商品X）。"""
    nm = (g.get("name") or "").strip()
    return nm if nm else str(g["gid"])


def glabel(g, limit=11):
    """图表/表格用短名（脱敏后直接用 name + 编号）。"""
    nm = (g.get("name") or "").strip()
    return nm if nm else str(g["gid"])


def _tw(s, size=10):
    """粗略文字宽度：中文按字号、ASCII 按 0.58 字号。"""
    return sum(size if ord(c) > 127 else size * 0.58 for c in s)


def chart_goods():
    gs = M["goods"]
    W, H = 1080, 520
    L, R, T, B = 66, 30, 42, 54
    pw, ph = W-L-R, H-T-B
    xmin, xmax = 28, 1700
    def X(b): return L + (math.log10(b)-math.log10(xmin))/(math.log10(xmax)-math.log10(xmin))*pw
    def Y(c): return T + ph*(1-c/0.8)
    xm, ym = X(150), Y(M["goods_cvr_overall"])
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    # 两个值得看的象限：低流量高转化（扩量）、高流量低转化（排查）
    s.append(rect(L, T, xm-L, ym-T, "#EAF1EE", 0, .55))
    s.append(rect(xm, ym, W-R-xm, T+ph-ym, "#F7EEE3", 0, .55))
    for c in (0, .2, .4, .6, .8):
        s.append(line(L, Y(c), W-R, Y(c), RULE, 1))
        s.append(t(L-8, Y(c)+4, f"{c*100:.0f}%", 10, MUTED, "end"))
    for b in (30, 50, 100, 200, 500, 1000):
        s.append(line(X(b), T, X(b), T+ph, RULE, 1, "2 3"))
        s.append(t(X(b), H-B+16, str(b), 10, MUTED, "middle"))
    s.append(t(L+pw/2, H-8, "浏览 UV（对数轴）", 10.5, MUTED, "middle"))
    s.append(t(L-4, T-18, "商品详情页 → 确认订单转化率", 10.5, MUTED, "start", 600))
    s.append(line(xm, T, xm, T+ph, "#9FB0AA", 1, "5 4"))
    s.append(line(L, ym, W-R, ym, "#9FB0AA", 1, "5 4"))
    s.append(t(xm+6, T+13, "浏览中位数 150", 9.2, MUTED))
    s.append(t(L+4, ym-6, f"商品级加权 {pc(M['goods_cvr_overall'])}", 9.2, MUTED, "start"))
    q1 = "低流量 · 高转化 → 扩量候选"
    s.append(t(L+10, T+16, q1, 9, "#2F6E63", "start", 600))
    # 颜色图例（右上空白区）
    lg_y = T + 16
    s.append(f'<circle cx="{W-R-228:.1f}" cy="{lg_y-3:.1f}" r="4" fill="{ACCENT}" opacity=".8"/>')
    s.append(t(W-R-220, lg_y, f"高转化 ≥ {pc(M['goods_cvr_overall'])}", 9, MUTED))
    s.append(f'<circle cx="{W-R-112:.1f}" cy="{lg_y-3:.1f}" r="4" fill="#C9A27E" opacity=".8"/>')
    s.append(t(W-R-104, lg_y, f"低转化 < {pc(M['goods_cvr_overall'])}", 9, MUTED))
    # 预留文字位置，标签避让
    placed = [(L+4, T+6, L+14+_tw(q1, 9), T+20),
              (W-R-234, T+6, W-R-42, T+22)]
    byid = {g["gid"]: g for g in gs}
    for g in gs:
        x, y = X(g["browse"]), Y(g["cvr"])
        r = 3.2 + math.sqrt(g["order"])/2.6
        col = ACCENT if g["cvr"] >= M["goods_cvr_overall"] else "#C9A27E"
        tip = (f'{gname(g)}（编号 {g["gid"]}）\n浏览 {n(g["browse"])} UV\n'
               f'确认订单 {n(g["order"])} UV ｜ 转化 {pc(g["cvr"])}')
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" opacity=".72" '
                 f'data-tip="{esc(tip)}"/>')
    # 关键商品（脱敏后按编号引用，对应浏览量前十中的关键点）
    label_ids = ["P01", "P02", "P05", "P03", "P06", "P08", "P13", "P16", "P18", "P19"]
    for gid in label_ids:
        g = byid.get(gid)
        if not g:
            continue
        name = glabel(g)
        x, y = X(g["browse"]), Y(g["cvr"])
        r = 3.2 + math.sqrt(g["order"])/2.6
        w = _tw(name)
        cands = [(r+5, -4, "start"), (-r-5, -4, "end"),
                 (r+5, 13, "start"), (-r-5, 13, "end"),
                 (0, -14, "middle"), (0, 22, "middle"),
                 (r+5, -16, "start"), (-r-5, -16, "end"),
                 (r+5, 25, "start"), (-r-5, 25, "end"),
                 (r+8, -28, "start"), (-r-8, -28, "end"),
                 (0, -30, "middle"), (r+8, 36, "start"), (-r-8, 36, "end")]
        chosen = None
        for dx, dy, anc in cands:
            lx, ly = x + dx, y + dy
            bx0 = lx if anc == "start" else (lx - w if anc == "end" else lx - w/2)
            bx1 = bx0 + w
            by0, by1 = ly - 10, ly + 3
            if bx0 < L + 3 or bx1 > W - R - 3 or by0 < T + 3 or by1 > T + ph - 3:
                continue
            if any(not (bx1 < a or bx0 > c or by1 < b or by0 > d) for a, b, c, d in placed):
                continue
            chosen = (lx, ly, anc, bx0, bx1, by0, by1)
            break
        if not chosen:
            continue
        lx, ly, anc, bx0, bx1, by0, by1 = chosen
        placed.append((bx0, by0, bx1, by1))
        sx = x + (r + 1.5) * (1 if lx >= x else -1)
        ex = bx0 - 2 if lx >= x else bx1 + 2
        s.append(line(sx, y, ex, (by0 + by1) / 2, "#8FA0A8", .8, "", .5))
        s.append(t(lx, ly, name, 10, "#1E3346", anc, 650))
    s.append("</svg>")
    return "".join(s)

# ============================================================ dates
def chart_dates():
    ds = M["dates"]
    W, H = 980, 320
    L, R, T, B = 52, 20, 34, 44
    pw, ph = W-L-R, H-T-B
    muv = max(d["uv"] for d in ds)*1.08
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, .1, .2, .3, .4):
        y = T+ph*(1-v/0.45)
        s.append(line(L, y, W-R, y, RULE, 1))
        s.append(t(L-8, y+4, f"{v*100:.0f}%", 10, "#9A7B4F", "end"))
    s.append(t(L-8, T-12, "确认订单率", 10, "#9A7B4F", "end", 600))
    s.append(t(L, T-12, "UV", 10, MUTED, "start", 600))
    bw = pw/len(ds)*0.62
    for i, d in enumerate(ds):
        cx = L + pw*(i+.5)/len(ds)
        h = ph*(d["uv"]/muv)
        s.append(rect(cx-bw/2, T+ph-h, bw, h, "#B7CEC8", 1.5, .9,
                      f'data-tip="{esc(d["d"]+"："+n(d["uv"])+" UV，确认订单率 "+pc(d["rate"]))}"'))
        if i % 4 == 0:
            s.append(t(cx, H-B+15, d["d"][5:], 9, MUTED, "middle"))
    pts = [(L+pw*(i+.5)/len(ds), T+ph*(1-d["rate"]/0.45)) for i, d in enumerate(ds)]
    s.append(pline(pts, "#B45309", 1.8))
    for x, y in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{PAPER}" stroke="#B45309" stroke-width="1.4"/>')
    for d in sorted(ds, key=lambda x: -x["uv"])[:2]:
        i = ds.index(d); cx = L + pw*(i+.5)/len(ds)
        s.append(t(cx, T+ph*(1-d["uv"]/muv)-7, n(d["uv"]), 9.5, "#3E5B54", "middle", 700))
    s.append("</svg>")
    return "".join(s)

# ============================================================ hours
def chart_hours():
    hs = M["hours"]
    W, H = 980, 300
    L, R, T, B = 52, 20, 34, 40
    pw, ph = W-L-R, H-T-B
    muv = max(h["uv"] for h in hs)*1.12
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for v in (0, .05, .10, .15, .20):
        y = T+ph*(1-v/0.22)
        s.append(line(L, y, W-R, y, RULE, 1))
        s.append(t(L-8, y+4, f"{v*100:.0f}%", 9.5, "#9A7B4F", "end"))
    s.append(t(L-8, T-12, "确认订单率", 9.5, "#9A7B4F", "end", 600))
    s.append(t(L, T-12, "UV", 10, MUTED, "start", 600))
    bw = pw/len(hs)*0.6
    for i, h in enumerate(hs):
        cx = L + pw*(i+.5)/len(hs)
        hh = ph*(h["uv"]/muv)
        s.append(rect(cx-bw/2, T+ph-hh, bw, hh, "#B7CEC8", 1.5, .9,
                      f'data-tip="{esc(str(h["h"])+" 点："+n(h["uv"])+" UV，确认订单率 "+pc(h["rate"]))}"'))
        s.append(t(cx, H-B+15, str(h["h"]), 9, MUTED, "middle"))
    pts = [(L+pw*(i+.5)/len(hs), T+ph*(1-h["rate"]/0.22)) for i, h in enumerate(hs)]
    s.append(pline(pts, "#B45309", 1.8))
    for x, y in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{PAPER}" stroke="#B45309" stroke-width="1.4"/>')
    for i, dx in ((10, 0),):
        cx = L + pw*(i+.5)/len(hs)
        s.append(t(cx+dx, T+ph*(1-hs[i]["uv"]/muv)-7, f'{n(hs[i]["uv"])} UV · {pc(hs[i]["rate"])}', 9.5, "#8A5A3B", "middle", 700))
    s.append("</svg>")
    return "".join(s)
