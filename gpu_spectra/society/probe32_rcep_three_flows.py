#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉜：RCEP 三流协同检验（10.78 预言 7.01）v2
================================================================
预言 10.78.7.01 (三流协同): RCEP 生效 (2022-01) 后, 区域内 15 国应观测到
  货物流 (BACI 双边贸易)、信息流 (专利活动)、制度流 (WGI 制度质量趋同)
  三流协同变化 —— 判定"全通道耦合" vs "物质交换"假说。

设计:
  A) 货物流: BACI HS92 (1995-2023) + HS12 (2024), RCEP 15 国区域内双边贸易
     双向合计, 2018-2024; 生效前 T0=2018-2021 vs 生效后 T1=2022-2024
  B) 信息流: World Bank API IP.PAT.RESD + IP.PAT.NRES (专利申请), 2010-2024
     区域内总量; T0 vs T1 增长率 (滞后限制: 接受 2022-2023 可得窗口)
  C) 制度流: QoG WGI 六指标 (wbgi_vae/pve/gee/rqe/rle/cce) 长表
     RCEP 15 国 2010-2023; 趋同 = 区域内指标标准差下降

v2 修正: QoG 为长表 (year 列); 专利总量 = RESD+NRES
"""
import pandas as pd
import numpy as np
import json, os, time, urllib.request

DL = '/Users/oygb/Downloads'
HS92 = f'{DL}/BACI_HS92_V202501'
HS12 = f'{DL}/BACI_HS12_V202601'
OUT = '.'
RCEP_ISO3 = ['CHN','JPN','KOR','AUS','NZL','IDN','MYS','PHL','SGP','THA','BRN','VNM','LAO','MMR','KHM']
RCEP_NAME = {'CHN':'中国','JPN':'日本','KOR':'韩国','AUS':'澳大利亚','NZL':'新西兰',
             'IDN':'印尼','MYS':'马来西亚','PHL':'菲律宾','SGP':'新加坡','THA':'泰国',
             'BRN':'文莱','VNM':'越南','LAO':'老挝','MMR':'缅甸','KHM':'柬埔寨'}
WGI_DIMS = ['wbgi_vae','wbgi_pve','wbgi_gee','wbgi_rqe','wbgi_rle','wbgi_cce']
t0 = time.time()

def log(*a):
    print(f'[{time.time()-t0:6.1f}s]', *a, flush=True)

def load_codes(path, fix_deu=True):
    codes = pd.read_csv(path)
    d = dict(zip(codes.country_iso3.str.upper(), codes.country_code))
    if fix_deu: d['DEU'] = 276
    return d

iso3_92 = load_codes(f'{HS92}/country_codes_V202501.csv')
iso3_12 = load_codes(f'{HS12}/country_codes_V202601.csv')
iso3_92['TWN'] = 490; iso3_12['TWN'] = 490
rcep92 = {c: iso3_92[c] for c in RCEP_ISO3}
rcep12 = {c: iso3_12[c] for c in RCEP_ISO3}

# ---------- A) 货物流 ----------
def agg_rcep_year(y):
    if y <= 2023:
        p = f'{HS92}/BACI_HS92_Y{y}_V202501.csv'
        rcep = rcep92
    else:
        p = f'{HS12}/BACI_HS12_Y2024_V202601.csv'
        rcep = rcep12
    codes = set(rcep.values())
    df = pd.read_csv(p, usecols=['i','j','v'], dtype={'i':'int32','j':'int32','v':'float32'})
    df = df[df['i'].isin(codes) & df['j'].isin(codes)]
    g = df.groupby(['i','j'])['v'].sum()
    N = len(RCEP_ISO3)
    M = np.zeros((N,N))
    cvals = list(rcep.values())
    for (i,j), v in g.items():
        a = cvals.index(i); b = cvals.index(j)
        M[a,b] += v; M[b,a] += v
    return M

flows = {}
for y in range(2018, 2025):
    M = agg_rcep_year(y)
    flows[y] = M.sum()/2
    log(f'  {y}: 区域内贸易 = {flows[y]/1e6:.1f} 亿美元')

# ---------- B) 信息流 ----------
def wb_series(indicator):
    url = (f'https://api.worldbank.org/v2/country/'
           f'{";".join(RCEP_ISO3)}/indicator/{indicator}?date=2010:2024&format=json&per_page=300')
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read().decode())
        return {(d['country']['id'], d['date']): d['value'] for d in data[1]}
    except Exception as e:
        log('WB ERR', indicator, e)
        return {}

pat_resd = wb_series('IP.PAT.RESD')
pat_nres = wb_series('IP.PAT.NRES')
log('专利: RESD', len(pat_resd), 'NRES', len(pat_nres))

def pat_year(series, y):
    tot = 0; n = 0
    for c in RCEP_ISO3:
        v = series.get((c, str(y)))
        if v is not None:
            tot += v; n += 1
    return tot, n

pat_table = {}
for y in range(2010, 2025):
    r, nr = pat_year(pat_resd, y)
    n_, _ = pat_year(pat_nres, y)
    pat_table[y] = {'resd': r, 'nres': n_, 'tot': r + n_, 'n': nr}
    if nr > 0:
        log(f'  {y}: 居民 {r:,.0f} + 非居民 {n_:,.0f} = {r+n_:,.0f} (n={nr})')

# ---------- C) 制度流 ----------
qog = pd.read_csv(f'{OUT}/qog_std_ts_jan25.csv', usecols=['ccodealp','year'] + WGI_DIMS, low_memory=False)
qog_rcep = qog[qog['ccodealp'].isin(RCEP_ISO3) & qog['year'].between(2010, 2023)]
wgi_table = {}
for y in range(2010, 2024):
    sub = qog_rcep[qog_rcep['year'] == y]
    if len(sub) < 10: continue
    row = {}
    for dim in WGI_DIMS:
        s = sub[dim].dropna()
        if len(s) >= 8:
            row[dim] = {'mean': float(s.mean()), 'std': float(s.std()), 'n': int(len(s))}
    if row:
        wgi_table[str(y)] = row
        stds = [v['std'] for v in row.values()]
        log(f'  {y}: WGI 六指标区域内 std 均值 = {np.mean(stds):.4f} (n={len(sub)})')

res = {'rcep': RCEP_ISO3,
       'flows_usd1000': {str(y): flows[y] for y in flows},
       'patents': pat_table,
       'wgi': wgi_table}
with open('probe32_results.json','w') as f:
    json.dump(res, f, indent=1, default=str)
log('DONE -> probe32_results.json')
