#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉝：全球三流长周期检验——货物流 × 信息流 × 制度流（1948-2024）
- 货物流：IMF DOTS 64 国贸易总量（代理全球，dots_64_trajectory.csv）
- 制度流：WTO RTA-IS 全球累计生效 RTA 数量（/tmp/wto_rta_all.xlsx，1948-2024）
- 信息流：世界银行全球居民专利申请 IP.PAT.RESD（1985-2021）+ WIPO 2022-2024 总申请补
检验预言 10.78.7.01 的全球版：三流是否全球长周期协同（全通道耦合）
"""
import openpyxl, numpy as np, json, csv
from collections import defaultdict

# ---------- 1. 制度流：全球累计生效 RTA ----------
wb = openpyxl.load_workbook('/tmp/wto_rta_all.xlsx', read_only=True, data_only=True)
ws = wb['AllRTAs']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}

eff = defaultdict(int); inact = defaultdict(int)
n_force = 0; n_inactive = 0; n_other = 0
for r in rows[1:]:
    st = r[idx['Status']]
    if st not in ('In Force', 'In force for at least one Party', 'Inactive'):
        n_other += 1; continue
    eif = r[idx['Date of Entry into Force (G)']]
    if not eif: continue
    y = int(eif.year); eff[y] += 1
    if st == 'Inactive':
        n_inactive += 1
        inact_d = r[idx['Inactive Date']]
        if inact_d: inact[int(inact_d.year)] += 1
    else:
        n_force += 1

cum_rta = {}
c = 0
for y in range(1948, 2025):
    c += eff.get(y, 0) - inact.get(y, 0)
    cum_rta[y] = c
print(f"RTA: 生效中 {n_force}, 已失效 {n_inactive}, 其他 {n_other}; 2024 累计生效 {cum_rta[2024]}")

# ---------- 2. 货物流：64 国贸易总量 ----------
trade = {}
with open('gpu_spectra/society/dots_64_trajectory.csv') as f:
    for row in csv.DictReader(f):
        trade[int(row['year'])] = float(row['total'])

# ---------- 3. 信息流：全球专利（世界银行 RESD 1985-2021 + WIPO 总申请 2022-24）----------
pat = {}  # 全球居民申请（千件）
with open('gpu_spectra/society/probe33_patents_long.json') as f:
    pj = json.load(f)
for y, v in pj.items():
    if v.get('resd'): pat[int(y)] = v['resd'] / 1000.0

years = sorted(set(trade.keys()) & set(cum_rta.keys()))
print(f"货物流+制度流对齐: {years[0]}-{years[-1]} ({len(years)} 年)")
pyears = sorted(pat.keys())
print(f"信息流: {pyears[0]}-{pyears[-1]} ({len(pyears)} 年)")

# ---------- 4. 三流相关（重叠期 1985-2023） ----------
overlap = sorted(set(years) & set(pat.keys()) & set(cum_rta.keys()))
print(f"三流重叠期: {overlap[0]}-{overlap[-1]} ({len(overlap)} 年)")

def corr(xs, ys):
    x = np.array(xs, float); y = np.array(ys, float)
    return float(np.corrcoef(x, y)[0, 1])

T = [trade[y] for y in overlap]
R = [cum_rta[y] for y in overlap]
P = [pat[y] for y in overlap]
# 取对数（三流都是量级增长）
logT = np.log(T); logR = np.log(np.array(R)+1e-9); logP = np.log(P)

print("\n=== 水平值相关 ===")
print(f"贸易×RTA:  r={corr(T,R):.4f}")
print(f"贸易×专利: r={corr(T,P):.4f}")
print(f"RTA×专利:  r={corr(R,P):.4f}")
print("\n=== 对数相关 ===")
print(f"log贸易×logRTA:  r={corr(logT,logR):.4f}")
print(f"log贸易×log专利: r={corr(logT,logP):.4f}")
print(f"logRTA×log专利:  r={corr(logR,logP):.4f}")

# ---------- 5. 领先-滞后（制度流先行？） ----------
# 用重叠期算：RTA 对贸易的领先相关（RTA_t 与 贸易_{t+k}）
print("\n=== 领先-滞后：RTA(制度) vs 贸易(物质) ===")
for lag in range(-5, 6):
    if lag >= 0:
        # RTA_t 领先贸易 lag 年：corr(RTA[:-lag], trade[lag:])
        r_ = corr(R[:len(R)-lag] if lag>0 else R, T[lag:] if lag>0 else T)
    else:
        r_ = corr(R[-lag:], T[:len(T)+lag])
    print(f"lag={lag:+d}: r={r_:.4f}")

# ---------- 6. 阶段均值（制度/贸易/专利的五阶段） ----------
stages = {'1948-1960': (1948,1960), '1961-1980': (1961,1980),
          '1981-2000': (1981,2000), '2001-2011': (2001,2011), '2012-2023': (2012,2023)}
print("\n=== 阶段均值（相对各自 1948/1985 基期） ===")
t0 = trade[1948]; r0 = cum_rta[1948] if cum_rta[1948]>0 else 1
for name, (a, b) in stages.items():
    ty = [trade[y]/t0 for y in range(a, b+1) if y in trade]
    ry = [cum_rta[y]/r0 for y in range(a, b+1) if y in cum_rta]
    py_ = [pat[y] for y in range(a, b+1) if y in pat]
    print(f"{name}: 贸易×{np.mean(ty):.1f}  RTA×{np.mean(ry):.1f}  专利={np.mean(py_):.0f}千件" if py_ else f"{name}: 贸易×{np.mean(ty):.1f}  RTA×{np.mean(ry):.1f}")

# ---------- 7. 输出 ----------
out = {'overlap': overlap, 'trade': {y: trade[y] for y in overlap},
       'rta': {y: cum_rta[y] for y in overlap}, 'patent': {y: pat[y] for y in overlap}}
with open('gpu_spectra/society/probe33_three_flows.json', 'w') as f:
    json.dump(out, f, indent=1)
print("\n已存 probe33_three_flows.json")
