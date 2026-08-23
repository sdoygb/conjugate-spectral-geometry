#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉗ (P0)：66 国历年贸易矩阵聚合 + 阈值化核心图 → 30 年谱轨迹
================================================================
数据: BACI HS92 V202501 (1995-2023) + HS12 V202601 (2024)
  66 国 = WVS Wave 7 国家列表 (探针⑰/⑮ 同源)
  台湾 TWN → BACI 490 (Other Asia, nes, S19); PRI/NIR 无 BACI 独立代码 → 全零节点
  边权 = 双向合计 (千美元)
输出:
  baci_66_yearly.csv       : 66 国逐年对称矩阵 (稀疏, year,i,j,v)
  baci_66_trajectory.csv   : 30 年全图/核心图 λ₂, BR, 活跃节点, 边数
  probe27_results.json     : 汇总结果
"""
import pandas as pd
import numpy as np
import json, os, sys, time

DL = '/Users/oygb/Downloads'
HS92 = f'{DL}/BACI_HS92_V202501'
HS12 = f'{DL}/BACI_HS12_V202601'
OUT = '.'

t0 = time.time()
codes = pd.read_csv(f'{DL}/BACI_HS22_V202601/country_codes_V202601.csv')
iso3_to_code = dict(zip(codes.country_iso3.str.upper(), codes.country_code))
iso3_to_code['TWN'] = 490   # 台湾 = BACI 'Other Asia, nes' (S19), CEPII 标准

# ---------- 66 国 (WVS7) ----------
wvs = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', usecols=['B_COUNTRY_ALPHA'])
ctrys66 = sorted(set(wvs['B_COUNTRY_ALPHA'].str.strip().str.upper()))
c66_iso3 = list(ctrys66)
c66_code = [iso3_to_code.get(c) for c in ctrys66]
c66_set = set(c for c in c66_code if c is not None)
missing = [c for c in ctrys66 if c not in iso3_to_code]
print(f'[wvs] 66 国: {len(ctrys66)}, BACI 可映射: {len(c66_set)}, 全零: {missing}', flush=True)
idx = {code: i for i, code in enumerate(c66_code)}
N = len(c66_code)

def path_of(y):
    if y <= 2023:
        return f'{HS92}/BACI_HS92_Y{y}_V202501.csv'
    return f'{HS12}/BACI_HS12_Y2024_V202601.csv'

def agg_year(y):
    p = path_of(y)
    df = pd.read_csv(p, usecols=['i', 'j', 'v'],
                     dtype={'i': 'int32', 'j': 'int32', 'v': 'float32'})
    df = df[df['i'].isin(c66_set) & df['j'].isin(c66_set)]
    g = df.groupby(['i', 'j'])['v'].sum()
    M = np.zeros((N, N), dtype='float64')
    for (i, j), v in g.items():
        M[idx[i], idx[j]] += v
        M[idx[j], idx[i]] += v
    return M

def metrics(M):
    n = M.shape[0]
    deg = M.sum(axis=1)
    active = int((deg > 0).sum())
    tot = float(deg.sum())
    mx = float(M.max())
    # 归一化 (除以最大边)
    Mn = M / mx if mx > 0 else M
    Ln = np.diag(Mn.sum(axis=1)) - Mn
    evn = np.sort(np.linalg.eigvalsh(Ln))
    l2 = float(evn[1]) if n > 1 else 0.0
    evAn = np.sort(np.linalg.eigvalsh(Mn))
    br = float(sum(abs(evAn[i] + evAn[n-1-i]) for i in range(n//2)) / (n//2))
    return l2, br, active, tot, mx

def core_metrics(M, tau=None, topk=None):
    """阈值化核心图: 归一化后保留边 ≥ tau 或 top-k 大边"""
    n = M.shape[0]
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
    l2 = float(ev[1]) if n > 1 else 0.0
    evA = np.sort(np.linalg.eigvalsh(Wc))
    br = float(sum(abs(evA[i] + evA[n-1-i]) for i in range(n//2)) / (n//2))
    return dict(l2=l2, br=br, nedge=nedge, wshare=wshare)

# ---------- 主循环 ----------
years = list(range(1995, 2025))
rows_traj = []
mat_store = {}
for y in years:
    M = agg_year(y)
    mat_store[y] = M
    l2, br, active, tot, mx = metrics(M)
    c02 = core_metrics(M, tau=0.02)
    c05 = core_metrics(M, tau=0.05)
    c10 = core_metrics(M, tau=0.10)
    tk100 = core_metrics(M, topk=100)
    rows_traj.append(dict(year=y, active=active, tot=tot, max_edge=mx,
                          l2_full=l2, br_full=br,
                          l2_core02=c02['l2'], br_core02=c02['br'], nedge02=c02['nedge'], wshare02=c02['wshare'],
                          l2_core05=c05['l2'], br_core05=c05['br'], nedge05=c05['nedge'],
                          l2_core10=c10['l2'], br_core10=c10['br'], nedge10=c10['nedge'],
                          l2_top100=tk100['l2'], br_top100=tk100['br'], wshare100=tk100['wshare']))
    print(f'  {y}: active={active} l2_full={l2:.5f} br_full={br:.5f} l2_c02={c02["l2"]:.5f} '
          f'({time.time()-t0:.0f}s)', flush=True)

traj = pd.DataFrame(rows_traj)
traj.to_csv(f'{OUT}/baci_66_trajectory.csv', index=False)

# ---------- 稀疏矩阵存储 ----------
sp_rows = []
for y in years:
    M = mat_store[y]
    for i in range(N):
        for j in range(i+1, N):
            v = M[i, j]
            if v > 0:
                sp_rows.append((y, c66_code[i], c66_code[j], v))
sp = pd.DataFrame(sp_rows, columns=['year', 'i', 'j', 'v'])
sp.to_csv(f'{OUT}/baci_66_yearly.csv', index=False)
print(f'[ok] baci_66_yearly.csv: {len(sp)} rows', flush=True)

# ---------- 校验 ----------
m24 = mat_store[2024]
ci, ti = idx[156], idx[490]
cn_tw_24 = m24[ci, ti] / 1e5
m23 = mat_store[2023]
cn_us_23 = m23[idx[156], idx[842]] / 1e5
print(f'[校验] 2024 CN-TW = {cn_tw_24:.2f} 亿美元 (6节点 1902.80)', flush=True)
print(f'[校验] 2023 CN-US = {cn_us_23:.2f} 亿美元 (6节点 5898.34)', flush=True)

# ---------- 汇总 ----------
res = dict(
    n_countries=N, iso3=c66_iso3, codes=c66_code,
    missing_no_baci_code=missing,
    years=years,
    trajectory=rows_traj,
    check_cn_tw_2024_100mUSD=round(cn_tw_24, 2),
    check_cn_us_2023_100mUSD=round(cn_us_23, 2),
    note='边权=双向合计千美元; 归一化=除以当年最大边; core02=阈值0.02核心图; top100=保留100大边'
)
json.dump(res, open(f'{OUT}/probe27_results.json', 'w'), ensure_ascii=False, indent=1)
print(f'[done] {time.time()-t0:.0f}s total', flush=True)
