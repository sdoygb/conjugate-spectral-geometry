#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉛ (P1 长周期回溯)：IMF DOTS 1948-2023 全球贸易耦合长周期谱轨迹
================================================================
数据: ~/Downloads/IMF_DOT.csv (World Bank Data360 镜像, SDMX 展平)
      INDICATOR: IMF_DOT_TXG_FOB_USD = 出口 FOB
方法: 64 国 (probe28 名单) 逐年双边矩阵 → 边权=双向出口 max(对称化)
      → 归一化(当年最大边) → top100 核心 → GCC → λ₂/BR (probe29 逻辑)
输出: dots_64_trajectory.csv + probe31_results.json
向量化: 无逐行循环 (groupby 聚合)
"""
import pandas as pd
import numpy as np
import json

DOT = '/Users/oygb/Downloads/IMF_DOT.csv'

ISO3_64 = ['AND','ARG','ARM','AUS','BGD','BOL','BRA','CAN','CHL','CHN','COL','CYP','CZE',
           'DEU','ECU','EGY','ETH','GBR','GRC','GTM','HKG','IDN','IND','IRN','IRQ','JOR',
           'JPN','KAZ','KEN','KGZ','KOR','LBN','LBY','MAC','MAR','MDV','MEX','MMR','MNG',
           'MYS','NGA','NIC','NLD','NZL','PAK','PER','PHL','ROU','RUS','SGP','SRB','SVK',
           'THA','TJK','TUN','TUR','TWN','UKR','URY','USA','UZB','VEN','VNM','ZWE']
TARGET = set(ISO3_64)

import json
LABEL2ISO = json.load(open('dots_label2iso.json'))

def strip_label(lbl):
    return lbl.replace('Counterpart: ', '') if lbl.startswith('Counterpart: ') else lbl

print('[1/3] 读取 + 向量化映射...', flush=True)
print('[1/3] 读取 + 向量化映射...', flush=True)
frames = []
unmatched = set()
chunks = pd.read_csv(DOT, usecols=['REF_AREA', 'COMP_BREAKDOWN_1', 'COMP_BREAKDOWN_1_LABEL',
                                   'INDICATOR', 'TIME_PERIOD', 'OBS_VALUE'],
                     chunksize=1000000)
for ci, ch in enumerate(chunks):
    ch = ch[ch['INDICATOR'] == 'IMF_DOT_TXG_FOB_USD']
    ch = ch.dropna(subset=['COMP_BREAKDOWN_1', 'OBS_VALUE', 'TIME_PERIOD'])
    ch['ISO_P'] = ch['COMP_BREAKDOWN_1_LABEL'].map(strip_label).map(LABEL2ISO)
    unmatched |= set(ch.loc[ch['ISO_P'].isna(), 'COMP_BREAKDOWN_1_LABEL'].map(strip_label).unique())
    ch = ch.dropna(subset=['ISO_P'])
    ch = ch[ch['REF_AREA'].isin(TARGET) & ch['ISO_P'].isin(TARGET)]
    frames.append(ch[['REF_AREA', 'ISO_P', 'TIME_PERIOD', 'OBS_VALUE']])
    print(f'  chunk {ci}: {len(ch)} 行', flush=True)

df = pd.concat(frames, ignore_index=True)
df['TIME_PERIOD'] = df['TIME_PERIOD'].astype(int)
df['OBS_VALUE'] = df['OBS_VALUE'].astype(float)
df = df[df['OBS_VALUE'] >= 0]
print(f'  总记录: {len(df)}; 未匹配 label {len(unmatched)}:', sorted(unmatched)[:8], flush=True)

print('[2/3] groupby 聚合 + 矩阵...', flush=True)
# 边权 = max(双向出口), 对称化
g = df.groupby(['REF_AREA', 'ISO_P', 'TIME_PERIOD'])['OBS_VALUE'].max().reset_index()
# 排序使 (min,max) 一致
g['a'] = g[['REF_AREA', 'ISO_P']].min(axis=1)
g['b'] = g[['REF_AREA', 'ISO_P']].max(axis=1)
g = g[g['a'] != g['b']]
g = g.groupby(['a', 'b', 'TIME_PERIOD'])['OBS_VALUE'].max().reset_index()

idx = {c: k for k, c in enumerate(ISO3_64)}
N = len(ISO3_64)
years = sorted(g['TIME_PERIOD'].unique())
print(f'  年份: {years[0]}-{years[-1]} ({len(years)} 年); 边数: {g.shape[0]}', flush=True)

# 稀疏存储: (i,j) -> {year: v}
edge_vals = {}
for a, b, y, v in g.itertuples(index=False):
    i, j = idx[a], idx[b]
    edge_vals.setdefault((min(i, j), max(i, j)), {})[y] = max(
        edge_vals.get((min(i, j), max(i, j)), {}).get(y, 0.0), v)

print('[3/3] 逐年谱指标...', flush=True)

def gcc_of(W):
    n = W.shape[0]
    seen = np.zeros(n, bool)
    comps = []
    for s in range(n):
        if seen[s]:
            continue
        stack = [s]; seen[s] = True; comp = []
        while stack:
            u = stack.pop(); comp.append(u)
            for v in np.nonzero(W[u] > 0)[0]:
                if not seen[v]:
                    seen[v] = True; stack.append(v)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    gcc = comps[0]
    return W[np.ix_(gcc, gcc)], [ISO3_64[i] for i in gcc], len(comps)

def metrics_sub(W):
    n = W.shape[0]
    mx = W.max()
    if mx <= 0 or n < 2:
        return dict(l2=0.0, br=0.0, n=n)
    Wn = W / mx
    L = np.diag(Wn.sum(axis=1)) - Wn
    ev = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev[1])
    evA = np.sort(np.linalg.eigvalsh(Wn))
    br = float(sum(abs(evA[i] + evA[n - 1 - i]) for i in range(n // 2)) / (n // 2))
    return dict(l2=l2, br=br, n=n)

def core_topk(M, topk=100):
    mx = M.max()
    if mx <= 0:
        return M, mx
    W = M / mx
    flat = np.triu(W, 1).flatten()
    pos = flat[flat > 0]
    thr = np.sort(pos)[-topk] if len(pos) >= topk else 0.0
    mask = np.triu(W, 1) >= thr
    return np.where(mask | mask.T, W, 0.0), mx

rows = []
missing_years = []
for y in years:
    M = np.zeros((N, N))
    for (i, j), d in edge_vals.items():
        v = d.get(y)
        if v is not None:
            M[i, j] = v
            M[j, i] = v
    if M.max() <= 0:
        missing_years.append(y)
        continue
    Wc, mx = core_topk(M, topk=100)
    Wg, gcc_list, ncomp = gcc_of(Wc)
    m = metrics_sub(Wg)
    rows.append(dict(year=y, gcc_n=m['n'], gcc_l2=m['l2'], gcc_br=m['br'],
                     ncomp=ncomp, max_edge=mx, total=float(M.sum()),
                     gcc_members=','.join(gcc_list)))
    if y in (1950, 1955, 1960, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000,
             2005, 2010, 2015, 2020, 2023):
        print(f'  {y}: λ₂={m["l2"]:.6f} (n={m["n"]}) | BR={m["br"]:.6f} | '
              f'分量={ncomp} | 最大边={mx:.0f} | 总量={M.sum():.0f}', flush=True)

res = dict(years=years, n_countries=N, iso3=ISO3_64,
           missing_years=missing_years, trajectory=rows)
def _clean(o):
    if isinstance(o, dict): return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list): return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    return o
json.dump(_clean(res), open('probe31_results.json', 'w'), ensure_ascii=False, indent=1)
pd.DataFrame(rows).to_csv('dots_64_trajectory.csv', index=False)
print(f'[done] 缺失年份: {missing_years}')
