# 数据字典（report_data.json）

所有字段均已脱敏并模拟化：商品名 → 商品A/B/C…，商品 ID → P01…，主要页面 ID → V01…V12，长尾页面 ID → L01…，日期 → D01…；数值经过 ±3% 扰动，仅保留分布形状。

## 顶层规模指标

| 字段 | 含义 |
|---|---|
| uv_total / uv_order / uv_nonorder | 访问 UV 总数 / 下单用户 UV / 未下单 UV |
| uv_confirm / uv_pay | 触达确认订单页 / 支付结果页的 UV |
| user_total / user_order / user_nonorder | 用户层数量（用户标识去重） |
| start_uv | 首步为活动页的 UV |
| share_confirm / share_pay / share_order_uv | 对应占比（分母 uv_total） |
| goods_confirm_rate | 商详 → 确认订单转化率（按 UV） |
| uv_goods / goods_confirm_uv | 进过商详的 UV / 其中触达确认订单的 UV |
| uv_nogoods / nogoods_confirm | 未进商详的 UV / 其中触达确认订单的数量 |
| censor10_all / censor10_order | 第 10 步截断占比 |

## kitagawa（差异分解）

`base_nonorder` / `target_order`：两组确认订单率；`delta`：差距；
`struct_a/struct_b`、`rate_a/rate_b`：两种权重下的结构效应与率效应；
`struct_shapley` / `rate_shapley`：对称分解结果。

## 列表型数据

| 字段 | 结构 |
|---|---|
| arrival | [{step, all, order, nonorder}] 各步累计到达率 |
| first_jump | [{pid, share, confirm, uv}] 第 2 步去向构成 |
| steps_bucket / dur_bucket | 步数分布 / 停留时长分桶（share、confirm） |
| reach | [{pid, name, order, nonorder, diff, uv_total}] 页面触达率 |
| dates / hours | [{d/h, uv, confirm, rate}] 逐日 / 分时指标 |
| radar | [{axis, order, nonorder, max, unit}] 六维对比 |
| goods | [{gid, name, browse, order, cvr}] 商品级漏斗（gid=P01…） |

## 桑基图数据（sankey_all / sankey_nonorder / sankey_order）

```
{
  steps: 7,
  nodes: [{step, total, items: [{pid, share, uv, name}]}],   # pid = V01…
  edges: [[{s, t, n}]]                                        # 按 si-1 索引
}
```

- `pid`：页面编号（V01 活动页 … V12 H5，见报告页面字典）
- `share`：该步 UV 占比；`n`：跳转 UV 数
