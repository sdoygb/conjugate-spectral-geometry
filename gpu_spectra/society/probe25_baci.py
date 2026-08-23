#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉕: BACI 真实双边贸易流聚合 (1995-2024)
================================================
数据: BACI HS92 (1995-2023) + HS12 (2024), CEPII
  - 台湾 = code 490 "Other Asia, nes" (S19), UN Comtrade 标准编码
  - EU27 聚合为单一节点
输出:
  baci_6node_yearly.csv   : 6节点 (CN,TW,JP,IN,US,EU) 逐年双边贸易矩阵
  baci_66_y2023.csv       : WVS 66 国 2023 双边矩阵 (探针⑩' 贸易通道 Mantel)
  baci_cn_tw_us.csv       : CN-TW / US-TW / CN-US / CN-EU 时序 (探针㉓' 时序)
"""
import pandas as pd
import numpy as np
import os, sys, time

DL = '/Users/oygb/Downloads'
HS92 = f'{DL}/BACI_HS92_V202501'
HS12 = f'{DL}/BACI_HS12_V202601'
OUT = '.'

# ---------- 码表 ----------
codes = pd.read_csv(f'{DL}/BACI_HS22_V202601/country_codes_V202601.csv')
iso3_to_code = dict(zip(codes.country_iso3.str.upper(), codes.country_code))

EU27 = ['AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC','HUN',
        'IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK','SVN','ESP','SWE']
EU_CODES = set(iso3_to_code[c] for c in EU27 if c in iso3_to_code)

# 6 节点: CN=156, TW=490, JP=392, IN=699, US=842, EU=聚合
NODES = {'CN': 156, 'TW': 490, 'JP': 392, 'IN': 699, 'US': 842}
NODE_NAMES = ['CN', 'TW', 'JP', 'IN', 'US', 'EU']

def node_of(code):
    """把国家码映射到 6 节点之一 (EU 聚合)"""
    if code in EU_CODES:
        return 'EU'
    for name, c in NODES.items():
        if code == c:
            return name
    return None

def agg_file(path):
    """聚合单个 BACI 文件 → {(i,j): v}"""
    df = pd.read_csv(path, usecols=['i', 'j', 'v'], dtype={'i': 'int32', 'j': 'int32', 'v': 'float32'})
    # 过滤到目标集合 (6节点 + 66国)
    all_codes = set(NODES.values()) | EU_CODES | set(iso3_to_code.values())
    df = df[df['i'].isin(all_codes) & df['j'].isin(all_codes)]
    g = df.groupby(['i', 'j'])['v'].sum()
    return g

def main():
    t0 = time.time()
    # ---------- 年份文件列表 ----------
    files = []  # (year, path)
    for y in range(1995, 2024):
        files.append((y, f'{HS92}/BACI_HS92_Y{y}_V202501.csv'))
    files.append((2024, f'{HS12}/BACI_HS12_Y2024_V202601.csv'))

    # ---------- 6 节点逐年矩阵 ----------
    rows = []
    for y, path in files:
        g = agg_file(path)
        # 6节点双边 (双向分开)
        rec = {'year': y}
        pairs = {}
        for (i, j), v in g.items():
            ni, nj = node_of(i), node_of(j)
            if ni and nj and ni != nj:
                pairs[(ni, nj)] = pairs.get((ni, nj), 0.0) + v
        for ni in NODE_NAMES:
            for nj in NODE_NAMES:
                if ni == nj:
                    continue
                rec[f'{ni}->{nj}'] = pairs.get((ni, nj), 0.0) / 1e5  # 千美元→亿美元
        rows.append(rec)
        print(f'  {y}: {len(g)} pairs -> 6node matrix done ({time.time()-t0:.0f}s)', flush=True)
    ydf = pd.DataFrame(rows)
    ydf.to_csv(f'{OUT}/baci_6node_yearly.csv', index=False)
    print(f'[ok] baci_6node_yearly.csv: {ydf.shape}', flush=True)

    # ---------- 66 国 2023 截面 (探针⑩' 贸易 Mantel) ----------
    wvs = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', usecols=['B_COUNTRY_ALPHA'])
    ctrys66 = sorted(set(wvs['B_COUNTRY_ALPHA'].str.strip().str.upper()))
    print(f'[wvs] 66 国列表: {len(ctrys66)}')
    c66 = [iso3_to_code.get(c) for c in ctrys66]
    c66 = [c for c in c66 if c is not None]
    print(f'[baci] 可映射 {len(c66)}/{len(ctrys66)} 国')
    g23 = agg_file(f'{HS92}/BACI_HS92_Y2023_V202501.csv')
    rows66 = []
    for (i, j), v in g23.items():
        if i in c66 and j in c66:
            rows66.append((i, j, v))
    m66 = pd.DataFrame(rows66, columns=['i', 'j', 'v'])
    m66.to_csv(f'{OUT}/baci_66_y2023.csv', index=False)
    print(f'[ok] baci_66_y2023.csv: {len(m66)} pairs', flush=True)

    # ---------- CN-TW/US-TW/CN-US/CN-EU 时序 ----------
    cols = ['year', 'CN->TW', 'TW->CN', 'US->TW', 'TW->US', 'CN->US', 'US->CN',
            'CN->EU', 'EU->CN', 'US->EU', 'EU->US', 'CN->IN', 'IN->CN']
    ydf[cols].to_csv(f'{OUT}/baci_cn_tw_us.csv', index=False)
    print(f'[ok] baci_cn_tw_us.csv ({time.time()-t0:.0f}s)')

if __name__ == '__main__':
    main()
