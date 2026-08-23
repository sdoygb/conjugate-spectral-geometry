#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉘ (P0 修复版)：66 国历年贸易矩阵聚合 v2 —— 修复德国代码映射 bug
================================================================
Bug 修复: country_codes 里 DEU 有两行 (276=Germany, 280=Fed.Rep.Germany...1990),
  dict(zip()) 时 280 覆盖 276 → DEU=280, 但 V202501/V202601 数据里德国=276
  → 德国 30 年贸易全零 (probe27 缺陷)。修复: 强制 DEU=276 (数据内实际 code)。

数据: BACI HS92 V202501 (1995-2023) + HS12 V202601 (2024)
  66 国 = WVS Wave 7 国家列表; 台湾 TWN → BACI 490; NIR/PRI 无 BACI 代码 → 剔除
  边权 = 双向合计 (千美元)
输出:
  baci_66_yearly_v2.csv     : 64 活跃节点逐年对称矩阵 (稀疏, year,i,j,v)
  baci_66_trajectory_v2.csv : 30 年全图/核心图 λ₂, BR (64 节点, 无孤立)
  probe28_results.json      : 汇总 + 校验 + 新旧对比
"""
import pandas as pd
import numpy as np
import json, os, sys, time

DL = '/Users/oygb/Downloads'
HS92 = f'{DL}/BACI_HS92_V202501'
HS12 = f'{DL}/BACI_HS12_V202601'
OUT = '.'

t0 = time.time()

def load_codes(path, fix_deu=True):
    codes = pd.read_csv(path)
    d = dict(zip(codes.country_iso3.str.upper(), codes.country_code))
    if fix_deu:
        d['DEU'] = 276   # 数据内实际 code (V202501 & V202601 均为 276)
    return d

iso3_92 = load_codes(f'{HS92}/country_codes_V202501.csv')
iso3_12 = load_codes(f'{HS12}/country_codes_V202601.csv')
iso3_92['TWN'] = 490
iso3_12['TWN'] = 490

# ---------- 66 国 (WVS7) ----------
wvs = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', usecols=['B_COUNTRY_ALPHA'])
ctrys66 = sorted(set(wvs['B_COUNTRY_ALPHA'].str.strip().str.upper()))
c66_iso3 = list(ctrys66)
c66_code92 = [iso3_92.get(c) for c in ctrys66]
c66_code12 = [iso3_12.get(c) for c in ctrys66]
missing = [c for c in ctrys66 if c not in iso3_92]
print(f'[wvs] 66 国, 无 BACI 代码: {missing}', flush=True)

# 活跃节点: 在 92 或 12 中有代码
active_idx = [i for i, c in enumerate(c66_code92) if c is not None]
c_iso_active = [c66_iso3[i] for i in active_idx]
c_code_active = [c66_code92[i] for i in active_idx]
N = len(active_idx)
print(f'[active] {N} 节点: {c_iso_active}', flush=True)
idx92 = {c66_code92[i]: k for k, i in enumerate(active_idx)}
idx12 = {c66_code12[i]: k for k, i in enumerate(active_idx)}
set92 = set(c66_code92[i] for i in active_idx)
set12 = set(c66_code12[i] for i in active_idx)

def agg_year(y):
    if y <= 2023:
        p = f'{HS92}/BACI_HS92_Y{y}_V202501.csv'
        cset, idx = set92, idx92
    else:
        p = f'{HS12}/BACI_HS12_Y2024_V202601.csv'
        cset, idx = set12, idx12
    df = pd.read_csv(p, usecols=['i', 'j', 'v'],
                     dtype={'i': 'int32', 'j': 'int32', 'v': 'float32'})
    df = df[df['i'].isin(cset) & df['j'].isin(cset)]
    g = df.groupby(['i', 'j'])['v'].sum()
    M = np.zeros((N, N), dtype='float64')
    for (i, j), v in g.items():
        a, b = idx[i], idx[j]
        M[a, b] += v
        M[b, a] += v
    return M

def metrics(M):
    deg = M.sum(axis=1)
    tot = float(deg.sum())
    mx = float(M.max())
    Mn = M / mx if mx > 0 else M
    Ln = np.diag(Mn.sum(axis=1)) - Mn
    evn = np.sort(np.linalg.eigvalsh(Ln))
    l2 = float(evn[1])
    evA = np.sort(np.linalg.eigvalsh(Mn))
    br = float(sum(abs(evA[i] + evA[N - 1 - i]) for i in range(N // 2)) / (N // 2))
    return l2, br, int((deg > 0).sum()), tot, mx

def core_metrics(M, topk=None, tau=None):
    mx = M.max()
    if mx <= 0:
        return dict(l2=0.0, br=0.0, nedge=0, wshare=0.0)
    W = M / mx
    tot_w = W.sum() / 2
    if topk is not None:
        flat = np.triu(W, 1).flatten()
        pos = flat[flat > 0]
        thr = np.sort(pos)[-topk] if len(pos) >= topk else 0.0
        mask = np.triu(W, 1) >= thr
    else:
        mask = np.triu(W, 1) >= tau
    Wc = np.where(mask | mask.T, W, 0.0)
    nedge = int((np.triu(Wc, 1) > 0).sum())
    wshare = float(Wc.sum() / 2 / tot_w) if tot_w > 0 else 0.0
    deg = Wc.sum(axis=1)
    L = np.diag(deg) - Wc
    ev = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev[1])
    evA = np.sort(np.linalg.eigvalsh(Wc))
    br = float(sum(abs(evA[i] + evA[N - 1 - i]) for i in range(N // 2)) / (N // 2))
    return dict(l2=l2, br=br, nedge=nedge, wshare=wshare)

# ---------- 主循环 ----------
years = list(range(1995, 2025))
rows = []
mat_store = {}
for y in years:
    M = agg_year(y)
    mat_store[y] = M
    l2, br, active, tot, mx = metrics(M)
    t100 = core_metrics(M, topk=100)
    t150 = core_metrics(M, topk=150)
    t02 = core_metrics(M, tau=0.02)
    rows.append(dict(year=y, active=active, tot=tot, max_edge=mx,
                     l2_full=l2, br_full=br,
                     l2_top100=t100['l2'], br_top100=t100['br'], nedge100=t100['nedge'], wshare100=t100['wshare'],
                     l2_top150=t150['l2'], br_top150=t150['br'], nedge150=t150['nedge'],
                     l2_tau02=t02['l2'], br_tau02=t02['br'], nedge02=t02['nedge'], wshare02=t02['wshare']))
    print(f'  {y}: active={active} l2_full={l2:.6f} br_full={br:.6f} '
          f'l2_top100={t100["l2"]:.6f} br_top100={t100["br"]:.6f} ({time.time()-t0:.0f}s)', flush=True)

traj = pd.DataFrame(rows)
traj.to_csv(f'{OUT}/baci_66_trajectory_v2.csv', index=False)

# ---------- 稀疏矩阵 ----------
sp = []
for y in years:
    M = mat_store[y]
    for i in range(N):
        for j in range(i + 1, N):
            v = M[i, j]
            if v > 0:
                sp.append((y, c_code_active[i], c_code_active[j], v))
spdf = pd.DataFrame(sp, columns=['year', 'i', 'j', 'v'])
spdf.to_csv(f'{OUT}/baci_66_yearly_v2.csv', index=False)
print(f'[ok] baci_66_yearly_v2.csv: {len(spdf)} rows', flush=True)

# ---------- 校验 ----------
m24 = mat_store[2024]
ci, ti, ui = idx92[156], idx92[490], idx92[842]
print(f'[校验] 2024 CN-TW = {m24[ci, ti]/1e5:.2f} 亿美元 (6节点 1902.80)', flush=True)
print(f'[校验] 2024 CN-US = {m24[ci, ui]/1e5:.2f} 亿美元 (6节点 6007.9?)', flush=True)
m23 = mat_store[2023]
di = idx92[276]
print(f'[校验] 2023 DEU 总边权 = {m23[di].sum()/1e5:.2f} 亿美元 (修复后应非零)', flush=True)
print(f'[校验] 2024 CN-DEU = {m24[ci, di]/1e5:.2f} 亿美元', flush=True)

res = dict(
    n_countries=len(ctrys66), active_nodes=N, iso3=c_iso_active, codes=c_code_active,
    missing_no_baci_code=missing, years=years,
    trajectory=rows,
    bug_fix='DEU 强制 276 (V202501/V202601 数据实际 code); probe27 用 280 导致德国 30 年全零',
    check_cn_tw_2024_100mUSD=round(m24[ci, ti] / 1e5, 2),
    check_cn_us_2024_100mUSD=round(m24[ci, ui] / 1e5, 2),
    check_deu_2023_total_100mUSD=round(m23[di].sum() / 1e5, 2),
    note='64 活跃节点 (剔除 NIR/PRI); 边权=双向合计千美元; 归一化=除以当年最大边'
)
json.dump(res, open(f'{OUT}/probe28_results.json', 'w'), ensure_ascii=False, indent=1)
print(f'[done] {time.time()-t0:.0f}s total', flush=True)
