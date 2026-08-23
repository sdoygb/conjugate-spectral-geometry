#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针㉕（长周期回溯）：IMF DOTS 1948-2023 核心经济体贸易耦合 λ₂/BR 轨迹
数据源：World Bank Data360 镜像 IMF_DOT.csv（SDMX 展平）
指标：出口 FOB = IMF_DOT_TXG_FOB_USD；进口 CIF = IMF_DOT_TMG_CIF_USD（单位=美元）
节点：US/GB/FR/DE/IT/JP/IN/CN/CA/AU/KR/RU/TW（台湾=528 伙伴视角，无报告国）
方法：A[i,j] = max(i 报告出口到 j, j 报告从 i 进口) → 对称化 → 最大边归一化
      → 拉普拉斯 λ₂（代数连通度）+ 邻接谱二部残差 BR（阵营化）
"""
import pandas as pd
import numpy as np

SRC = '/Users/oygb/Downloads/IMF_DOT.csv'

REPORT = {'US':'USA','GB':'GBR','FR':'FRA','DE':'DEU','IT':'ITA','JP':'JPN','IN':'IND',
          'CN':'CHN','CA':'CAN','AU':'AUS','KR':'KOR','RU':'RUS'}
PARTNER = {'US':'111','GB':'112','FR':'132','DE':'134','IT':'136','JP':'158','IN':'534',
           'CN':'924','CA':'156','AU':'193','KR':'542','RU':'922','TW':'528'}
NODES = list(REPORT.keys()) + ['TW']
ISO2NODE = {v: k for k, v in REPORT.items()}
PART2NODE = {v: k for k, v in PARTNER.items()}

def load():
    cols = ['REF_AREA','INDICATOR','COMP_BREAKDOWN_1','TIME_PERIOD','OBS_VALUE']
    df = pd.read_csv(SRC, usecols=cols, low_memory=False)
    df = df[df['INDICATOR'].isin(['IMF_DOT_TXG_FOB_USD','IMF_DOT_TMG_CIF_USD'])].copy()
    df['TIME_PERIOD'] = df['TIME_PERIOD'].astype(int)
    df['PARTNER'] = df['COMP_BREAKDOWN_1'].str.replace('IMF_CNT_COUNTRY_', '')
    df['IS_EXPORT'] = (df['INDICATOR'] == 'IMF_DOT_TXG_FOB_USD')
    return df[['REF_AREA','PARTNER','TIME_PERIOD','OBS_VALUE','IS_EXPORT']]

def build_matrix(df, year):
    """A[i,j] = max(i 出口到 j, j 从 i 进口)。台湾行由各国从台进口补全。"""
    y = df[df['TIME_PERIOD'] == year]
    A = np.zeros((len(NODES), len(NODES)))
    idx = {k: i for i, k in enumerate(NODES)}
    # i 出口到 j（i 报告 TXG，伙伴 j）
    exp = y[(y['IS_EXPORT']) & (y['REF_AREA'].isin(REPORT.values())) & (y['PARTNER'].isin(PARTNER.values()))]
    for _, r in exp.iterrows():
        i = ISO2NODE.get(r['REF_AREA']); j = PART2NODE.get(r['PARTNER'])
        if i is not None and j is not None and i != j:
            A[idx[i], idx[j]] = max(A[idx[i], idx[j]], r['OBS_VALUE'])
    # j 从 i 进口（j 报告 TMG，伙伴 i）→ 等价于 i→j 的流，补缺失方向
    imp = y[(~y['IS_EXPORT']) & (y['REF_AREA'].isin(REPORT.values())) & (y['PARTNER'].isin(PARTNER.values()))]
    for _, r in imp.iterrows():
        j = ISO2NODE.get(r['REF_AREA']); i = PART2NODE.get(r['PARTNER'])
        if i is not None and j is not None and i != j:
            A[idx[i], idx[j]] = max(A[idx[i], idx[j]], r['OBS_VALUE'])
    Asym = np.maximum(A, A.T)
    return Asym, idx

def laplacian_lambda2(M):
    L = np.diag(M.sum(axis=1)) - M
    ev = np.sort(np.linalg.eigvalsh(L))
    return float(ev[1]) if len(ev) > 1 else float('nan')

def bipartite_residual(M):
    ev = np.sort(np.linalg.eigvalsh(M))
    n = len(ev)
    return float(sum(abs(ev[i] + ev[n-1-i]) for i in range(n//2)) / (n//2))

def main():
    print('载入 IMF DOTS 进出口数据...')
    df = load()
    print(f'  行数: {len(df)}, 年份 {df["TIME_PERIOD"].min()}-{df["TIME_PERIOD"].max()}')
    years = list(range(1948, 2024))
    rows = []
    for yr in years:
        A, idx = build_matrix(df, yr)
        deg = A.sum(axis=1)
        active = [k for k in NODES if deg[idx[k]] > 0]
        if len(active) < 3:
            rows.append({'year': yr, 'n_active': len(active), 'lambda2': np.nan, 'BR': np.nan,
                         'active': ','.join(active), 'total_usd': float(A.sum())})
            continue
        sub_idx = [idx[k] for k in active]
        M = A[np.ix_(sub_idx, sub_idx)]
        maxw = M.max()
        Mn = M / maxw if maxw > 0 else M
        l2 = laplacian_lambda2(Mn)
        br = bipartite_residual(Mn)
        rows.append({'year': yr, 'n_active': len(active), 'lambda2': l2, 'BR': br,
                     'active': ','.join(active), 'total_usd': float(A.sum()),
                     'max_edge_usd': float(maxw)})
        if yr in (1948, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2015, 2020, 2023):
            print(f"  {yr}: n={len(active)} λ₂={l2:.4f} BR={br:.4f} 总贸易={A.sum()/1e12:.2f}万亿$ 最大边={maxw/1e9:.0f}B$ 活跃={','.join(active)}")
    out = pd.DataFrame(rows)
    out.to_csv('gpu_spectra/society/imf_dots_longcycle.csv', index=False)
    print('\n保存: gpu_spectra/society/imf_dots_longcycle.csv')

    print('\n=== 关键边权重（归一化，最大边=1）===')
    print('年份  CN-US  CN-JP  CN-TW  CN-IN  US-DE  TW-US')
    for yr in [1960, 1970, 1980, 1990, 2000, 2010, 2015, 2020, 2023]:
        A, idx = build_matrix(df, yr)
        deg = A.sum(axis=1)
        active = [k for k in NODES if deg[idx[k]] > 0]
        sub_idx = [idx[k] for k in active]
        M = A[np.ix_(sub_idx, sub_idx)]
        maxw = M.max()
        Mn = M / maxw if maxw > 0 else M
        def w(a, b):
            if a not in active or b not in active: return float('nan')
            return Mn[active.index(a), active.index(b)]
        print(f"  {yr}: {w('CN','US'):.3f}  {w('CN','JP'):.3f}  {w('CN','TW'):.3f}  {w('CN','IN'):.3f}  {w('US','DE'):.3f}  {w('TW','US'):.3f}")

if __name__ == '__main__':
    main()
