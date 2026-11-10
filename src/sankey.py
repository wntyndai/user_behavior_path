# -*- coding: utf-8 -*-
"""Sankey module for the dual-cohort report.

Design rules
------------
* 7 fixed steps, one column per step; node order is identical in every column so
  the same page is always found in the same place.
* Node height = page share of that step.  Ribbon height = share of the *source*
  page's UV, so widths are directly readable (no non-linear boost) and the blank
  tail of a node is exactly its drop-off.
* Colour encodes page category (活动/浏览/交易/账户/其他); ribbons fade along the
  source colour, so origin is readable without hunting for the source node.
* Three emphasis tiers.  Flows below 2% of the step are hidden by default (they
  stay in the DOM): hovering a node reveals all of its own flows, and the
  「细流」 toggle reveals everything.
* Flow percentages live in tooltips/hover only; no floating numbers on the canvas.
"""
import html

INK = "#081F5C"
MUTED = "#5D6E7A"
PAPER = "#F7F2EB"
RULE = "#DBE2DD"


def esc(s):
    return html.escape(str(s), quote=True)


def n(x):
    return f"{int(round(x)):,}"


def pc(x, d=1):
    return f"{x * 100:.{d}f}%"


def pcs(x):
    """Percent without trailing .0 (25%, 33.9%, 0.04%)."""
    v = x * 100
    if 0 < v < 0.1:
        return f"{v:.2f}%"
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s + "%"

# page -> (category, colour)
PAGE = {
    "V01": ("活动", "#1C8677"),
    "V02": ("浏览", "#4472A8"),
    "V03": ("浏览", "#24528C"),
    "V04": ("浏览", "#7FA0C6"),
    "V05": ("交易", "#C05A34"),
    "V06": ("交易", "#C58A45"),
    "V07": ("交易", "#96683A"),
    "V08": ("账户", "#9C7290"),
    "V09": ("账户", "#C39BB0"),
    "V10": ("账户", "#7F6377"),
    "V11": ("账户", "#A98A66"),
    "V12": ("其他", "#B4AC9E"),
    "OTHER": ("其他", "#C9C2B4"),
}
FALLBACK = ("其他", "#C9C2B4")

CATS = [("活动", "#1C8677"), ("浏览", "#3A66A0"), ("交易", "#B9633A"),
        ("账户", "#9C7290"), ("其他", "#BDB5A7")]

# node order inside every column (activity -> browse -> transaction -> account -> rest)
ORDER = ["V01", "V02", "V03", "V04", "V05", "V06", "V07",
         "V08", "V09", "V10", "V11", "V12", "OTHER"]

MAIN_T = 0.040   # >= 4.0% of the step -> fully saturated
SUB_T = 0.020    # >= 2.0% -> visible but quiet; below -> hidden until hover


def cat(pid):
    return PAGE.get(str(pid), FALLBACK)[0]


def pcol(pid):
    return PAGE.get(str(pid), FALLBACK)[1]


def _curve(x1, y1, h1, x2, y2, h2):
    dx = x2 - x1
    return (f"M{x1:.1f} {y1:.1f} C{x1 + dx * 0.42:.1f} {y1:.1f} "
            f"{x2 - dx * 0.42:.1f} {y2:.1f} {x2:.1f} {y2:.1f} "
            f"L{x2:.1f} {y2 + h2:.1f} C{x2 - dx * 0.42:.1f} {y2 + h2:.1f} "
            f"{x1 + dx * 0.42:.1f} {y1 + h1:.1f} {x1:.1f} {y1 + h1:.1f} Z")


def sankey_svg(data, W=1300, H=600, uid="sk"):
    rank = {p: i for i, p in enumerate(ORDER)}

    def rk_(p):
        return rank.get(p, 99)

    steps = data["steps"]
    top, bottom, left, right, nw = 96, 30, 104, 118, 16
    ph = H - top - bottom
    NGAP = 8

    # --- column geometry: the first hop gets a tighter gap -------------
    first = 246
    gap = (W - right - first - nw) / (steps - 2) if steps > 2 else 0
    xs = [left, first] + [first + gap * i for i in range(1, steps - 1)]

    # --- node layout ---------------------------------------------------
    lay, tot, order_in_step = {}, {}, {}
    for nd in data["nodes"]:
        y = top
        tot[nd["step"]] = nd["total"]
        pids = sorted([it["pid"] for it in nd["items"]], key=lambda p: (rk_(p), p))
        order_in_step[nd["step"]] = pids
        items = {it["pid"]: it for it in nd["items"]}
        inner = ph - NGAP * max(len(pids) - 1, 0)
        for pid in pids:
            it = items[pid]
            h = max(it["share"] * inner, 0)
            lay[(nd["step"], pid)] = {"y": y, "h": h, "uv": it["uv"],
                                      "name": it["name"], "pid": pid,
                                      "share": it["share"]}
            y += h + NGAP

    # --- edges ---------------------------------------------------------
    edges = []
    for si in range(1, steps):
        for k, e in enumerate(data["edges"][si - 1]):
            node_s = lay[(si, e["s"])]
            edges.append({"eid": f"{si}-{k}", "si": si, "k": k,
                          "s": e["s"], "t": e["t"], "n": e["n"],
                          "name_s": node_s["name"],
                          "name_t": lay[(si + 1, e["t"])]["name"],
                          "share": e["n"] / tot[si],
                          "share_src": e["n"] / node_s["uv"] if node_s["uv"] else 0})

    # --- offsets inside each node (ordered by the opposite column's rank)
    #     width = share of that page's UV, so the blank tail of a node is exactly
    #     the drop-off (visitors who stopped after this page).
    out_off, in_off = {}, {}
    for si in range(1, steps):
        by_src = {}
        for e in edges:
            if e["si"] == si:
                by_src.setdefault(e["s"], []).append(e)
        for pid, lst in by_src.items():
            lst.sort(key=lambda e: rk_(e["t"]))
            node = lay[(si, pid)]
            base = max(node["uv"], sum(e["n"] for e in lst), 1.0)
            y = node["y"]
            for e in lst:
                h = e["n"] / base * node["h"]
                out_off[e["eid"]] = (y, h)
                y += h
        by_tgt = {}
        for e in edges:
            if e["si"] == si:
                by_tgt.setdefault(e["t"], []).append(e)
        for pid, lst in by_tgt.items():
            lst.sort(key=lambda e: rk_(e["s"]))
            node = lay[(si + 1, pid)]
            base = max(node["uv"], sum(e["n"] for e in lst), 1.0)
            y = node["y"]
            for e in lst:
                h = e["n"] / base * node["h"]
                in_off[e["eid"]] = (y, h)
                y += h

    inflow, outflow = {}, {}
    for e in edges:
        inflow[(e["si"] + 1, e["t"])] = inflow.get((e["si"] + 1, e["t"]), 0) + e["n"]
        outflow[(e["si"], e["s"])] = outflow.get((e["si"], e["s"]), 0) + e["n"]

    # --- dominant follow-on path after any hop --------------------------
    def best_path(start_pid, from_step):
        """从第 from_step 步的 start_pid 出发，沿每步人数最多的一跳走到末尾。"""
        cur, ids = start_pid, []
        for step in range(from_step + 1, steps):
            cand = [(k, ee) for k, ee in enumerate(data["edges"][step - 1]) if ee["s"] == cur]
            if not cand:
                break
            base = tot[step]
            pool = [c for c in cand if c[1]["n"] >= 0.02 * base] or cand
            k, ee = max(pool, key=lambda c: (c[1]["n"] / base, c[1]["n"]))
            ids.append(f"{step}-{k}")
            cur = ee["t"]
        return ids

    paths = {e["eid"]: best_path(e["t"], e["si"]) for e in edges}

    # --- 到达确认订单概率最高的后续路径（双击流量带时用）-----------------
    # V[(step, pid)] = 到达该页后、剩余步数内触达「确认订单」的实际概率
    #   （按该页真实去向加权，等价于“这一页的后续转化率”）
    # D[(step, pid)] = 沿可达路径到确认订单最少还要几步（用于“更早到达”）
    CONFIRM = "V05"
    INF = 99
    V, D = {}, {}
    for step in range(steps, 0, -1):
        for pid in order_in_step[step]:
            if str(pid) == CONFIRM:
                V[(step, pid)], D[(step, pid)] = 1.0, 0
                continue
            if step == steps:
                V[(step, pid)], D[(step, pid)] = 0.0, INF
                continue
            base = tot[step]
            cand = [e for e in edges if e["si"] == step and e["s"] == pid]
            pool = [e for e in cand if e["n"] >= 0.02 * base] or cand
            out = sum(e["n"] for e in cand) or 1
            V[(step, pid)] = sum(e["n"] / out * V.get((step + 1, e["t"]), 0.0) for e in cand)
            ds = [D.get((step + 1, e["t"]), INF) for e in pool]
            best = min(ds) if ds else INF
            D[(step, pid)] = 1 + best if best < INF else INF

    def conv_path(start_pid, from_step):
        cur, ids = start_pid, []
        if str(cur) == CONFIRM:
            return ids
        for step in range(from_step + 1, steps):
            cand = [e for e in edges if e["si"] == step and e["s"] == cur]
            if not cand:
                break
            base = tot[step]
            pool = [e for e in cand if e["n"] >= 0.02 * base] or cand
            vmax = max(V.get((step + 1, e["t"]), 0.0) for e in pool)
            # 转化率与最优相差 1pp 以内，视为同级，优先更早到达，再取人数更多
            near = [e for e in pool if V.get((step + 1, e["t"]), 0.0) >= vmax - 0.01]
            e = min(near, key=lambda x: (D.get((step + 1, x["t"]), INF), -x["n"]))
            ids.append(e["eid"])
            cur = e["t"]
            if str(cur) == CONFIRM:
                break
        return ids

    cpaths = {e["eid"]: conv_path(e["t"], e["si"]) for e in edges}

    # 百分比只在悬停时出现，避免静态图里出现悬浮数字。

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
         f'font-family="Inter, Microsoft YaHei, PingFang SC, sans-serif" '
         f'aria-label="7 步页面路径桑基图" preserveAspectRatio="xMidYMid meet">']
    s.append("<defs>")
    for pid in ORDER:
        c = pcol(pid)
        s.append(f'<linearGradient id="{uid}-g-{pid}" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0" stop-color="{c}" stop-opacity=".80"/>'
                 f'<stop offset="1" stop-color="{c}" stop-opacity=".42"/></linearGradient>')
    s.append("</defs>")

    # --- legend ---------------------------------------------------------
    lx = 104.0
    for name, c in CATS:
        s.append(f'<circle cx="{lx + 3.5:.1f}" cy="18" r="3.6" fill="{c}"/>')
        s.append(f'<text x="{lx + 12:.1f}" y="22" font-size="10.5" fill="{MUTED}" '
                 f'font-weight="600">{name}</text>')
        lx += 62
    s.append(f'<text x="{W - right}" y="22" text-anchor="end" font-size="10" '
             f'fill="#93A1AA">色带宽度 = 该跳占来源页面的比例</text>')

    # --- step headers ---------------------------------------------------
    for i in range(steps):
        x = xs[i]
        if i > 0:
            s.append(f'<line x1="{xs[i - 1]:.1f}" y1="44" x2="{x - 6:.1f}" y2="44" '
                     f'stroke="{RULE}" stroke-width="1"/>')
        s.append(f'<text x="{x:.1f}" y="67" font-size="10" fill="{MUTED}" '
                 f'font-weight="700" letter-spacing="1.3">第 {i + 1} 步</text>')
        if i > 0:
            d = tot[i + 1] / tot[i] - 1
            s.append(f'<text x="{x + 54:.1f}" y="67" font-size="9.5" fill="#B4653F" '
                     f'font-weight="700">↓{abs(d) * 100:.0f}%</text>')
        s.append(f'<text x="{x:.1f}" y="86" font-size="12.5" fill="{INK}" '
                 f'font-weight="700">{n(tot[i + 1])}<tspan font-size="9.5" fill="#93A1AA" '
                 f'font-weight="600"> UV</tspan></text>')

    # --- ribbons --------------------------------------------------------
    s.append('<g class="flows" style="mix-blend-mode:multiply">')
    bands = []
    for e in edges:
        y1, h1 = out_off[e["eid"]]
        y2, h2 = in_off[e["eid"]]
        x1 = xs[e["si"] - 1] + nw
        x2 = xs[e["si"]]
        tier = "main" if e["share"] >= MAIN_T else ("sub" if e["share"] >= SUB_T else "mini")
        rate = e["share_src"]
        tip = (f'{e["name_s"]} → {e["name_t"]}\n{n(e["n"])} UV ｜ 占来源页面 {pcs(rate)}'
               f' ｜ 占本步 {pcs(e["share"])}')
        extra = (f' data-e="{e["eid"]}" data-s="{e["s"]}" data-t="{e["t"]}" data-st="{e["si"]}"'
                 f' data-sname="{esc(e["name_s"])}"'
                 f' data-tname="{esc(e["name_t"])}" data-rate="{pcs(rate)}"'
                 f' data-path="{",".join(paths[e["eid"]])}"'
                 f' data-pathc="{",".join(cpaths[e["eid"]])}"')
        quiet = cat(e["s"]) in ("账户", "其他")
        cls = "flow " + tier + (" quiet" if quiet else "") + " clickable"
        if tier == "mini":
            op = 0.0
        elif tier == "main":
            op = 0.46 if quiet else 0.74
        else:
            op = 0.16 if quiet else 0.40
        d = _curve(x1, y1, max(h1, 0.6), x2, y2, max(h2, 0.6))
        fill = f'url(#{uid}-g-{e["s"]})'
        edge = ' stroke="{0}" stroke-opacity=".62" stroke-width=".8"'.format(PAPER)
        bands.append((e["si"], y1, f'<path class="{cls}" d="{d}" fill="{fill}" opacity="{op:.2f}"{edge}'
                                   f'{extra} data-tip="{esc(tip)}"/>'))
    # draw far-left / top ribbons first so the eye lands on the lower pile last
    s.extend([b[2] for b in sorted(bands, key=lambda b: (b[0], b[1]))])
    s.append("</g>")

    # --- nodes ----------------------------------------------------------
    s.append('<g class="nodes">')
    for nd in data["nodes"]:
        for pid in order_in_step[nd["step"]]:
            node = lay[(nd["step"], pid)]
            if node["h"] <= 0.4:
                continue
            tip = f'{node["name"]}：{pcs(node["share"])}'
            s.append(f'<rect class="node" x="{xs[nd["step"] - 1]:.1f}" y="{node["y"]:.1f}" '
                     f'width="{nw}" height="{max(node["h"] - 1.2, 0.8):.1f}" rx="2.6" '
                     f'fill="{pcol(pid)}" data-pid="{pid}" data-step="{nd["step"]}" '
                     f'data-name="{esc(node["name"])}" data-in="{n(inflow.get((nd["step"], pid), 0))}" '
                     f'data-out="{n(outflow.get((nd["step"], pid), 0))}" '
                     f'data-tip="{esc(tip)}"/>')
    s.append("</g>")

    # --- node labels (every node gets a name) ---------------------------
    s.append('<g class="nlabels" pointer-events="none">')
    BLOCK, LGAP = 26.0, 2.0
    for nd in data["nodes"]:
        step = nd["step"]
        col = []
        for pid in order_in_step[step]:
            node = lay[(step, pid)]
            if node["h"] < 1.2:
                continue
            col.append({"pid": pid, "node": node, "cy": node["y"] + node["h"] / 2})
        # spread labels so none collide, then clamp to the plot bottom
        prev = -1e9
        for it in col:
            it["ly"] = max(it["cy"], prev + BLOCK + LGAP)
            prev = it["ly"]
        nxt = H - bottom - 14
        for it in reversed(col):
            it["ly"] = min(it["ly"], nxt)
            nxt = it["ly"] - BLOCK - LGAP
        for it in col:
            pid, node, cy, ly = it["pid"], it["node"], it["cy"], it["ly"]
            if step == 1:
                lx, anchor = xs[0] - 13, "end"
                lead = (xs[0], cy, lx + 3, ly)
            else:
                lx, anchor = xs[step - 1] + nw + 13, "start"
                lead = (xs[step - 1] + nw, cy, lx - 3, ly)
            s.append(f'<g class="nlabel" data-npid="{pid}" data-nstep="{step}">')
            if abs(ly - cy) > 3:
                s.append(f'<line class="nlead" x1="{lead[0]:.1f}" y1="{cy:.1f}" '
                         f'x2="{lead[2]:.1f}" y2="{ly:.1f}" stroke="{MUTED}" '
                         f'stroke-width=".9" opacity=".5"/>')
                s.append(f'<circle cx="{lead[0]:.1f}" cy="{cy:.1f}" r="1.6" fill="{MUTED}" opacity=".7"/>')
            s.append(f'<text x="{lx:.1f}" y="{ly - 2.0:.1f}" font-size="10.3" fill="{INK}" '
                     f'font-weight="650" stroke="{PAPER}" stroke-width="3.6" '
                     f'paint-order="stroke" text-anchor="{anchor}">{esc(node["name"])}</text>')
            s.append(f'<text class="npct" data-npid="{pid}" data-nstep="{step}" '
                     f'data-share="{pcs(node["share"])}" x="{lx:.1f}" y="{ly + 9.4:.1f}" '
                     f'font-size="8.9" fill="{MUTED}" stroke="{PAPER}" stroke-width="3.2" '
                     f'paint-order="stroke" text-anchor="{anchor}">{pcs(node["share"])}</text>')
            s.append("</g>")
    s.append("</g>")

    # --- flow labels: every first-hop ribbon keeps a permanent % -------
    s.append('<g class="flabels" pointer-events="none">')
    first_y, prev = {}, -1e9
    for e in sorted([x for x in edges if x["si"] == 1 and x["n"] >= 50],
                    key=lambda x: in_off[x["eid"]][0]):
        y1, h1 = out_off[e["eid"]]
        y2, h2 = in_off[e["eid"]]
        y = max(y2 + h2 / 2, prev + 13.5)
        prev = y
        first_y[e["eid"]] = y
    for e in edges:
        y1, h1 = out_off[e["eid"]]
        y2, h2 = in_off[e["eid"]]
        x1 = xs[e["si"] - 1] + nw
        x2 = xs[e["si"]]
        rate = e["share_src"]
        if e["eid"] in first_y:
            x, y, anchor = x2 - 10, first_y[e["eid"]], "end"
            cls = "flabel always"
        else:
            x, y, anchor = (x1 + x2) / 2, ((y1 + h1 / 2) + (y2 + h2 / 2)) / 2 + 3.5, "middle"
            cls = "flabel"
        s.append(f'<text class="{cls}" data-for="{e["eid"]}" x="{x:.1f}" y="{y:.1f}" '
                 f'font-size="10.5" fill="{INK}" text-anchor="{anchor}" '
                 f'stroke="{PAPER}" stroke-width="3.4" paint-order="stroke" '
                 f'font-weight="700">{pcs(rate)}</text>')
    s.append("</g>")

    s.append("</svg>")
    return "".join(s)
