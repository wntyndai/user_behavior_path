# -*- coding: utf-8 -*-
import json, os, html
from charts import (M, n, pc, pp, esc, fig, chart_funnel, chart_radar, sankey_svg,
                    chart_arrival, chart_reach, chart_first_jump, chart_waterfall,
                    chart_steps, chart_dur, chart_goods, chart_dates,
                    chart_hours, gname, glabel,
                    C_ORDER, C_NON, ACCENT, BLUE, CLAY, INK, MUTED)

# 项目根目录（src/ 的上一级），输出到 output/
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output", "营销活动用户行为路径分析_脱敏版.html")

kg = M["kitagawa"]
arr = M["arrival"]
a2o, a2n = arr[1]["order"], arr[1]["nonorder"]
a7o, a7n = arr[6]["order"], arr[6]["nonorder"]
fj = M["first_jump"]
dshort = M["dur_bucket"][0]
dmid = M["dur_bucket"][2]
dlong = M["dur_bucket"][6]
ds = M["dates"]
hs = M["hours"]
peak = max(ds, key=lambda d: d["uv"])
worst = min([d for d in ds if d["uv"] > 800], key=lambda d: d["rate"])
best = max([d for d in ds if d["uv"] > 100], key=lambda d: d["rate"])
h10, h22 = hs[10], hs[22]
hbest = max(hs, key=lambda h: h["rate"])
fj_dead = [r for r in fj if r["pid"] in ("none", "V01", "V08")]
dead_share = sum(r["share"] for r in fj_dead)
fj_good = [r for r in fj if r["pid"] in ("V03", "V02", "V04")]
good_share = sum(r["share"] for r in fj_good)

goods = M["goods"]
rd = {r["name"]: r for r in M["reach"]}
hs_day = [h for h in hs if 12 <= h["h"] <= 19]
day_uv = sum(h["uv"] for h in hs_day); day_conf = sum(h["confirm"] for h in hs_day)
day_rate = day_conf / day_uv
peak_uv = h10["uv"] + h22["uv"]

def sk_item(data, step, pid):
    for it in data["nodes"][step-1]["items"]:
        if it["pid"] == pid:
            return it
    return {"share": 0.0, "uv": 0}

hi_browse = sorted(goods, key=lambda g: -g["browse"])[:6]
hi_cvr = sorted([g for g in goods if g["browse"] >= 50], key=lambda g: -g["cvr"])[:4]
seen, gt = set(), []
for g in hi_browse + hi_cvr:
    if g["gid"] in seen: continue
    seen.add(g["gid"]); gt.append(g)

def judge(g):
    if g["cvr"] >= 0.30: return "高转化，可扩量"
    if g["browse"] >= 600 and g["cvr"] < 0.10: return "高流量低转化，建议优化"
    if g["cvr"] < 0.05: return "低转化，观察"
    return "—"

sankey_all = sankey_svg(M["sankey_all"], uid="ska")
sankey_n = sankey_svg(M["sankey_nonorder"], uid="skn")
sankey_o = sankey_svg(M["sankey_order"], uid="sko")

PAGE_TABLE = [
    ("V01", "活动页", "活动"), ("V02", "新首页", "浏览"), ("V03", "商品详情页", "浏览"),
    ("V04", "项目列表", "浏览"), ("V05", "确认订单", "交易"), ("V06", "支付结果", "交易"),
    ("V07", "订单详情", "交易"), ("V08", "积分明细", "账户"), ("V09", "我的奖品", "账户"),
    ("V10", "我的页", "账户"), ("V11", "优惠券页", "账户"), ("V12", "H5", "其他"),
]

CSS = """
:root{--paper:#F7F2EB;--ink:#081F5C;--muted:#5D6E7A;--accent:#218D80;--blue:#426CB2;
--rule:#E2D9C9;--card:#FFFCF6;--clay:#B4653F}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:Inter,"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
font-variant-numeric:tabular-nums;line-height:1.68;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:0 28px}
header.top{position:sticky;top:0;z-index:50;background:rgba(247,242,235,.93);
backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
.topbar{display:flex;align-items:center;gap:20px;height:52px}
.brand{font-size:11.5px;letter-spacing:.12em;font-weight:800;color:var(--muted);white-space:nowrap}
nav{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
nav a{font-size:12.5px;color:var(--muted);text-decoration:none;padding:5px 9px;border-radius:7px;white-space:nowrap}
nav a:hover{background:#EDE6D9;color:var(--ink)}
.hero{padding:62px 0 6px}
.eyebrow{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:800}
h1{font-size:clamp(30px,4vw,44px);line-height:1.26;margin:14px 0 18px;letter-spacing:-.012em;font-weight:700}
.lede{font-size:15.5px;color:#2C4257;max-width:830px;margin:0}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:36px 0 6px}
.kpi{background:var(--card);border:1px solid var(--rule);border-radius:16px;padding:15px 18px 13px;border-top:3px solid var(--accent)}
.kpi b{display:block;font-size:27px;letter-spacing:-.02em;line-height:1.2}
.kpi span{font-size:12px;color:var(--muted);display:block;margin-top:3px}
.kpi em{font-size:11px;color:#93A1AA;font-style:normal;display:block;margin-top:1px}
.takeaways{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:20px 0 0}
.tk{background:var(--card);border:1px solid var(--rule);border-radius:16px;padding:18px}
.tk h3{margin:0 0 6px;font-size:13.5px;letter-spacing:.01em}
.tk p{margin:0;font-size:12.6px;color:#3C5164}
.tk b{color:var(--accent)}
section{padding:52px 0 4px;border-top:1px solid var(--rule);margin-top:58px}
h2{font-size:22px;margin:0 0 6px;display:flex;align-items:baseline;gap:10px;letter-spacing:-.01em}
h2 i{font-style:normal;font-size:11.5px;color:var(--accent);font-weight:800;letter-spacing:.12em}
.sub{color:var(--muted);font-size:13.4px;margin:0 0 20px;max-width:850px}
h3{font-size:15px;margin:32px 0 6px}
p{margin:0 0 12px;font-size:13.6px;color:#243B50}
ul,ol{margin:8px 0 14px;padding-left:20px;font-size:13.4px;color:#243B50}
li{margin:5px 0}
.chart{background:var(--card);border:1px solid var(--rule);border-radius:18px;padding:16px 20px 12px;margin:16px 0 8px}
.chart-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:4px}
.chart-head h3{margin:0;font-size:14px}
.chart-head p{margin:2px 0 0;font-size:11.6px;color:var(--muted)}
.chart-wrap{overflow-x:auto}
.chart-wrap svg{display:block;min-width:660px;width:100%;height:auto}
.chart.wide .chart-wrap svg{min-width:1480px}
figcaption{font-size:11.3px;color:#7D8C95;line-height:1.62;margin-top:6px;border-top:1px dashed var(--rule);padding-top:7px}
.dl{font:700 10px/1 Inter,sans-serif;letter-spacing:.08em;color:var(--muted);
background:transparent;border:1px solid var(--rule);border-radius:6px;padding:5px 7px;cursor:pointer;flex:none}
.dl:hover{color:var(--ink);border-color:#C9BEA9}
.note{background:#EAF1EE;border-left:3px solid var(--accent);border-radius:0 12px 12px 0;
padding:13px 18px;margin:14px 0;font-size:13px;color:#1E4A46}
.note b{color:#123B37}
.warn{background:#F6EEE4;border-left:3px solid var(--clay);border-radius:0 12px 12px 0;
padding:13px 18px;margin:14px 0;font-size:13px;color:#6B3F26}
table{border-collapse:collapse;width:100%;font-size:12.4px;margin:10px 0 6px}
th,td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:700;font-size:11.2px;letter-spacing:.03em;background:#F3EDE1}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:hover{background:#F7F1E5}
details{background:var(--card);border:1px solid var(--rule);border-radius:14px;padding:13px 18px;margin:12px 0}
summary{cursor:pointer;font-weight:700;font-size:13.2px;color:#2C4257}
details[open] summary{margin-bottom:8px}
.seg{display:flex;gap:5px;flex:none}
.seg button{font:600 11.5px/1 inherit;color:var(--muted);background:#F3EDE1;border:1px solid var(--rule);
padding:7px 12px;border-radius:8px;cursor:pointer}
.seg button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.actions{display:grid;grid-template-columns:repeat(2,1fr);gap:48px;margin:18px 0}
.act{background:var(--card);border:1px solid var(--rule);border-radius:16px;padding:18px}
.act h4{margin:0 0 8px;font-size:13.5px;color:var(--accent)}
.act ul{margin:0;padding-left:16px;font-size:12.6px}
.act li{margin:6px 0;color:#33495C}
.chart.sankey{width:min(1340px,calc(100vw - 40px));margin-left:50%;transform:translateX(-50%)}
.sk-panel{position:relative}
.flow{transition:opacity .18s ease}
.flow.mini{pointer-events:none}
.flow.faded{opacity:.035!important}
.flow.on{opacity:1!important}
.flow.mini.on{opacity:.55!important;pointer-events:auto}
.flow.lit{opacity:1!important;stroke:#081F5C;stroke-width:.7}
.flow.lit.cv{stroke:#B45309;stroke-width:1.6}
.flow.clickable{cursor:pointer}
.sk-panel:not(.hovering):not(.pathing) .flow.clickable:hover{opacity:1!important}
.sk-panel.showall .flow.mini{opacity:.16;pointer-events:auto}
.node{transition:opacity .18s ease,stroke-width .18s ease}
.sk-panel.hovering .node{opacity:.28}
.sk-panel.hovering .node.on{opacity:1;stroke:#081F5C;stroke-width:1.8}
.sk-panel.hovering .node.sel{stroke:#0B2A4A;stroke-width:2.8}
.sk-panel.pathing .node{opacity:.3}
.sk-panel.pathing .node.on{opacity:1;stroke:#081F5C;stroke-width:1.8}
.sk-panel.pathing .node.sel{stroke:#0B2A4A;stroke-width:2.8}
.sk-panel.hovering .nlabel.sel text{font-weight:750}
.nlabel{transition:opacity .18s ease}
.npct{transition:fill .15s ease}
.npct.flowpct{fill:#081F5C;font-weight:700}
.sk-panel.hovering .nlabel,.sk-panel.pathing .nlabel{opacity:.15}
.sk-panel.hovering .nlabel.on,.sk-panel.pathing .nlabel.on{opacity:1}
.flabel{opacity:0;transition:opacity .15s ease;pointer-events:none}
.flabel.always{opacity:.92}
.flabel.on{opacity:1}
.sk-panel.hovering .flabel.always,.sk-panel.pathing .flabel.always{opacity:.28}
.sk-panel.hovering .flabel.always.on,.sk-panel.pathing .flabel.always.on{opacity:1}
.ghost{font:600 11.5px/1 inherit;color:var(--muted);background:transparent;
border:1px dashed #C9BEA9;padding:6px 10px;border-radius:8px;cursor:pointer}
.ghost.on{background:#EAF1EE;border-style:solid;border-color:var(--accent);color:#1E4A46}
.flow-status{font-size:12px;color:var(--muted);min-height:22px;margin:2px 0 4px;font-weight:600;
letter-spacing:.01em;line-height:1.85;word-break:break-word}
.flow-status.live{color:var(--ink)}
#tip{position:fixed;z-index:9999;pointer-events:none;background:#12303A;color:#fff;
font:12px/1.55 "Microsoft YaHei",sans-serif;padding:8px 11px;border-radius:8px;max-width:340px;
white-space:pre-line;box-shadow:0 8px 24px rgba(8,31,92,.22)}
footer{margin-top:70px;padding:26px 0 60px;border-top:1px solid var(--rule);
font-size:11.6px;color:#8A9AA4;line-height:1.8}
@media (max-width:900px){.kpis,.takeaways,.grid2{grid-template-columns:1fr 1fr}
.actions{grid-template-columns:1fr 1fr;gap:24px}
h1{font-size:30px}}
@media (max-width:640px){.kpis,.takeaways,.grid2{grid-template-columns:1fr}
.actions{grid-template-columns:1fr;gap:16px}}
@media print{header.top,.dl,.seg{display:none}body{background:#fff}
.chart{break-inside:avoid}section{break-before:auto}.chart.wide .chart-wrap svg{min-width:0}
.chart.sankey{width:auto;margin-left:0;transform:none}}
"""

JS = """
const tip=document.getElementById('tip');
document.addEventListener('pointermove',e=>{
  const el=e.target.closest?e.target.closest('[data-tip]'):null;
  if(!el){tip.hidden=true;return;}
  tip.hidden=false;tip.textContent=el.getAttribute('data-tip');
  const p=14,r=tip.getBoundingClientRect();
  let x=e.clientX+p,y=e.clientY+p;
  if(x+r.width>innerWidth-8)x=e.clientX-r.width-p;
  if(y+r.height>innerHeight-8)y=e.clientY-r.height-p;
  tip.style.left=x+'px';tip.style.top=y+'px';
});
document.addEventListener('pointerleave',()=>{tip.hidden=true});
document.querySelectorAll('.seg button[data-seg]').forEach(b=>{
  b.addEventListener('click',()=>{
    const g=b.dataset.seg,v=b.dataset.val;
    document.querySelectorAll('.seg button[data-seg="'+g+'"]').forEach(x=>x.classList.toggle('on',x===b));
    document.querySelectorAll('[data-panel="'+g+'"]').forEach(p=>{p.hidden=p.dataset.val!==v});
  });
});
(function(){
  const status=document.getElementById('sk-status');
  const panels=[...document.querySelectorAll('.sk-panel')];
  const clearers=[];
  const STEPS=['第1步','第2步','第3步','第4步','第5步','第6步','第7步'];
  function init(panel){
    const flows=[...panel.querySelectorAll('.flow')];
    const nodes=[...panel.querySelectorAll('.node')];
    const labels=[...panel.querySelectorAll('.flabel')];
    const nlabels=[...panel.querySelectorAll('.nlabel')];
    const pcts=[...panel.querySelectorAll('.npct')];
    const sel=new Set();
    let timers=[];
    function stopTimers(){timers.forEach(clearTimeout);timers=[];}
    function resetPct(){
      pcts.forEach(t=>{t.textContent=t.dataset.share;t.classList.remove('flowpct');});
    }
    function setPct(step,pid,val){
      pcts.forEach(t=>{
        if(t.dataset.nstep===String(step)&&t.dataset.npid===pid){
          t.textContent=val;t.classList.add('flowpct');
        }
      });
    }
    function clear(){
      stopTimers();
      flows.forEach(f=>f.classList.remove('faded','on','lit'));
      labels.forEach(l=>l.classList.remove('on'));
      nodes.forEach(n=>n.classList.remove('on','sel'));
      nlabels.forEach(g=>g.classList.remove('on','sel'));
      resetPct();
      panel.classList.remove('hovering','pathing');
      if(status){status.textContent='';status.classList.remove('live');}
    }
    clearers.push(()=>{sel.clear();clear();});
    function markNode(step,pid,strong){
      nodes.forEach(n=>{
        if(n.dataset.step===String(step)&&n.dataset.pid===pid){
          n.classList.add('on');if(strong)n.classList.add('sel');
        }
      });
      nlabels.forEach(g=>{
        if(g.dataset.nstep===String(step)&&g.dataset.npid===pid){
          g.classList.add('on');if(strong)g.classList.add('sel');
        }
      });
    }
    /* keys: Set of "step|pid"；selected=true 表示点击锁定（可多选） */
    function focus(keys,selected){
      clear();
      if(!keys.size)return;
      panel.classList.add('hovering');
      keys.forEach(k=>{
        const i=k.indexOf('|');
        markNode(+k.slice(0,i),k.slice(i+1),true);
      });
      // 相连的非选中节点：取与所选节点之间最强的一条流量，显示它的占比
      const best=new Map();
      function note(key,rate,f){
        const cur=best.get(key);
        if(!cur||rate>cur.rate)best.set(key,{rate:rate,f:f});
      }
      flows.forEach(f=>{
        const st=Number(f.dataset.st);
        const sk=st+'|'+f.dataset.s, tk=(st+1)+'|'+f.dataset.t;
        const hs=keys.has(sk), ht=keys.has(tk);
        if(!hs&&!ht){f.classList.add('faded');return;}
        f.classList.add('on');
        const rate=parseFloat(f.dataset.rate)||0;
        if(hs&&!ht)note(tk,rate,f);
        if(ht&&!hs)note(sk,rate,f);
      });
      best.forEach((v,key)=>{
        const i=key.indexOf('|');
        markNode(+key.slice(0,i),key.slice(i+1),false);
        setPct(+key.slice(0,i),key.slice(i+1),v.f.dataset.rate);
      });
      if(status){
        status.classList.add('live');
        if(selected){
          status.textContent='已选 '+keys.size+' 个节点｜再点节点可取消，点空白处或按 Esc 退出';
        }else{
          const k=[...keys][0], i=k.indexOf('|');
          const st=+k.slice(0,i), pid=k.slice(i+1);
          const nd=nodes.find(n=>n.dataset.step===String(st)&&n.dataset.pid===pid);
          if(nd)status.textContent='聚焦 '+nd.dataset.name+'（第 '+st+' 步）｜来向 '+nd.dataset.in+' UV｜去向 '+nd.dataset.out+' UV';
        }
      }
    }
    nodes.forEach(nd=>{
      const key=nd.dataset.step+'|'+nd.dataset.pid;
      nd.addEventListener('pointerenter',()=>{
        if(sel.size===0)focus(new Set([key]),false);
      });
      nd.addEventListener('pointerleave',()=>{
        if(sel.size===0)clear();
      });
      nd.addEventListener('click',ev=>{
        ev.stopPropagation();
        if(sel.has(key))sel.delete(key);else sel.add(key);
        if(sel.size)focus(sel,true);else clear();
      });
    });
    function showPath(f,conv){
      sel.clear();
      clear();
      panel.classList.add('pathing');
      flows.forEach(x=>x.classList.add('faded'));
      const st0=Number(f.dataset.st);
      markNode(st0,f.dataset.s,true);
      f.classList.remove('faded');
      f.classList.add('lit');
      if(conv)f.classList.add('cv');
      const firstLb=panel.querySelector('.flabel[data-for="'+f.dataset.e+'"]');
      if(firstLb)firstLb.classList.add('on');
      const ids=((conv?f.dataset.pathc:f.dataset.path)||'').split(',').filter(Boolean);
      if(status){
        status.classList.add('live');
        // 链条按“节点 + 离开该节点的占比”排列，并标出步序：第一跳先写去向，避免漏掉第 2 步
        status.textContent=(conv?'转化最优路径：':'主干路径：')
          +STEPS[st0-1]+f.dataset.sname+' '+f.dataset.rate+' → '+STEPS[st0]+f.dataset.tname;
        if(!ids.length){
          status.textContent+=f.dataset.tname==='确认订单'?'（本跳即到达确认订单）':'（已到最后一步）';
        }
      }
      ids.forEach((id,i)=>{
        timers.push(setTimeout(()=>{
          const el=panel.querySelector('.flow[data-e="'+id+'"]');
          if(!el)return;
          el.classList.remove('faded');el.classList.add('lit');
          if(conv)el.classList.add('cv');
          const lb=panel.querySelector('.flabel[data-for="'+id+'"]');
          if(lb)lb.classList.add('on');
          if(status)status.textContent+=' '+el.dataset.rate+' → '+STEPS[Number(el.dataset.st)]+el.dataset.tname;
          markNode(Number(el.dataset.st)+1,el.dataset.t,false);
        },280*i+60));
      });
    }
    flows.forEach(f=>{
      f.addEventListener('click',ev=>{
        ev.stopPropagation();
        if(ev.detail>1)return;   // 双击时交给 dblclick，避免先闪一次主干路径
        showPath(f,false);
      });
      f.addEventListener('dblclick',ev=>{
        ev.stopPropagation();
        ev.preventDefault();
        showPath(f,true);
      });
    });
    panel.addEventListener('click',e=>{
      if(e.target.closest('.flow')||e.target.closest('.node'))return;
      sel.clear();clear();
    });
  }
  panels.forEach(init);
  document.addEventListener('keydown',e=>{if(e.key==='Escape')clearers.forEach(f=>f());});
  document.querySelectorAll('.seg button[data-seg="sk"]').forEach(b=>b.addEventListener('click',()=>clearers.forEach(f=>f())));
  document.querySelectorAll('[data-toggle="mini"]').forEach(b=>{
    b.addEventListener('click',()=>{
      const on=b.classList.toggle('on');
      document.querySelectorAll('.sk-panel').forEach(p=>p.classList.toggle('showall',on));
      clearers.forEach(f=>f());
    });
  });
})();
document.querySelectorAll('[data-dl]').forEach(b=>{
  b.addEventListener('click',()=>{
    const f=b.closest('figure'),svg=f.querySelector('svg');
    const s=new XMLSerializer().serializeToString(svg);
    const blob=new Blob(['<?xml version="1.0" encoding="UTF-8"?>\\n'+s],{type:'image/svg+xml'});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);
    a.download=(f.id||'chart')+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1500);
  });
});
"""

NAV = [("s1", "口径"), ("s2", "人群"), ("s3", "路径"), ("s4", "差异"),
       ("s5", "转化"), ("s6", "节奏"), ("s7", "结论")]

sankey_fig = f'''<figure class="chart sankey" id="sankey">
  <div class="chart-head">
    <div><h3>前 7 步路径：全量 / 未下单 / 已下单</h3>
    <p>色带＝该跳占来源页面的比例｜点击节点可多选并固定，只看所选节点的来向与去向｜单击色带：主干路径；双击色带：后续转化率最高、更早到达确认订单的路径</p></div>
    <div class="seg">
      <button class="on" data-seg="sk" data-val="all">全量</button>
      <button data-seg="sk" data-val="nonorder">未下单</button>
      <button data-seg="sk" data-val="order">已下单</button>
      <button class="ghost" data-toggle="mini" title="显示每步占比低于 1.6% 的细流">细流</button>
    </div>
  </div>
  <div class="flow-status" id="sk-status" aria-live="polite"></div>
  <div class="chart-wrap">
    <div class="sk-panel" data-panel="sk" data-val="all">{sankey_all}</div>
    <div class="sk-panel" data-panel="sk" data-val="nonorder" hidden>{sankey_n}</div>
    <div class="sk-panel" data-panel="sk" data-val="order" hidden>{sankey_o}</div>
  </div>
</figure>'''

def _gcell(g):
    nm = gname(g)
    disp = nm if len(nm) <= 22 else nm[:22] + "…"
    return (f"<span title=\"{esc(nm)}\">{esc(disp)}</span><br>"
            f"<code>{g['gid']}</code>")


goods_rows = "".join(
    f"<tr><td>{_gcell(g)}</td><td class='num'>{n(g['browse'])}</td>"
    f"<td class='num'>{n(g['order'])}</td><td class='num'>{pc(g['cvr'])}</td>"
    f"<td>{judge(g)}</td></tr>" for g in gt)

dict_rows = "".join(f"<tr><td><code>{i}</code></td><td>{nm}</td><td>{c}</td></tr>"
                    for i, nm, c in PAGE_TABLE)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>营销活动用户行为路径分析</title>
<style>{CSS}</style>
</head><body>
<header class="top"><div class="wrap topbar">
  <div class="brand">某医美平台 · 营销活动</div>
  <nav>{"".join(f'<a href="#{i}">{t}</a>' for i, t in NAV)}</nav>
</div></header>

<main class="wrap">
<div class="hero">
  <div class="eyebrow">行为路径诊断 · 观察期 41 天</div>
  <h1>营销活动用户行为路径分析</h1>
  <p class="lede">下单与未下单两组用户的差距，主要不在路径结构，而在同一路径上的转化强度：19.1pp 的确认订单率差距中，首跳去向解释 5.0pp，其余 14.1pp 来自进入商品详情页之后的购买决策。</p>

  <div class="kpis">
    <div class="kpi"><b>{n(M['uv_total'])}</b><span>访问 UV</span><em>用户标识＋访问日期去重</em></div>
    <div class="kpi"><b>{pc(M['share_order_uv'])}</b><span>下单用户占比</span><em>{n(M['uv_order'])} / {n(M['uv_total'])} UV</em></div>
    <div class="kpi"><b>{pc(M['share_confirm'])}</b><span>确认订单触达率</span><em>{n(M['uv_confirm'])} UV，同期结果</em></div>
    <div class="kpi"><b>{pc(M['goods_confirm_rate'])}</b><span>商详 → 确认订单</span><em>{n(M['uv_goods'])} → {n(M['goods_confirm_uv'])} UV</em></div>
  </div>

  <div class="takeaways">
    <div class="tk"><h3>① 结构只解释 1/4</h3><p>19.1pp 的确认订单率差距中，首跳去向解释 <b>5.0pp</b>（2.4–7.7pp），同一路径上的转化强度解释 <b>14.1pp</b>（11.4–16.7pp）。</p></div>
    <div class="tk"><h3>② 只有一个闸门</h3><p>进过商详的 UV 中 {pc(M['goods_confirm_rate'])} 触达确认订单；没进过商详的 {n(M['uv_nogoods'])} UV 里只有 <b>{M['nogoods_confirm']} 个</b>。</p></div>
    <div class="tk"><h3>③ 30 秒分水岭</h3><p>{pc(dshort['share'])} 的访问不到 30 秒，确认订单率仅 <b>{pc(dshort['confirm'],1)}</b>；停留 0.5–15 分钟升到 14%–15%。</p></div>
  </div>
</div>

<section id="s1">
  <h2><i>01</i>口径与方法</h2>
  <p class="sub">一份报告、三层人群、一个同期结果。所有路径指标都在「uv＝用户标识＋访问日期」这一层计算，避免把“人”和“这次访问”混在一起。</p>

  <table>
    <thead><tr><th>层</th><th>单位</th><th class="num">规模</th><th>用途</th></tr></thead>
    <tbody>
      <tr><td>L1 用户层</td><td>用户标识</td><td class="num">{n(M['user_total'])}</td><td>人群盘子：下单用户 {n(M['user_order'])} / 未下单 {n(M['user_nonorder'])}；每人仅 1 天记录，不做复访分析</td></tr>
      <tr><td>L2 访问层</td><td>用户标识＋日期</td><td class="num">{n(M['uv_total'])}</td><td><b>主分析层</b>：下单用户 {n(M['uv_order'])} / 未下单 {n(M['uv_nonorder'])}</td></tr>
      <tr><td>L3 结果层</td><td>UV 内是否触达确认订单页</td><td class="num">{n(M['uv_confirm'])}</td><td><b>同期、可归因的结果变量</b>，触达率 {pc(M['share_confirm'])}</td></tr>
    </tbody>
  </table>

  <details><summary>页面字典（功能类别汇总）</summary>
    <table><thead><tr><th>编号</th><th>页面名称</th><th>类别</th></tr></thead><tbody>{dict_rows}</tbody></table>
    <p style="font-size:12px;color:#7D8C95;margin-top:8px">早期报告曾把 29564 写作“我的订单详情”、21066 写作“抽奖结果页”、21065 写作“商品列表页”，与源表不一致，本报告全部改回源表名称。其余长尾页面合并为“其他页面”。</p>
  </details>
</section>

<section id="s2">
  <h2><i>02</i>人群规模与漏斗</h2>
  <p class="sub">人群口径和行为口径是两条平行轨道，不是一条嵌套漏斗——这一点决定了后面所有对比的读法。</p>
  {fig("funnel", "两条轨道：人群收缩 vs 同期行为", "上：按用户身份切；下：按当次访问行为切", chart_funnel(),
       "确认订单 UV 中 " + n(M['uv_confirm_in_nonorder']) + " 个不属于“期间下过单的用户”，因此不能把 3,677 与 2,022 画成上下级。")}
  <div class="note">漏斗最陡的一层是“访问 → 下单用户”（{pc(M['share_order_uv'])}），但这不是转化率，是人群占比；真正可归因的转化是“访问 → 确认订单”（{pc(M['share_confirm'])}），再往下一层“支付结果”只剩 {pc(M['share_pay'])}。</div>
</section>

<section id="s3">
  <h2><i>03</i>总体路径对比</h2>
  <p class="sub">三组共用同一套页面配色、同一个 7 步窗口、同一套节点顺序。先看全量确认整体形状，再切到未下单 / 已下单看差异；色带宽度是该跳占来源页面的比例，不是绝对 UV。</p>
  {sankey_fig}
  <ol>
    <li><b>第 2 步就分叉。</b>下单用户 {pc(a2o)} 继续访问，未下单只有 {pc(a2n)}；到第 7 步变成 {pc(a7o)} vs {pc(a7n)}。</li>
    <li><b>首跳构成其实很接近。</b>第 2 步去商品详情页 {pc(sk_item(M['sankey_order'],2,'V03')['share'])} vs {pc(sk_item(M['sankey_nonorder'],2,'V03')['share'])}，去新首页 {pc(sk_item(M['sankey_order'],2,'V02')['share'])} vs {pc(sk_item(M['sankey_nonorder'],2,'V02')['share'])}——起点相似，差距在后续每一步的留存被放大。</li>
    <li><b>未下单组更爱“原地打转”。</b>第 7 步仍有 {pc(sk_item(M['sankey_nonorder'],7,'V01')['share'])} 停在活动页，下单组是 {pc(sk_item(M['sankey_order'],7,'V01')['share'])}。</li>
  </ol>
</section>

<section id="s4">
  <h2><i>04</i>差异诊断</h2>
  <p class="sub">五个角度回答同一个问题：两组的差距究竟来自“去了哪”，还是“到了之后买不买”。</p>

  <div class="grid2">
    <div>{fig("radar", "六维差异一览", "各轴按两类最大值归一", chart_radar(), "")}</div>
    <div>
      <h3 style="margin-top:14px">读图</h3>
      <p>深度、时长、商详触达、确认订单四条轴，下单组都明显外扩；但<b>商品广度几乎重合</b>（1.53 vs 1.55 个/UV）。</p>
      <p>也就是说，下单人群并不是“看得更多”，而是<b>在商品页完成决策</b>。这条差异否定了“多推商品就能提升转化”的直觉。</p>
      <div class="note" style="margin-top:14px">奖品触达只有 +4.3pp，是六条轴里最弱的一条——抽奖侧行为并不是区分两类人的关键。</div>
    </div>
  </div>

  <h3>4.1 到达率：分叉发生在第 2 步</h3>
  {fig("arrival", "各步累计到达率", "分母为该组全部访问 UV；第 8–10 步为窗口截断区", chart_arrival(),
       "第 2 步差 " + pp(a2o-a2n) + "，第 7 步扩大到 " + pp(a7o-a7n) + "。曲线不会相交，说明差异是持续性的，不是某一步的偶发。")}

  <h3>4.2 页面触达：差异全部集中在商品域与交易域</h3>
  {fig("reach", "各页面 UV 触达率（按差值排序）", "灰点＝未下单，绿点＝下单用户；右列为差值与两侧水平", chart_reach(),
       "商详 " + pp(rd['商品详情页']['diff']) + "，而活动页 " + pp(rd.get('活动页', {'diff': 0})['diff']) + "、积分明细 " + pp(rd['积分明细']['diff']) + "、内容详情 " + pp(rd['内容详情']['diff']) + " 基本无差——差异不是“什么都更多”。")}

  <h3>4.3 首跳去向：{pc(dead_share)} 的流量走进“死口子”</h3>
  {fig("firstjump", "第 2 步去向 × 确认订单率", "虚线为全站均值 " + pc(M['share_confirm']), chart_first_jump(),
       "无第 2 步（" + pc(fj[0]['share']) + "）、原地留在活动页（22.9%）、去积分明细（8.7%）三类合计 " + pc(dead_share) + " 的流量，确认订单率都在 5.4% 以下；去商详/新首页/项目列表的 " + pc(good_share) + " 流量贡献了绝大部分订单。")}

  <h3>4.4 差异分解：结构只占 1/4</h3>
  {fig("waterfall", "19.1pp 差距的来源", "对称（Shapley）分解，范围为两种权重下的上下界", chart_waterfall(),
       "若以下单组为权重，结构效应 7.7pp、率效应 11.4pp；两种权重下结论一致：差距主要由“同一路径上的决策强度”驱动。")}

  <h3>4.5 深度与时长：浅层流量占一半</h3>
  <div class="grid2">
    <div>{fig("steps", "步数分布", "未下单 UV 的步数高度集中在前 3 步", chart_steps(), "")}</div>
    <div>{fig("dur", "停留时长与确认订单率", "柱＝UV 占比，线＝确认订单率", chart_dur(), "")}</div>
  </div>
  <div class="note"><b>30 秒分水岭：</b>{pc(dshort['share'])} 的访问在 30 秒内结束，确认订单率仅 {pc(dshort['confirm'],1)}；停留 0.5–15 分钟的访问升到 14%–15%，但超过 15 分钟后回落到 9% 左右（多为多任务挂着页面）。运营上，“在 2 分钟内把人送进商详”比“延长停留”更可执行。</div>
</section>

<section id="s5">
  <h2><i>05</i>转化分析</h2>
  <p class="sub">全站只有一个入口能通向订单。闸门之前的流量再多，只要没进商详，就不会产生订单。</p>

  <h3>5.1 商品级漏斗：同一个入口，转化率差 70 倍</h3>
  {fig("goods", "浏览 UV × 转化率（气泡＝确认订单 UV）", "仅展示浏览 UV ≥ 30 的 " + str(M['goods_n']) + " 个商品；标出关键商品的短名，悬停看全名与 UV", chart_goods(),
       "按商品聚合的加权转化 " + pc(M['goods_cvr_overall']) + "（同一 UV 浏览多个商品会重复计入），按 UV 计的整体转化是 " + pc(M['goods_confirm_rate']) + "。左上（低流量高转化）适合扩量，右下（高流量低转化）适合排查；商品名称已按浏览量降序编号脱敏。")}

  <table>
    <thead><tr><th>商品（ID）</th><th class="num">浏览 UV</th><th class="num">确认订单 UV</th><th class="num">转化率</th><th>判读</th></tr></thead>
    <tbody>{goods_rows}</tbody>
  </table>
  <p style="font-size:12px;color:#7D8C95">样本为浏览 UV ≥ 30 的商品；小于 50 UV 的商品转化率波动大，仅作参考。</p>
</section>

<section id="s6">
  <h2><i>06</i>时间节奏</h2>
  <p class="sub">流量大不等于订单多。日期和时段的转化率波动，比路径结构的差异更剧烈。</p>
  {fig("dates", "逐日 UV 与确认订单率", "柱＝当日访问 UV，线＝当日确认订单率（双轴独立缩放）", chart_dates(),
       "流量最大的 " + peak['d'][5:] + " 有 " + n(peak['uv']) + " UV，确认订单率只有 " + pc(peak['rate']) + "；而 " + best['d'][5:] + " 只有 " + n(best['uv']) + " UV，确认订单率达到 " + pc(best['rate']) + "。")}
  {fig("hours", "时段 UV 与确认订单率", "按首步访问时间归入小时", chart_hours(),
       "10 点与 22 点两个流量峰合计 " + n(peak_uv) + " UV（" + pc(peak_uv/M['uv_total']) + "），确认订单率都只有 " + pc(h10['rate']) + "，低于全站 " + pc(M['share_confirm']) + "；12–19 点合计 " + n(day_uv) + " UV，确认订单率 " + pc(day_rate) + "。")}
  <div class="note"><b>高量低质：</b>10 点（{n(h10['uv'])} UV）、22 点（{n(h22['uv'])} UV）两个峰，与 9/26、10/25 两个大流量日，都呈现“UV 高、确认订单率低”的特征，典型是集中推送带来的浅层访问。把这类流量单独打标再评估活动效果，会比总量指标可靠。</div>
</section>

<section id="s7">
  <h2><i>07</i>结论与行动</h2>

  <ol>
    <li><b>差异在强度，不在结构。</b>把更多人导到商详，最多回收 2.4–7.7pp；让已经在商详的人下单，空间是 11.4–16.7pp。</li>
    <li><b>商详是唯一闸门。</b>{n(M['uv_nogoods'])} 个没进商详的 UV 只产生 {M['nogoods_confirm']} 个确认订单，任何绕过商详的路径几乎都不会产生订单。</li>
    <li><b>流量质量的时间波动被低估。</b>大流量日的确认订单率只有均值的 1/3 到 1/2，用总量评估会高估活动效果。</li>
  </ol>

  <div class="actions">
    <div class="act"><h4>产品</h4><ul>
      <li>活动页首屏增加商品直达入口，缩短进入商详的路径</li>
      <li>商详页补充价格、资质、评价等决策信息</li>
      <li>调整积分与奖品入口位置，降低对商品页的分流</li>
    </ul></div>
    <div class="act"><h4>运营</h4><ul>
      <li>排查高浏览、低转化的商品，优先优化商品详情与定价</li>
      <li>对高转化商品加大曝光与推荐权重</li>
      <li>大流量时段的推送内容与商品权益结合，而非单一奖励</li>
    </ul></div>
  </div>

  <div class="warn"><b>待验证假设：</b>“商详决策力不足”目前只能从路径差异推断，缺少价格、评价、库存等页面要素数据；需要 A/B 或页面要素埋点才能证实，不能据此直接归因。</div>
</section>

<footer>
  <div>营销活动用户行为路径分析 · 脱敏版</div>
  <div>数据来源：全量行为日志（表A）（{n(M['rows_v'])} 行）、下单用户行为日志（表B）（{n(M['rows_o'])} 行）｜ UV＝用户标识＋访问日期 ｜ 前 10 步 ｜ 数据周期 41 天</div>
  <div>本报告为自包含 HTML，可离线打开；每张图右上角可下载 SVG，便于贴入 Word。</div>
</footer>
</main>
<div id="tip" hidden></div>
<script>{JS}</script>
</body></html>"""

open(OUT, "w", encoding="utf-8").write(HTML)
print("written", OUT, round(len(HTML)/1024, 1), "KB")
